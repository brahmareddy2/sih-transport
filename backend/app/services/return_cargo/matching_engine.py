"""
Phase 6 — Return Cargo Matching & Empty-Kilometer Reduction Engine.

Core algorithmic module that:
1. Identifies vehicles at destination cities ready for return trips
2. Evaluates compatibility with pending shipments
3. Computes exact distance deltas, deadhead reductions, and fuel/cost impacts
4. Generates deterministic 0–100 match scores and rankings
5. Creates and optimizes return routes on operator approval
"""
import logging
import math
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.driver import Driver
from app.models.notification import Notification
from app.models.return_cargo import ReturnCargoMatch
from app.models.route import Route, RouteStop
from app.models.shipment import Shipment
from app.models.user import User
from app.models.vehicle import Vehicle
from app.services.optimization.cost_calculator import (
    calculate_fuel_cost,
    calculate_route_cost,
)
from app.services.optimization.distance_matrix import (
    INDIAN_CITIES,
    city_distance_km,
    haversine_km,
    road_distance_km,
)

logger = logging.getLogger(__name__)


# ── Distance & City Helpers ───────────────────────────────────────────────────

def get_safe_city_distance(origin: str, dest: str) -> float:
    """Compute road distance between two cities safely, with fallback."""
    if not origin or not dest or origin == dest:
        return 0.0
    if origin in INDIAN_CITIES and dest in INDIAN_CITIES:
        return city_distance_km(origin, dest)
    # Generic default for test/mock cities
    return 150.0


# ── 1. Constraint & Compatibility Checker ─────────────────────────────────────

def evaluate_compatibility(
    vehicle: Vehicle,
    shipment: Shipment,
    current_city: str,
    home_city: str,
    max_detour_km: float = 300.0,
) -> Tuple[bool, Dict[str, Any]]:
    """
    Check if a shipment is physically, operationally, and geographically
    compatible for return transport by the given vehicle.
    """
    reasons = []
    checks = {
        "weight_compatible": True,
        "volume_compatible": True,
        "refrigeration_compatible": True,
        "hazmat_compatible": True,
        "route_compatible": True,
        "time_compatible": True,
    }

    # 1. Weight capacity check
    veh_capacity_kg = float(vehicle.capacity_weight_kg)
    shipment_weight = float(shipment.weight_kg)
    if shipment_weight > veh_capacity_kg:
        checks["weight_compatible"] = False
        reasons.append(
            f"Weight {shipment_weight}kg exceeds vehicle capacity {veh_capacity_kg}kg"
        )

    # 2. Volume capacity check
    if shipment.volume_m3 and vehicle.capacity_volume_m3:
        if float(shipment.volume_m3) > float(vehicle.capacity_volume_m3):
            checks["volume_compatible"] = False
            reasons.append(
                f"Volume {shipment.volume_m3}m3 exceeds vehicle capacity {vehicle.capacity_volume_m3}m3"
            )

    # 3. Special capability checks
    if shipment.requires_refrigeration and not vehicle.is_refrigerated:
        checks["refrigeration_compatible"] = False
        reasons.append("Shipment requires refrigeration but vehicle is not refrigerated")

    if shipment.is_hazardous and not vehicle.can_carry_hazmat:
        checks["hazmat_compatible"] = False
        reasons.append("Shipment is hazardous but vehicle cannot carry hazmat")

    # 4. Route & detour compatibility
    empty_before = get_safe_city_distance(current_city, home_city)
    pickup_dist = get_safe_city_distance(current_city, shipment.origin_city)
    loaded_dist = get_safe_city_distance(shipment.origin_city, shipment.destination_city)
    dropoff_to_depot = get_safe_city_distance(shipment.destination_city, home_city)
    total_trip = pickup_dist + loaded_dist + dropoff_to_depot
    detour_km = max(0.0, total_trip - empty_before)

    # Reject if pickup is too far (>250km from current location) or detour > max_detour_km
    if pickup_dist > 250.0:
        checks["route_compatible"] = False
        reasons.append(f"Pickup location ({shipment.origin_city}) is too far from current city ({pickup_dist} km)")
    elif detour_km > max_detour_km and empty_before > 0:
        checks["route_compatible"] = False
        reasons.append(f"Detour of {detour_km:.1f} km exceeds max threshold of {max_detour_km} km")

    is_compatible = all(checks.values())
    return is_compatible, {
        "checks": checks,
        "reasons": reasons,
        "pickup_distance_km": round(pickup_dist, 1),
        "loaded_distance_km": round(loaded_dist, 1),
        "dropoff_to_depot_km": round(dropoff_to_depot, 1),
        "detour_km": round(detour_km, 1),
    }


# ── 2. Empty-KM, Cost & Scoring Math ──────────────────────────────────────────

def calculate_match_metrics(
    vehicle: Vehicle,
    shipment: Shipment,
    current_city: str,
    home_city: str,
) -> Dict[str, Any]:
    """
    Perform transparent mathematical calculations for:
    - Empty-km before & after
    - Empty-km reduction & percentage
    - Fuel and operational costs
    - Deterministic matching score (0–100)
    """
    empty_before = get_safe_city_distance(current_city, home_city)
    if empty_before <= 0.0:
        empty_before = get_safe_city_distance(shipment.origin_city, shipment.destination_city) or 100.0

    pickup_deadhead = get_safe_city_distance(current_city, shipment.origin_city)
    loaded_km = get_safe_city_distance(shipment.origin_city, shipment.destination_city)
    if loaded_km <= 0.0:
        loaded_km = 50.0  # minimal intra-city leg

    dropoff_deadhead = get_safe_city_distance(shipment.destination_city, home_city)
    total_trip_km = pickup_deadhead + loaded_km + dropoff_deadhead

    detour_km = max(0.0, total_trip_km - empty_before)
    empty_after = pickup_deadhead + dropoff_deadhead
    empty_km_reduced = max(0.0, empty_before - empty_after)
    empty_km_reduction_pct = round((empty_km_reduced / max(1.0, empty_before)) * 100.0, 2)

    fuel_eff = float(vehicle.fuel_efficiency_kmpl or 5.0)
    fuel_type = vehicle.fuel_type or "diesel"
    veh_type = vehicle.vehicle_type or "medium_truck"

    # Baseline cost without return cargo (driving empty straight back)
    cost_empty_direct = calculate_route_cost(
        total_distance_km=empty_before,
        empty_distance_km=empty_before,
        fuel_efficiency_kmpl=fuel_eff,
        fuel_type=fuel_type,
        vehicle_type=veh_type,
        road_type="mixed",
        payload_kg=0.0,
    )

    # Cost with return cargo trip
    cost_with_cargo = calculate_route_cost(
        total_distance_km=total_trip_km,
        empty_distance_km=empty_after,
        fuel_efficiency_kmpl=fuel_eff,
        fuel_type=fuel_type,
        vehicle_type=veh_type,
        road_type="mixed",
        payload_kg=float(shipment.weight_kg),
    )

    add_fuel_l = max(0.0, cost_with_cargo.fuel_litres - cost_empty_direct.fuel_litres)
    add_fuel_cost = max(0.0, cost_with_cargo.fuel_cost_inr - cost_empty_direct.fuel_cost_inr)
    add_toll_cost = max(0.0, cost_with_cargo.toll_cost_inr - cost_empty_direct.toll_cost_inr)
    total_add_cost = max(0.0, cost_with_cargo.total_cost_inr - cost_empty_direct.total_cost_inr)

    # Market freight value estimation
    weight_tonnes = float(shipment.weight_kg) / 1000.0
    estimated_revenue = round(
        max(1200.0, loaded_km * 16.0 * max(0.5, weight_tonnes)), 2
    )

    # Net financial benefit: revenue - added costs + deadhead savings benefit
    deadhead_savings_val = empty_km_reduced * 5.0
    net_benefit = round(estimated_revenue - total_add_cost + deadhead_savings_val, 2)

    # ── Deterministic Score (0–100) ───────────────────────────────────────────
    # 1. Empty-km reduction (0–40 pts)
    score_empty_km = min(40.0, max(0.0, (empty_km_reduced / max(1.0, empty_before)) * 40.0))

    # 2. Capacity utilization (0–25 pts)
    cap_util = min(1.0, float(shipment.weight_kg) / max(1.0, float(vehicle.capacity_weight_kg)))
    score_utilization = cap_util * 25.0

    # 3. Route detour score (0–20 pts)
    detour_ratio = detour_km / max(1.0, empty_before)
    score_detour = max(0.0, min(20.0, 20.0 * (1.0 - min(1.0, detour_ratio / 0.5))))

    # 4. Economic net benefit score (0–15 pts)
    score_economics = min(15.0, max(0.0, (net_benefit / 5000.0) * 15.0))

    total_score = round(score_empty_km + score_utilization + score_detour + score_economics, 1)
    total_score = max(0.0, min(100.0, total_score))

    return {
        "empty_km_before": round(empty_before, 1),
        "empty_km_after": round(empty_after, 1),
        "empty_km_reduced": round(empty_km_reduced, 1),
        "empty_km_reduction_pct": empty_km_reduction_pct,
        "loaded_distance_km": round(loaded_km, 1),
        "detour_distance_km": round(detour_km, 1),
        "total_trip_km": round(total_trip_km, 1),
        "additional_fuel_l": round(add_fuel_l, 2),
        "additional_fuel_cost_inr": round(add_fuel_cost, 2),
        "additional_toll_cost_inr": round(add_toll_cost, 2),
        "total_additional_cost_inr": round(total_add_cost, 2),
        "estimated_revenue_inr": estimated_revenue,
        "net_benefit_inr": net_benefit,
        "match_score": total_score,
        "score_breakdown": {
            "empty_km_score": round(score_empty_km, 1),
            "utilization_score": round(score_utilization, 1),
            "detour_score": round(score_detour, 1),
            "economic_score": round(score_economics, 1),
        },
    }


# ── 3. Match Finder & Opportunity Scanner ─────────────────────────────────────

def find_return_matches_for_vehicle(
    vehicle: Vehicle,
    db: Session,
    current_city: Optional[str] = None,
    home_city: Optional[str] = None,
    max_detour_km: float = 300.0,
    min_score: float = 0.0,
) -> List[Dict[str, Any]]:
    """
    Search all unassigned / pending shipments in the database and find
    compatible return cargo matches for the specified vehicle.
    """
    curr_city = current_city or vehicle.current_city or "Mumbai"
    h_city = home_city or vehicle.home_depot_city or "Mumbai"

    # Query pending shipments that need transport
    pending_shipments = (
        db.query(Shipment)
        .filter(Shipment.status.in_(["pending", "consolidated"]))
        .all()
    )

    matches = []
    for shipment in pending_shipments:
        compatible, compat_details = evaluate_compatibility(
            vehicle=vehicle,
            shipment=shipment,
            current_city=curr_city,
            home_city=h_city,
            max_detour_km=max_detour_km,
        )

        metrics = calculate_match_metrics(
            vehicle=vehicle,
            shipment=shipment,
            current_city=curr_city,
            home_city=h_city,
        )

        if metrics["match_score"] >= min_score:
            matches.append({
                "vehicle": vehicle,
                "shipment": shipment,
                "is_compatible": compatible,
                "compatibility_details": {
                    **compat_details,
                    "score_breakdown": metrics["score_breakdown"],
                },
                "metrics": metrics,
                "vehicle_current_city": curr_city,
                "vehicle_home_city": h_city,
            })

    # Sort descending by match_score
    matches.sort(key=lambda m: (m["is_compatible"], m["metrics"]["match_score"]), reverse=True)
    return matches


def persist_return_matches(
    vehicle: Vehicle,
    matches: List[Dict[str, Any]],
    db: Session,
) -> List[ReturnCargoMatch]:
    """
    Save or update evaluated matches in the return_cargo_matches table.
    """
    persisted = []
    for m in matches:
        shipment = m["shipment"]
        metrics = m["metrics"]

        # Check if an existing match record exists
        existing = (
            db.query(ReturnCargoMatch)
            .filter(
                ReturnCargoMatch.vehicle_id == vehicle.id,
                ReturnCargoMatch.shipment_id == shipment.id,
                ReturnCargoMatch.status == "pending",
            )
            .first()
        )

        if existing:
            # Update metrics
            existing.empty_km_before = metrics["empty_km_before"]
            existing.empty_km_after = metrics["empty_km_after"]
            existing.empty_km_reduced = metrics["empty_km_reduced"]
            existing.empty_km_reduction_pct = metrics["empty_km_reduction_pct"]
            existing.loaded_distance_km = metrics["loaded_distance_km"]
            existing.detour_distance_km = metrics["detour_distance_km"]
            existing.additional_fuel_l = metrics["additional_fuel_l"]
            existing.additional_fuel_cost_inr = metrics["additional_fuel_cost_inr"]
            existing.additional_toll_cost_inr = metrics["additional_toll_cost_inr"]
            existing.total_additional_cost_inr = metrics["total_additional_cost_inr"]
            existing.estimated_revenue_inr = metrics["estimated_revenue_inr"]
            existing.net_benefit_inr = metrics["net_benefit_inr"]
            existing.match_score = metrics["match_score"]
            existing.compatibility_details = m["compatibility_details"]
            persisted.append(existing)
        else:
            match_row = ReturnCargoMatch(
                vehicle_id=vehicle.id,
                shipment_id=shipment.id,
                origin_city=shipment.origin_city,
                destination_city=shipment.destination_city,
                vehicle_current_city=m["vehicle_current_city"],
                vehicle_home_city=m["vehicle_home_city"],
                empty_km_before=metrics["empty_km_before"],
                empty_km_after=metrics["empty_km_after"],
                empty_km_reduced=metrics["empty_km_reduced"],
                empty_km_reduction_pct=metrics["empty_km_reduction_pct"],
                loaded_distance_km=metrics["loaded_distance_km"],
                detour_distance_km=metrics["detour_distance_km"],
                additional_fuel_l=metrics["additional_fuel_l"],
                additional_fuel_cost_inr=metrics["additional_fuel_cost_inr"],
                additional_toll_cost_inr=metrics["additional_toll_cost_inr"],
                total_additional_cost_inr=metrics["total_additional_cost_inr"],
                estimated_revenue_inr=metrics["estimated_revenue_inr"],
                net_benefit_inr=metrics["net_benefit_inr"],
                match_score=metrics["match_score"],
                compatibility_details=m["compatibility_details"],
                status="pending",
            )
            db.add(match_row)
            persisted.append(match_row)

    try:
        db.commit()
        for p in persisted:
            db.refresh(p)
    except Exception as e:
        db.rollback()
        logger.error("Failed to persist return cargo matches: %s", e)
        raise

    return persisted


# ── 4. Approval & Return Route Execution ──────────────────────────────────────

def execute_approve_return_match(
    match: ReturnCargoMatch,
    approver_user_id: Optional[uuid.UUID],
    db: Session,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Approve a return cargo match and execute route generation:
    1. Update match status to 'approved'
    2. Create return Route and RouteStops in DB
    3. Update Shipment status to 'assigned'
    4. Update Vehicle status to 'in_transit'
    5. Emit multi-role notifications
    """
    if match.status == "approved":
        raise ValueError("Match is already approved")

    vehicle = match.vehicle
    shipment = match.shipment
    if not vehicle or not shipment:
        raise ValueError("Vehicle or Shipment missing from match")

    try:
        # 1. Update Match record
        match.status = "approved"
        # Safe approver user verification
        if approver_user_id:
            approver = db.query(User).filter(User.id == approver_user_id).first()
            match.approved_by = approver_user_id if approver else None
        match.approved_at = datetime.now(timezone.utc)

        # 2. Create Return Route
        route_number = f"RET-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:5].upper()}"
        total_dist = float(match.loaded_distance_km + match.detour_distance_km)
        if total_dist <= 0.0:
            total_dist = float(match.empty_km_before) or 100.0

        est_duration_min = int((total_dist / 55.0) * 60) + 60  # driving time + loading/unloading buffer

        cost_res = calculate_route_cost(
            total_distance_km=total_dist,
            empty_distance_km=float(match.empty_km_after),
            fuel_efficiency_kmpl=float(vehicle.fuel_efficiency_kmpl),
            fuel_type=vehicle.fuel_type,
            vehicle_type=vehicle.vehicle_type,
            road_type="mixed",
            payload_kg=float(shipment.weight_kg),
        )

        return_route = Route(
            route_number=route_number,
            vehicle_id=vehicle.id,
            driver_id=vehicle.driver.id if vehicle.driver else None,
            origin_city=match.vehicle_current_city,
            destination_city=match.vehicle_home_city,
            total_distance_km=total_dist,
            estimated_duration_min=est_duration_min,
            estimated_fuel_l=cost_res.fuel_litres,
            estimated_fuel_cost_inr=cost_res.fuel_cost_inr,
            estimated_toll_inr=cost_res.toll_cost_inr,
            driver_cost_inr=cost_res.driver_cost_inr,
            total_estimated_cost_inr=cost_res.total_cost_inr,
            estimated_co2_kg=cost_res.co2_kg,
            status="in_progress",
            planned_start_time=datetime.now(timezone.utc),
            planned_end_time=datetime.now(timezone.utc) + timedelta(minutes=est_duration_min),
        )
        db.add(return_route)
        db.flush()

        # Link match to return route
        match.return_route_id = return_route.id

        # 3. Create Route Stops
        # Stop 1: Pickup Stop
        stop1 = RouteStop(
            route_id=return_route.id,
            shipment_id=shipment.id,
            stop_sequence=1,
            stop_type="pickup",
            city=shipment.origin_city,
            address=shipment.origin_address or f"{shipment.origin_city} Depot",
            lat=shipment.origin_lat or 19.0760,
            lon=shipment.origin_lon or 72.8777,
            planned_arrival=datetime.now(timezone.utc) + timedelta(minutes=30),
            planned_departure=datetime.now(timezone.utc) + timedelta(minutes=60),
            status="pending",
        )
        db.add(stop1)

        # Stop 2: Delivery Stop
        stop2 = RouteStop(
            route_id=return_route.id,
            shipment_id=shipment.id,
            stop_sequence=2,
            stop_type="delivery",
            city=shipment.destination_city,
            address=shipment.destination_address or f"{shipment.destination_city} Warehouse",
            lat=shipment.destination_lat or 28.7041,
            lon=shipment.destination_lon or 77.1025,
            planned_arrival=datetime.now(timezone.utc) + timedelta(minutes=est_duration_min - 30),
            planned_departure=datetime.now(timezone.utc) + timedelta(minutes=est_duration_min),
            status="pending",
        )
        db.add(stop2)

        # 4. Update Shipment & Vehicle Statuses
        shipment.status = "assigned"
        shipment.assigned_route_id = return_route.id
        vehicle.status = "in_transit"

        db.commit()

        # 5. Create In-App Notifications
        _create_return_cargo_notifications(match, return_route, vehicle, shipment, db)

        logger.info(
            "Approved return cargo match %s, created route %s, reduced empty km by %.1f km",
            match.id,
            route_number,
            match.empty_km_reduced,
        )

        fuel_saved_l = float(match.empty_km_reduced) / max(0.1, float(vehicle.fuel_efficiency_kmpl))
        cost_saved_inr = float(match.net_benefit_inr)

        return {
            "success": True,
            "match_id": match.id,
            "vehicle_id": vehicle.id,
            "shipment_id": shipment.id,
            "return_route_id": return_route.id,
            "return_route_number": route_number,
            "total_distance_km": total_dist,
            "empty_km_reduced": float(match.empty_km_reduced),
            "empty_km_reduction_pct": float(match.empty_km_reduction_pct),
            "estimated_fuel_saved_l": round(fuel_saved_l, 2),
            "estimated_cost_saved_inr": round(cost_saved_inr, 2),
            "new_eta": return_route.planned_end_time.isoformat() if return_route.planned_end_time else None,
            "message": (
                f"Return cargo approved. Route {route_number} created with {match.empty_km_reduction_pct:.1f}% "
                f"deadhead reduction ({match.empty_km_reduced:.0f} empty km saved)."
            ),
        }

    except Exception as e:
        db.rollback()
        logger.error("Failed to approve return cargo match: %s", e, exc_info=True)
        raise


def _create_return_cargo_notifications(
    match: ReturnCargoMatch,
    route: Route,
    vehicle: Vehicle,
    shipment: Shipment,
    db: Session,
):
    """Emit notifications to operators and assigned drivers."""
    try:
        operators = db.query(User).filter(User.role.in_(["admin", "fleet_operator"])).all()
        for op in operators:
            db.add(
                Notification(
                    user_id=op.id,
                    notification_type="return_cargo_matched",
                    title="🚛 Return Cargo Assigned — Empty-KM Reduced",
                    message=(
                        f"Vehicle {vehicle.registration_number} assigned return cargo {shipment.shipment_number} "
                        f"({shipment.origin_city} → {shipment.destination_city}). "
                        f"Saved {match.empty_km_reduced:.0f} empty km ({match.empty_km_reduction_pct:.1f}% reduction). "
                        f"Net benefit: ₹{match.net_benefit_inr:.0f}."
                    ),
                    data_json={
                        "match_id": str(match.id),
                        "route_id": str(route.id),
                        "vehicle_id": str(vehicle.id),
                        "shipment_id": str(shipment.id),
                    },
                    is_read=False,
                )
            )

        if vehicle.driver and vehicle.driver.user_id:
            db.add(
                Notification(
                    user_id=vehicle.driver.user_id,
                    notification_type="trip_assignment",
                    title="📦 Return Trip Assigned",
                    message=(
                        f"You have been assigned return cargo {shipment.shipment_number} from "
                        f"{shipment.origin_city} to {shipment.destination_city}. "
                        f"Route {route.route_number} is ready."
                    ),
                    data_json={"route_id": str(route.id)},
                    is_read=False,
                )
            )
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning("Could not create return cargo notifications: %s", e)
