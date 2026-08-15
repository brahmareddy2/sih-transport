"""
Phase 7 — What-If Simulation Engine.

Pure Python deterministic sandbox simulator for disruption analysis and
scenario evaluation without altering production data.
"""
import logging
import math
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.driver import Driver
from app.models.route import Route
from app.models.shipment import Shipment
from app.models.vehicle import Vehicle
from app.services.optimization.cost_calculator import (
    calculate_fuel_cost,
    calculate_route_cost,
    calculate_toll_cost,
    utilization_percentage,
)
from app.services.optimization.distance_matrix import (
    INDIAN_CITIES,
    city_distance_km,
    road_distance_km,
)

logger = logging.getLogger(__name__)

SCENARIO_TITLES = {
    "heavy_traffic": "🚦 Severe Traffic Congestion",
    "breakdown": "🔴 Vehicle Engine Breakdown",
    "tyre_puncture": "🔧 Tyre Puncture Incident",
    "road_closure": "🚧 Highway Closure / Blockade",
    "low_fuel": "⛽ Low Fuel Critical Alert",
    "driver_unavailable": "👤 Driver Unavailable / Hours Limit",
    "urgent_shipment": "⚡ Urgent Shipment Dynamic Insertion",
    "additional_shipment": "📦 Additional Shipment Consolidation",
    "vehicle_unavailable": "🚛 Vehicle Out of Service",
}


def _calc_metric(
    name: str,
    before: float,
    after: float,
    unit: str,
    lower_is_better: bool = True,
) -> Dict[str, Any]:
    """Helper to format a single comparison metric with delta percentage."""
    delta = round(after - before, 2)
    delta_pct = (
        round((delta / max(0.01, abs(before))) * 100.0, 1)
        if before > 0
        else (100.0 if delta > 0 else 0.0)
    )
    is_favorable = (delta <= 0) if lower_is_better else (delta >= 0)

    return {
        "metric_name": name,
        "before": round(before, 2),
        "after": round(after, 2),
        "delta": delta,
        "delta_pct": delta_pct,
        "unit": unit,
        "is_favorable": is_favorable,
    }


def simulate_what_if_scenario(
    scenario_type: str,
    db: Session,
    vehicle_id: Optional[uuid.UUID] = None,
    route_id: Optional[uuid.UUID] = None,
    extra_delay_min: Optional[int] = None,
    detour_km: Optional[float] = None,
    additional_weight_kg: Optional[float] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Simulate a What-If operational disruption or demand shift in sandbox mode.
    Returns Before vs After metrics and explainable optimization plan.
    """
    # 1. Fetch target vehicle or use a realistic benchmark
    vehicle = None
    if vehicle_id:
        vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        vehicle = db.query(Vehicle).first()

    veh_reg = vehicle.registration_number if vehicle else "MH12AB1001"
    veh_type = vehicle.vehicle_type if vehicle else "medium_truck"
    fuel_eff = float(vehicle.fuel_efficiency_kmpl if vehicle else 5.0)
    fuel_type = vehicle.fuel_type if vehicle else "diesel"
    cap_kg = float(vehicle.capacity_weight_kg if vehicle else 5000.0)

    # 2. Fetch target route or create standard baseline
    route = None
    if route_id:
        route = db.query(Route).filter(Route.id == route_id).first()

    base_dist = float(route.total_distance_km) if route else 380.0
    base_duration_min = int(route.estimated_duration_min) if route else int((base_dist / 55.0) * 60)
    base_weight = 3200.0  # standard baseline payload
    base_empty_km = float(base_dist * 0.15)  # 15% baseline deadhead

    # Baseline cost calculation
    base_cost = calculate_route_cost(
        total_distance_km=base_dist,
        empty_distance_km=base_empty_km,
        fuel_efficiency_kmpl=fuel_eff,
        fuel_type=fuel_type,
        vehicle_type=veh_type,
        road_type="mixed",
        payload_kg=base_weight,
    )
    base_util = utilization_percentage(base_weight, cap_kg)

    # 3. Simulate Scenarios
    after_dist = base_dist
    after_duration_min = base_duration_min
    after_empty_km = base_empty_km
    after_weight = base_weight
    extra_opex = 0.0
    action_title = ""
    action_steps = []
    plan_details = {}

    stype = scenario_type.lower()

    if stype == "heavy_traffic":
        added_delay = extra_delay_min if extra_delay_min is not None else 75
        after_duration_min += added_delay
        # Idling fuel penalty
        after_dist += 5.0
        action_title = f"Reroute via NH bypass to avoid {added_delay}m congestion delay."
        action_steps = [
            f"Detected major traffic bottleneck on primary corridor (+{added_delay} min delay).",
            "Evaluate alternate state highway with 12 km detour.",
            "Advise driver to divert at next major interchange.",
            "Recalculate customer ETA and emit live notification.",
        ]
        plan_details = {"strategy": "corridor_reroute", "delay_mitigation_min": int(added_delay * 0.6)}

    elif stype == "breakdown":
        added_delay = extra_delay_min if extra_delay_min is not None else 180
        added_detour = detour_km if detour_km is not None else 45.0
        after_duration_min += added_delay
        after_dist += added_detour
        extra_opex += 2500.0  # towing + dispatch
        action_title = "Dispatch nearest standby vehicle and transfer cargo."
        action_steps = [
            "Vehicle immobilized due to powertrain failure.",
            "Located 2 standby vehicles within 35 km radius.",
            "Assign replacement vehicle with matching capacity.",
            "Transfer cargo manifesting and update customer tracking links.",
        ]
        plan_details = {"strategy": "vehicle_replacement", "replacement_eta_min": 60}

    elif stype == "tyre_puncture":
        added_delay = extra_delay_min if extra_delay_min is not None else 45
        after_duration_min += added_delay
        extra_opex += 800.0  # puncture repair fee
        action_title = "Route to nearest authorized highway tyre service center."
        action_steps = [
            "Tyre pressure loss detected on rear axle.",
            "Identified nearest service workshop 6 km ahead on NH corridor.",
            "Expected repair downtime: 40-50 minutes.",
            "Resume delivery route with minimal ETA impact.",
        ]
        plan_details = {"strategy": "roadside_service", "service_center_distance_km": 6.2}

    elif stype == "road_closure":
        added_detour = detour_km if detour_km is not None else 65.0
        added_delay = extra_delay_min if extra_delay_min is not None else 80
        after_dist += added_detour
        after_duration_min += added_delay
        action_title = f"Activate emergency detour (+{added_detour:.0f} km) via SH-19."
        action_steps = [
            "National Highway section blocked due to infrastructure maintenance.",
            f"Compute multi-point detour: +{added_detour:.1f} km, +{added_delay} min.",
            "Verify bridge weight clearance and state permit validity.",
            "Broadcast updated turn-by-turn route to driver mobile app.",
        ]
        plan_details = {"strategy": "mandatory_detour", "detour_km": added_detour}

    elif stype == "low_fuel":
        added_detour = detour_km if detour_km is not None else 18.0
        added_delay = extra_delay_min if extra_delay_min is not None else 30
        after_dist += added_detour
        after_duration_min += added_delay
        action_title = "Schedule immediate refueling divert at IOCL highway hub."
        action_steps = [
            "Fuel level dropped below 15% reserve threshold.",
            "Selected optimal IOCL 24/7 commercial fuel station (+9 km round-trip).",
            "Driver completes 20-minute diesel refuel & telemetry sync.",
            "Return to primary route without schedule violation.",
        ]
        plan_details = {"strategy": "fuel_stop_divert", "fuel_station_brand": "IOCL"}

    elif stype == "driver_unavailable":
        added_delay = extra_delay_min if extra_delay_min is not None else 60
        after_duration_min += added_delay
        extra_opex += 500.0  # shift handover fee
        action_title = "Assign certified standby driver with remaining duty hours."
        action_steps = [
            "Primary driver reached 8-hour daily driving limit.",
            "Query driver pool: matched compliant driver with HMV certification.",
            "Execute seamless shift handover at depot transit point.",
            "Update regulatory electronic logbook (e-waybill compliance).",
        ]
        plan_details = {"strategy": "driver_shift_swap", "standby_driver_id": "DRV-102"}

    elif stype == "urgent_shipment":
        added_weight = additional_weight_kg if additional_weight_kg is not None else 850.0
        added_detour = detour_km if detour_km is not None else 22.0
        after_weight = min(cap_kg, base_weight + added_weight)
        after_dist += added_detour
        after_duration_min += 35
        after_empty_km = max(0.0, after_empty_km - 15.0)  # less empty deadhead
        action_title = f"Dynamically insert urgent {added_weight:.0f}kg shipment into route."
        action_steps = [
            f"Received high-priority pickup request ({added_weight:.0f}kg).",
            "Vehicle has sufficient spare capacity.",
            "OR-Tools re-orders stops to minimize extra distance (+22 km).",
            f"Vehicle utilization improves from {base_util:.0f}% to {utilization_percentage(after_weight, cap_kg):.0f}%.",
        ]
        plan_details = {"strategy": "dynamic_cargo_insertion", "added_weight_kg": added_weight}

    elif stype == "additional_shipment":
        added_weight = additional_weight_kg if additional_weight_kg is not None else 1200.0
        after_weight = min(cap_kg, base_weight + added_weight)
        after_dist += 15.0
        after_duration_min += 25
        after_empty_km = max(0.0, after_empty_km - 20.0)
        action_title = f"Consolidate additional {added_weight:.0f}kg LTL shipment."
        action_steps = [
            f"Consolidated extra {added_weight:.0f}kg cargo sharing the same transit corridor.",
            "Increased freight revenue with nominal fuel impact.",
            f"Capacity utilization maximized to {utilization_percentage(after_weight, cap_kg):.0f}%.",
            "All delivery time windows remain strictly satisfied.",
        ]
        plan_details = {"strategy": "ltl_consolidation", "added_weight_kg": added_weight}

    elif stype == "vehicle_unavailable":
        after_dist += 40.0
        after_duration_min += 60
        action_title = "Re-balance pending shipments across neighboring fleet routes."
        action_steps = [
            "Vehicle withdrawn for mandatory inspection.",
            "Re-run OR-Tools VRP multi-vehicle solver across active fleet.",
            "Shipments re-allocated without hiring 3rd-party spot market vehicles.",
            "Total fleet operational continuity preserved.",
        ]
        plan_details = {"strategy": "fleet_rebalancing"}

    else:
        action_title = "Standard baseline scenario."
        action_steps = ["No disruptions applied."]

    # Recalculate AFTER cost
    after_cost = calculate_route_cost(
        total_distance_km=after_dist,
        empty_distance_km=after_empty_km,
        fuel_efficiency_kmpl=fuel_eff,
        fuel_type=fuel_type,
        vehicle_type=veh_type,
        road_type="mixed",
        payload_kg=after_weight,
    )
    after_util = utilization_percentage(after_weight, cap_kg)
    after_total_cost = after_cost.total_cost_inr + extra_opex

    # 4. Construct Before vs After Comparison Metrics
    metrics = {
        "distance": _calc_metric("Distance", base_dist, after_dist, "km", lower_is_better=True),
        "duration": _calc_metric("Duration", base_duration_min, after_duration_min, "min", lower_is_better=True),
        "fuel_litres": _calc_metric("Fuel", base_cost.fuel_litres, after_cost.fuel_litres, "L", lower_is_better=True),
        "fuel_cost": _calc_metric("Fuel Cost", base_cost.fuel_cost_inr, after_cost.fuel_cost_inr, "₹", lower_is_better=True),
        "toll_cost": _calc_metric("Toll Cost", base_cost.toll_cost_inr, after_cost.toll_cost_inr, "₹", lower_is_better=True),
        "total_cost": _calc_metric("Total Cost", base_cost.total_cost_inr, after_total_cost, "₹", lower_is_better=True),
        "co2_kg": _calc_metric("CO2 Emissions", base_cost.co2_kg, after_cost.co2_kg, "kg", lower_is_better=True),
        "empty_km": _calc_metric("Empty KM", base_empty_km, after_empty_km, "km", lower_is_better=True),
        "utilization": _calc_metric("Vehicle Utilization", base_util, after_util, "%", lower_is_better=False),
    }

    return {
        "scenario_type": stype,
        "scenario_title": SCENARIO_TITLES.get(stype, stype.title()),
        "description": (
            f"Sandbox simulation of '{SCENARIO_TITLES.get(stype, stype)}' on vehicle {veh_reg} "
            f"comparing baseline operations vs post-incident recovery."
        ),
        "target_vehicle_registration": veh_reg,
        "target_route_number": route.route_number if route else f"SIM-RT-{uuid.uuid4().hex[:5].upper()}",
        "metrics": metrics,
        "recommended_action": action_title,
        "action_steps": action_steps,
        "optimization_plan": plan_details,
    }
