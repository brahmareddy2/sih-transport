"""
Phase 5 — Incident Recovery Engine.

Orchestrates the full incident-to-recovery workflow:
  1. Identify affected shipments from the disrupted route
  2. Find available replacement vehicles sorted by proximity
  3. Find available replacement drivers
  4. Generate ranked recovery plan options
  5. Execute the approved recovery plan (DB + GPS simulator updates)

Design principles:
  - Pure deterministic Python — no new ML or external services
  - Reuses existing cost_calculator, distance_matrix, and vrp_solver
  - Reuses Phase 4 GPS simulator for vehicle status updates
  - All DB writes are transactional; rolls back on error
"""
import logging
import math
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.incident import Incident, RecoveryPlan
from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.models.route import Route, RouteStop
from app.models.shipment import Shipment
from app.models.notification import Notification
from app.models.user import User
from app.services.optimization.cost_calculator import calculate_route_cost, calculate_fuel_cost
from app.services.optimization.distance_matrix import (
    road_distance_km, haversine_km, INDIAN_CITIES, travel_time_minutes
)

logger = logging.getLogger(__name__)

# ── Incident type → severity mapping ─────────────────────────────────────────
INCIDENT_SEVERITY_MAP: dict[str, str] = {
    "breakdown": "critical",
    "tyre_puncture": "high",
    "accident": "critical",
    "traffic_jam": "medium",
    "road_closure": "high",
    "low_fuel": "medium",
    "driver_unavailable": "high",
    "weather_disruption": "medium",
    "delay": "low",
    "other": "low",
}

# Fuel station cities (simplified — use INDIAN_CITIES as proxy fuel-stop hubs)
FUEL_STATION_HUBS = list(INDIAN_CITIES.keys())

# ETA delay added per incident type (minutes) — used in recovery scoring
INCIDENT_BASE_DELAY_MIN: dict[str, int] = {
    "breakdown": 180,
    "tyre_puncture": 60,
    "accident": 120,
    "traffic_jam": 45,
    "road_closure": 90,
    "low_fuel": 30,
    "driver_unavailable": 90,
    "weather_disruption": 60,
    "delay": 30,
    "other": 30,
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km."""
    return haversine_km(lat1, lon1, lat2, lon2)


def _road_dist(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    return road_distance_km(lat1, lon1, lat2, lon2)


def _incident_lat_lon(incident: Incident) -> tuple[float, float]:
    """Return (lat, lon) for the incident location, defaulting to vehicle DB location."""
    if incident.lat and incident.lon:
        return incident.lat, incident.lon
    if incident.vehicle and incident.vehicle.current_lat:
        return incident.vehicle.current_lat, incident.vehicle.current_lon
    # Last resort: origin city of route
    if incident.route and incident.route.origin_city:
        city = INDIAN_CITIES.get(incident.route.origin_city, {})
        return city.get("lat", 19.0760), city.get("lon", 72.8777)
    return 19.0760, 72.8777  # Mumbai as ultimate fallback


def _route_remaining_distance(route: Route, db: Session) -> float:
    """Estimate remaining km for a route (simplified: use total_distance_km)."""
    if route.total_distance_km:
        return float(route.total_distance_km)
    # Fallback: calc from stops
    stops = db.query(RouteStop).filter(RouteStop.route_id == route.id).order_by(
        RouteStop.stop_sequence
    ).all()
    if len(stops) >= 2:
        total = 0.0
        for i in range(len(stops) - 1):
            if stops[i].lat and stops[i+1].lat:
                total += _road_dist(stops[i].lat, stops[i].lon, stops[i+1].lat, stops[i+1].lon)
        return total
    return 200.0  # sensible default


# ── Step 1: Find affected shipments ──────────────────────────────────────────

def find_affected_shipments(route_id: uuid.UUID, db: Session) -> list[Shipment]:
    """Return all shipments assigned to the disrupted route."""
    return db.query(Shipment).filter(
        Shipment.assigned_route_id == route_id,
        Shipment.status.in_(["assigned", "in_transit", "consolidated"]),
    ).all()


# ── Step 2: Find available replacement vehicles ───────────────────────────────

def find_available_vehicles(
    incident: Incident,
    required_capacity_kg: float,
    db: Session,
    limit: int = 5,
) -> list[dict]:
    """
    Find available vehicles near the incident location, sorted by proximity.
    Filters:
      - status == "available"
      - capacity >= required_capacity_kg
      - not the broken vehicle itself
      - not currently simulated as active (in GPS simulator)
    """
    inc_lat, inc_lon = _incident_lat_lon(incident)

    candidates = db.query(Vehicle).filter(
        Vehicle.status == "available",
        Vehicle.capacity_weight_kg >= required_capacity_kg,
    ).all()

    # Exclude the broken vehicle
    if incident.vehicle_id:
        candidates = [v for v in candidates if v.id != incident.vehicle_id]

    # If incident vehicle has special capabilities, filter replacements accordingly
    broken = incident.vehicle
    if broken:
        if broken.is_refrigerated:
            candidates = [v for v in candidates if v.is_refrigerated]
        if broken.can_carry_hazmat:
            candidates = [v for v in candidates if v.can_carry_hazmat]

    result = []
    for v in candidates:
        v_lat = v.current_lat or INDIAN_CITIES.get(v.current_city or "Mumbai", {}).get("lat", 19.0760)
        v_lon = v.current_lon or INDIAN_CITIES.get(v.current_city or "Mumbai", {}).get("lon", 72.8777)
        dist_km = _haversine(inc_lat, inc_lon, v_lat, v_lon)
        # Road-adjusted distance
        road_dist = dist_km * 1.28
        travel_min = int((road_dist / 55.0) * 60)  # 55 km/h average

        driver_name = "No Driver"
        driver_id = None
        driver_status = None
        if v.driver:
            driver_name = v.driver.full_name if hasattr(v.driver, "full_name") else v.driver.employee_id
            driver_id = str(v.driver.id)
            driver_status = v.driver.status

        fuel_pct = 0.0
        if v.fuel_tank_capacity_l and v.current_fuel_level_l:
            fuel_pct = round((float(v.current_fuel_level_l) / float(v.fuel_tank_capacity_l)) * 100, 1)

        result.append({
            "vehicle_id": str(v.id),
            "registration_number": v.registration_number,
            "vehicle_type": v.vehicle_type,
            "make": v.make or "",
            "model_name": v.model_name or "",
            "capacity_weight_kg": float(v.capacity_weight_kg),
            "fuel_type": v.fuel_type,
            "fuel_efficiency_kmpl": float(v.fuel_efficiency_kmpl),
            "fuel_level_pct": fuel_pct,
            "current_city": v.current_city or "Unknown",
            "current_lat": v_lat,
            "current_lon": v_lon,
            "distance_from_incident_km": round(road_dist, 1),
            "estimated_arrival_min": travel_min,
            "driver_id": driver_id,
            "driver_name": driver_name,
            "driver_status": driver_status,
            "is_refrigerated": v.is_refrigerated,
            "can_carry_hazmat": v.can_carry_hazmat,
            "status": v.status,
        })

    # Sort by distance from incident
    result.sort(key=lambda x: x["distance_from_incident_km"])
    return result[:limit]


# ── Step 3: Find available replacement drivers ────────────────────────────────

def find_available_drivers(db: Session, exclude_driver_id: Optional[uuid.UUID] = None) -> list[dict]:
    """Find drivers that are available and not over working hours."""
    drivers = db.query(Driver).filter(
        Driver.status == "available",
        Driver.hours_driven_today < 10.0,
    ).all()

    if exclude_driver_id:
        drivers = [d for d in drivers if d.id != exclude_driver_id]

    result = []
    for d in drivers:
        result.append({
            "driver_id": str(d.id),
            "employee_id": d.employee_id,
            "full_name": d.full_name if hasattr(d, "full_name") else d.employee_id,
            "license_type": d.license_type or "HMV",
            "hours_driven_today": float(d.hours_driven_today or 0),
            "status": d.status,
            "home_city": d.home_city or "Unknown",
        })
    return result


# ── Step 4: Scoring algorithm ─────────────────────────────────────────────────

def score_recovery_plan(
    additional_cost_inr: float,
    delay_minutes: int,
    additional_km: float,
    vehicle_utilization_pct: float = 75.0,
) -> float:
    """
    Transparent deterministic recovery scoring (0–100).
    Higher score = better recovery option.

    Penalties:
      cost:         every ₹1000 extra → -8 pts  (max -40)
      delay:        every 30 min      → -8 pts  (max -30)
      distance:     every 50 km extra → -5 pts  (max -20)
    Bonus:
      utilization:  up to +10 pts
    """
    cost_penalty = min(40.0, (additional_cost_inr / 1000.0) * 8.0)
    delay_penalty = min(30.0, (delay_minutes / 30.0) * 8.0)
    dist_penalty = min(20.0, (additional_km / 50.0) * 5.0)
    util_bonus = min(10.0, vehicle_utilization_pct / 10.0)

    score = 100.0 - cost_penalty - delay_penalty - dist_penalty + util_bonus
    return round(max(0.0, min(100.0, score)), 1)


# ── Step 5: Generate recovery options ────────────────────────────────────────

def generate_recovery_options(incident_id: uuid.UUID, db: Session) -> list[dict]:
    """
    Core recovery planning function.
    Returns a list of ranked recovery option dicts (not yet persisted as RecoveryPlan rows).
    Caller should call persist_recovery_plans() to save them.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise ValueError(f"Incident {incident_id} not found")

    inc_type = incident.incident_type.lower()
    inc_lat, inc_lon = _incident_lat_lon(incident)

    # Get affected route
    route = None
    if incident.route_id:
        route = db.query(Route).filter(Route.id == incident.route_id).first()

    # Get affected shipments
    affected_shipments = []
    if route:
        affected_shipments = find_affected_shipments(route.id, db)

    total_weight_kg = sum(float(s.weight_kg) for s in affected_shipments) if affected_shipments else 0.0
    original_distance_km = _route_remaining_distance(route, db) if route else 200.0
    base_delay_min = INCIDENT_BASE_DELAY_MIN.get(inc_type, 60)

    options = []

    # ── Option types based on incident type ─────────────────────────────────

    # ROAD_CLOSURE / SEVERE_TRAFFIC → try reroute first
    if inc_type in ("road_closure", "traffic_jam"):
        options.append(_build_reroute_option(
            incident, route, original_distance_km, base_delay_min, total_weight_kg
        ))

    # LOW_FUEL → try fuel stop first
    if inc_type == "low_fuel":
        fuel_option = _build_fuel_stop_option(incident, inc_lat, inc_lon, route, base_delay_min)
        if fuel_option:
            options.append(fuel_option)

    # DRIVER_UNAVAILABLE → replace driver only
    if inc_type == "driver_unavailable":
        driver_opt = _build_driver_replacement_option(incident, db, route, base_delay_min)
        if driver_opt:
            options.append(driver_opt)

    # BREAKDOWN / PUNCTURE / ACCIDENT and others → find replacement vehicle
    if inc_type not in ("road_closure", "traffic_jam") or not options:
        nearby_vehicles = find_available_vehicles(
            incident, max(total_weight_kg, 500.0), db, limit=3
        )

        for i, veh in enumerate(nearby_vehicles):
            plan_type = "replace_vehicle" if i == 0 else "replace_vehicle_and_driver"
            alt_driver_id = veh.get("driver_id")
            alt_driver_name = veh.get("driver_name", "Unknown")

            # Cost: retrieval distance + remaining route
            retrieval_km = veh["distance_from_incident_km"]
            total_new_km = retrieval_km + original_distance_km
            additional_km = retrieval_km  # extra km vs original
            additional_delay_min = base_delay_min + veh["estimated_arrival_min"]

            # Calculate costs using existing cost_calculator
            cost_result = calculate_route_cost(
                total_distance_km=total_new_km,
                empty_distance_km=retrieval_km,
                fuel_efficiency_kmpl=veh["fuel_efficiency_kmpl"],
                fuel_type=veh["fuel_type"],
                vehicle_type=veh["vehicle_type"],
                road_type="mixed",
                travel_hours=(total_new_km / 55.0),
                num_days=1,
                payload_kg=total_weight_kg,
            )

            original_cost = calculate_route_cost(
                total_distance_km=original_distance_km,
                empty_distance_km=0.0,
                fuel_efficiency_kmpl=float(
                    incident.vehicle.fuel_efficiency_kmpl if incident.vehicle else 5.0
                ),
                fuel_type=incident.vehicle.fuel_type if incident.vehicle else "diesel",
                vehicle_type=incident.vehicle.vehicle_type if incident.vehicle else "medium_truck",
                road_type="mixed",
                travel_hours=(original_distance_km / 55.0),
                num_days=1,
                payload_kg=total_weight_kg,
            )

            additional_cost = max(0.0, cost_result.total_cost_inr - original_cost.total_cost_inr)
            util_pct = min(100.0, (total_weight_kg / veh["capacity_weight_kg"] * 100)) if veh["capacity_weight_kg"] > 0 else 0.0

            rec_score = score_recovery_plan(
                additional_cost_inr=additional_cost,
                delay_minutes=additional_delay_min,
                additional_km=additional_km,
                vehicle_utilization_pct=util_pct,
            )

            description = (
                f"Replace breakdown vehicle with {veh['registration_number']} "
                f"({veh['vehicle_type']}, {veh['make']}). "
                f"Retrieval from {veh['current_city']}: {retrieval_km:.0f} km. "
                f"Driver: {alt_driver_name}. "
                f"Estimated additional delay: {additional_delay_min} min."
            )

            options.append({
                "plan_type": plan_type,
                "plan_description": description,
                "action_type": "reassign_vehicle",
                "recommended_action": description,
                "alternative_vehicle_id": veh["vehicle_id"],
                "alternative_vehicle_info": veh,
                "alternative_driver_id": alt_driver_id,
                "alternative_driver_name": alt_driver_name,
                "estimated_delay_min": additional_delay_min,
                "additional_distance_km": round(additional_km, 1),
                "cost_impact_inr": round(additional_cost, 2),
                "original_cost_inr": round(original_cost.total_cost_inr, 2),
                "new_cost_inr": round(cost_result.total_cost_inr, 2),
                "recovery_score": rec_score,
                "original_distance_km": round(original_distance_km, 1),
                "new_total_distance_km": round(total_new_km, 1),
                "fuel_litres": round(cost_result.fuel_litres, 2),
                "co2_kg": round(cost_result.co2_kg, 2),
                "affected_shipment_count": len(affected_shipments),
                "total_payload_kg": round(total_weight_kg, 1),
            })

    # If no options generated at all, create a "delay only" fallback
    if not options:
        options.append({
            "plan_type": "delay_only",
            "plan_description": "No suitable replacement vehicle found. Shipments will be delayed until incident resolved.",
            "action_type": "delay_shipment",
            "recommended_action": "Delay shipments — no replacement available.",
            "alternative_vehicle_id": None,
            "alternative_driver_id": None,
            "estimated_delay_min": base_delay_min,
            "additional_distance_km": 0.0,
            "cost_impact_inr": 0.0,
            "recovery_score": 0.0,
        })

    # Sort by recovery_score descending
    options.sort(key=lambda x: x["recovery_score"], reverse=True)
    return options


def _build_reroute_option(incident, route, original_km, base_delay_min, total_weight_kg):
    """Build a reroute recovery option for road closure / severe traffic."""
    # Estimate reroute: 15% extra distance, 20% extra time
    detour_km = original_km * 0.15
    new_km = original_km + detour_km
    delay_min = base_delay_min

    if route and route.vehicle:
        v = route.vehicle
        cost_result = calculate_route_cost(
            total_distance_km=new_km,
            empty_distance_km=0.0,
            fuel_efficiency_kmpl=float(v.fuel_efficiency_kmpl),
            fuel_type=v.fuel_type,
            vehicle_type=v.vehicle_type,
            road_type="sh",  # forced to state highway reroute
            travel_hours=(new_km / 45.0),
            num_days=1,
            payload_kg=total_weight_kg,
        )
        original_cost = calculate_route_cost(
            total_distance_km=original_km,
            empty_distance_km=0.0,
            fuel_efficiency_kmpl=float(v.fuel_efficiency_kmpl),
            fuel_type=v.fuel_type,
            vehicle_type=v.vehicle_type,
            road_type="mixed",
            travel_hours=(original_km / 55.0),
            num_days=1,
            payload_kg=total_weight_kg,
        )
        add_cost = max(0.0, cost_result.total_cost_inr - original_cost.total_cost_inr)
        reg = v.registration_number
    else:
        add_cost = detour_km * 9.0  # ₹9/km rough estimate
        reg = "same vehicle"

    score = score_recovery_plan(add_cost, delay_min, detour_km, 85.0)
    return {
        "plan_type": "reroute",
        "plan_description": (
            f"Reroute {reg} via alternate state highways, avoiding the incident location. "
            f"Estimated detour: {detour_km:.0f} km extra. Additional delay: {delay_min} min."
        ),
        "action_type": "reroute",
        "recommended_action": f"Reroute via alternate road (+{detour_km:.0f} km, +{delay_min} min).",
        "alternative_vehicle_id": None,
        "alternative_driver_id": None,
        "estimated_delay_min": delay_min,
        "additional_distance_km": round(detour_km, 1),
        "cost_impact_inr": round(add_cost, 2),
        "recovery_score": score,
    }


def _build_fuel_stop_option(incident, inc_lat, inc_lon, route, base_delay_min):
    """Build a fuel stop option for low fuel incidents."""
    # Find nearest city as fuel hub proxy
    nearest_city = None
    min_dist = float("inf")
    for city_name, city_data in INDIAN_CITIES.items():
        d = _haversine(inc_lat, inc_lon, city_data["lat"], city_data["lon"])
        if d < min_dist:
            min_dist = d
            nearest_city = city_name

    if not nearest_city:
        return None

    detour_km = min_dist * 2 * 1.28  # round trip road distance
    delay_min = int((detour_km / 55.0) * 60) + 20  # travel + fill time
    add_cost = detour_km * 6.0  # ₹6/km rough fuel + toll

    score = score_recovery_plan(add_cost, delay_min, detour_km, 80.0)
    return {
        "plan_type": "fuel_stop",
        "plan_description": (
            f"Divert to nearest fuel station at {nearest_city} IOCL/BPCL fuel depot. "
            f"Distance: {detour_km:.0f} km detour. Estimated delay: {delay_min} min."
        ),
        "action_type": "find_fuel",
        "recommended_action": f"Refuel at {nearest_city} ({detour_km:.0f} km detour, {delay_min} min).",
        "alternative_vehicle_id": None,
        "alternative_driver_id": None,
        "estimated_delay_min": delay_min,
        "additional_distance_km": round(detour_km, 1),
        "cost_impact_inr": round(add_cost, 2),
        "recovery_score": score,
        "fuel_station_city": nearest_city,
        "fuel_station_distance_km": round(min_dist, 1),
    }


def _build_driver_replacement_option(incident, db, route, base_delay_min):
    """Build a driver-only replacement option."""
    available_drivers = find_available_drivers(
        db, exclude_driver_id=incident.driver_id
    )
    if not available_drivers:
        return None

    best_driver = available_drivers[0]
    add_cost = 800.0  # Transport cost to bring replacement driver
    score = score_recovery_plan(add_cost, base_delay_min, 0.0, 80.0)

    return {
        "plan_type": "replace_vehicle_and_driver",
        "plan_description": (
            f"Assign replacement driver {best_driver['full_name']} ({best_driver['employee_id']}) "
            f"to current vehicle. Estimated delay: {base_delay_min} min."
        ),
        "action_type": "reassign_vehicle",
        "recommended_action": f"Replace driver with {best_driver['full_name']}.",
        "alternative_vehicle_id": str(incident.vehicle_id) if incident.vehicle_id else None,
        "alternative_driver_id": best_driver["driver_id"],
        "estimated_delay_min": base_delay_min,
        "additional_distance_km": 0.0,
        "cost_impact_inr": add_cost,
        "recovery_score": score,
        "replacement_driver": best_driver,
    }


# ── Step 6: Persist recovery plans to DB ─────────────────────────────────────

def persist_recovery_plans(incident_id: uuid.UUID, options: list[dict], db: Session) -> list[RecoveryPlan]:
    """Save generated recovery options as RecoveryPlan rows."""
    # Delete existing unnapproved plans for this incident first
    db.query(RecoveryPlan).filter(
        RecoveryPlan.incident_id == incident_id,
        RecoveryPlan.is_approved == False,
    ).delete()

    plans = []
    for opt in options:
        alt_veh_id = None
        if opt.get("alternative_vehicle_id"):
            try:
                alt_veh_id = uuid.UUID(opt["alternative_vehicle_id"])
            except (ValueError, TypeError):
                pass

        alt_drv_id = None
        if opt.get("alternative_driver_id"):
            try:
                alt_drv_id = uuid.UUID(opt["alternative_driver_id"])
            except (ValueError, TypeError):
                pass

        plan = RecoveryPlan(
            incident_id=incident_id,
            plan_type=opt.get("plan_type", "delay_only"),
            plan_description=opt.get("plan_description", ""),
            action_type=opt.get("action_type", "delay_shipment"),
            recommended_action=opt.get("recommended_action", ""),
            alternative_vehicle_id=alt_veh_id,
            alternative_driver_id=alt_drv_id,
            estimated_delay_min=opt.get("estimated_delay_min", 0),
            cost_impact_inr=opt.get("cost_impact_inr", 0.0),
            additional_distance_km=opt.get("additional_distance_km", 0.0),
            recovery_score=opt.get("recovery_score", 0.0),
            is_approved=False,
        )
        db.add(plan)
        plans.append(plan)

    try:
        db.commit()
        for p in plans:
            db.refresh(p)
    except Exception as e:
        db.rollback()
        logger.error("Failed to persist recovery plans: %s", e)
        raise

    return plans


# ── Step 7: Execute approved recovery plan ────────────────────────────────────

def execute_recovery_plan(
    incident: Incident,
    plan: RecoveryPlan,
    approved_by_user_id: uuid.UUID,
    db: Session,
) -> dict:
    """
    Execute an approved recovery plan. Performs:
      1. Mark plan as approved
      2. Reassign route vehicle/driver
      3. Update vehicle statuses
      4. Mark affected shipments as 'delayed'
      5. Recalculate route cost
      6. Update incident status to in_recovery
      7. Create notifications
      8. Update GPS simulation state (stop old, start new if needed)
    """
    logger.info("Executing recovery plan %s for incident %s", plan.id, incident.id)

    try:
        # 1. Approve plan
        plan.is_approved = True
        # Verify approver exists in DB before setting FK (safe for test environments)
        approver = db.query(User).filter(User.id == approved_by_user_id).first()
        plan.approved_by = approved_by_user_id if approver else None
        plan.approved_at = datetime.now(timezone.utc)

        # 2. Get the affected route
        route = None
        if incident.route_id:
            route = db.query(Route).filter(Route.id == incident.route_id).first()

        new_vehicle = None
        new_driver = None

        # 3. Reassign vehicle if plan specifies
        if plan.alternative_vehicle_id and plan.plan_type != "delay_only":
            new_vehicle = db.query(Vehicle).filter(
                Vehicle.id == plan.alternative_vehicle_id
            ).first()
            if new_vehicle and route:
                route.vehicle_id = new_vehicle.id
                new_vehicle.status = "in_transit"
                logger.info("Reassigned route to vehicle %s", new_vehicle.registration_number)

        # 4. Reassign driver if plan specifies
        if plan.alternative_driver_id:
            new_driver = db.query(Driver).filter(
                Driver.id == plan.alternative_driver_id
            ).first()
            if new_driver and route:
                route.driver_id = new_driver.id
                new_driver.status = "on_trip"

        # 5. Mark broken vehicle as breakdown (if it's a vehicle replacement)
        if incident.vehicle_id and plan.plan_type in ("replace_vehicle", "replace_vehicle_and_driver"):
            broken_vehicle = db.query(Vehicle).filter(
                Vehicle.id == incident.vehicle_id
            ).first()
            if broken_vehicle:
                broken_vehicle.status = "breakdown"

        # 6. Update affected shipments
        affected_shipments = []
        if route:
            affected_shipments = find_affected_shipments(route.id, db)
            for shipment in affected_shipments:
                shipment.status = "delayed"

        # 7. Recalculate route cost with new vehicle if vehicle changed
        if new_vehicle and route and route.total_distance_km:
            total_km = float(route.total_distance_km)
            extra_km = float(plan.additional_distance_km or 0)
            new_total_km = total_km + extra_km
            total_weight = sum(float(s.weight_kg) for s in affected_shipments)

            cost_result = calculate_route_cost(
                total_distance_km=new_total_km,
                empty_distance_km=extra_km,
                fuel_efficiency_kmpl=float(new_vehicle.fuel_efficiency_kmpl),
                fuel_type=new_vehicle.fuel_type,
                vehicle_type=new_vehicle.vehicle_type,
                road_type=route.road_type or "mixed",
                travel_hours=(new_total_km / 55.0),
                num_days=1,
                payload_kg=total_weight,
            )
            route.total_distance_km = new_total_km
            route.total_estimated_cost_inr = cost_result.total_cost_inr
            route.estimated_fuel_l = cost_result.fuel_litres
            route.estimated_fuel_cost_inr = cost_result.fuel_cost_inr

            # Update ETA
            if route.planned_end_time:
                delay_delta = timedelta(minutes=int(plan.estimated_delay_min or 0))
                route.planned_end_time = route.planned_end_time + delay_delta
            else:
                route.planned_end_time = datetime.now(timezone.utc) + timedelta(
                    minutes=int((new_total_km / 55.0) * 60) + int(plan.estimated_delay_min or 0)
                )

        # 8. Update incident status
        incident.status = "in_recovery"

        db.commit()

        # 9. Create notifications
        _create_recovery_notifications(incident, plan, new_vehicle, new_driver, affected_shipments, db)

        # 10. GPS simulator update
        _update_gps_simulation(incident, plan, new_vehicle, db)

        new_eta = route.planned_end_time.isoformat() if route and route.planned_end_time else None

        logger.info("Recovery plan executed successfully for incident %s", incident.id)
        return {
            "success": True,
            "incident_id": str(incident.id),
            "plan_id": str(plan.id),
            "new_vehicle_id": str(new_vehicle.id) if new_vehicle else None,
            "new_vehicle_registration": new_vehicle.registration_number if new_vehicle else None,
            "new_driver_id": str(new_driver.id) if new_driver else None,
            "shipments_updated": len(affected_shipments),
            "estimated_delay_min": plan.estimated_delay_min or 0,
            "additional_cost_inr": float(plan.cost_impact_inr or 0),
            "new_eta": new_eta,
            "incident_status": "in_recovery",
            "message": "Recovery plan approved and executed successfully.",
        }

    except Exception as e:
        db.rollback()
        logger.error("Failed to execute recovery plan: %s", e, exc_info=True)
        raise


def _create_recovery_notifications(
    incident: Incident,
    plan: RecoveryPlan,
    new_vehicle,
    new_driver,
    affected_shipments: list,
    db: Session,
):
    """Create operator, driver, and customer notifications."""
    try:
        delay_min = plan.estimated_delay_min or 0
        inc_type_label = incident.incident_type.replace("_", " ").title()

        # Operator notification
        operators = db.query(User).filter(User.role.in_(["admin", "fleet_operator"])).all()
        for op in operators:
            db.add(Notification(
                user_id=op.id,
                notification_type="incident_recovery",
                title=f"✅ Recovery Approved: {inc_type_label}",
                message=(
                    f"Recovery plan approved for {inc_type_label} incident. "
                    f"New vehicle: {new_vehicle.registration_number if new_vehicle else 'Reroute'}. "
                    f"Estimated additional delay: {delay_min} min. "
                    f"{len(affected_shipments)} shipments updated to 'delayed'."
                ),
                data_json={
                    "incident_id": str(incident.id),
                    "plan_id": str(plan.id),
                    "incident_type": incident.incident_type,
                },
                is_read=False,
            ))

        # Driver notification (new driver if assigned)
        if new_driver and new_driver.user_id:
            db.add(Notification(
                user_id=new_driver.user_id,
                notification_type="trip_assignment",
                title="🚛 New Emergency Trip Assignment",
                message=(
                    f"You have been assigned to an emergency recovery trip. "
                    f"A {inc_type_label} incident has occurred. "
                    f"Please proceed to pickup location immediately."
                ),
                data_json={"incident_id": str(incident.id)},
                is_read=False,
            ))

        # Customer notifications
        for shipment in affected_shipments:
            if shipment.customer_id:
                new_eta_str = "updated soon"
                db.add(Notification(
                    user_id=shipment.customer_id,
                    notification_type="delivery_delay",
                    title=f"⚠️ Delivery Delay — {shipment.shipment_number}",
                    message=(
                        f"Your shipment {shipment.shipment_number} may experience a delay of "
                        f"approximately {delay_min} minutes due to a logistics incident. "
                        f"Updated ETA: {new_eta_str}. We apologize for the inconvenience."
                    ),
                    data_json={
                        "shipment_id": str(shipment.id),
                        "incident_id": str(incident.id),
                        "delay_minutes": delay_min,
                    },
                    is_read=False,
                ))

        db.commit()
        logger.info("Created recovery notifications for incident %s", incident.id)
    except Exception as e:
        db.rollback()
        logger.error("Failed to create recovery notifications: %s", e)


def _update_gps_simulation(incident: Incident, plan: RecoveryPlan, new_vehicle, db: Session):
    """
    Stop GPS simulation for the broken vehicle.
    If a replacement vehicle is available, start simulation on new vehicle.
    Reuses Phase 4 GPS simulator without modifying it.
    """
    try:
        from app.services.tracking.gps_simulator import (
            SIMULATIONS, stop_simulation, start_simulation
        )

        # Stop simulation for broken vehicle
        if incident.vehicle_id:
            v_str = str(incident.vehicle_id)
            if v_str in SIMULATIONS:
                SIMULATIONS.pop(v_str, None)
                logger.info("Stopped GPS simulation for broken vehicle %s", v_str)

        # Start simulation for replacement vehicle if there's an active route
        if new_vehicle and incident.route_id:
            try:
                start_simulation(new_vehicle.id, incident.route_id, db)
                logger.info("Started GPS simulation for replacement vehicle %s", new_vehicle.registration_number)
            except Exception as e:
                logger.warning("Could not start GPS simulation for replacement vehicle: %s", e)

    except Exception as e:
        logger.error("GPS simulation update failed (non-critical): %s", e)


# ── Simulate incident (for SIH demo) ─────────────────────────────────────────

def simulate_incident(
    vehicle_id: uuid.UUID,
    incident_type: str,
    route_id: Optional[uuid.UUID],
    db: Session,
    description: Optional[str] = None,
) -> Incident:
    """
    Create a new incident record for SIH demonstration.
    Also immediately affects vehicle and route statuses in DB.
    """
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise ValueError(f"Vehicle {vehicle_id} not found")

    # Get active route
    route = None
    if route_id:
        route = db.query(Route).filter(Route.id == route_id).first()
    elif not route_id:
        route = db.query(Route).filter(
            Route.vehicle_id == vehicle_id,
            Route.status.in_(["in_progress", "planned"]),
        ).first()

    # Determine incident location from GPS sim or vehicle DB
    inc_lat = vehicle.current_lat
    inc_lon = vehicle.current_lon
    inc_city = vehicle.current_city

    # Try GPS simulator for live position
    try:
        from app.services.tracking.gps_simulator import SIMULATIONS
        v_str = str(vehicle_id)
        if v_str in SIMULATIONS:
            state = SIMULATIONS[v_str]
            inc_lat = state["latitude"]
            inc_lon = state["longitude"]
    except Exception:
        pass

    severity = INCIDENT_SEVERITY_MAP.get(incident_type.lower(), "medium")

    # Affected shipments
    affected_ids = []
    if route:
        shipments = find_affected_shipments(route.id, db)
        affected_ids = [str(s.id) for s in shipments]

    incident = Incident(
        vehicle_id=vehicle_id,
        driver_id=vehicle.driver.id if vehicle.driver else None,
        route_id=route.id if route else None,
        incident_type=incident_type.lower(),
        severity=severity,
        description=description or f"Simulated {incident_type} incident on vehicle {vehicle.registration_number}",
        lat=inc_lat,
        lon=inc_lon,
        city=inc_city,
        source="system",
        reported_at=datetime.now(timezone.utc),
        detected_at=datetime.now(timezone.utc),
        status="open",
        affected_shipment_ids=affected_ids,
    )
    db.add(incident)

    # Update vehicle status
    if incident_type.lower() in ("breakdown", "accident"):
        vehicle.status = "breakdown"
    elif incident_type.lower() == "tyre_puncture":
        vehicle.status = "breakdown"

    if route and incident_type.lower() in ("breakdown", "accident", "tyre_puncture"):
        route.status = "delayed"

    try:
        db.commit()
        db.refresh(incident)
    except Exception as e:
        db.rollback()
        raise

    # Pause GPS simulation
    try:
        from app.services.tracking.gps_simulator import SIMULATIONS, pause_simulation
        v_str = str(vehicle_id)
        if v_str in SIMULATIONS:
            SIMULATIONS[v_str]["vehicle_status"] = "BREAKDOWN"
            SIMULATIONS[v_str]["engine_status"] = "off"
            SIMULATIONS[v_str]["speed"] = 0.0
            SIMULATIONS[v_str]["is_paused"] = True
    except Exception as e:
        logger.warning("Could not update GPS simulation state: %s", e)

    # Send operator alert
    try:
        operators = db.query(User).filter(User.role.in_(["admin", "fleet_operator"])).all()
        inc_label = incident_type.replace("_", " ").title()
        for op in operators:
            db.add(Notification(
                user_id=op.id,
                notification_type="incident_alert",
                title=f"🚨 Incident Detected: {inc_label} — {vehicle.registration_number}",
                message=(
                    f"A {inc_label} incident has been detected on vehicle {vehicle.registration_number}. "
                    f"Severity: {severity.upper()}. "
                    f"{len(affected_ids)} shipment(s) affected. "
                    f"Please generate and approve a recovery plan."
                ),
                data_json={"incident_id": str(incident.id), "vehicle_id": str(vehicle_id)},
                is_read=False,
            ))
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Failed to create incident notification: %s", e)

    logger.info("Simulated incident %s (%s) for vehicle %s", incident.id, incident_type, vehicle.registration_number)
    return incident
