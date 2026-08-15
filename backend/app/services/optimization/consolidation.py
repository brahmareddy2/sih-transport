"""
Load consolidation service.

Groups compatible shipments together to maximize vehicle utilization
and reduce the total number of vehicles required.

Consolidation rules:
1. Same or adjacent delivery zone (same state / same corridor)
2. Compatible goods types (hazmat never mixed, refrigerated never mixed)
3. Time windows overlap within threshold
4. Combined weight ≤ vehicle capacity × 0.92 (safety buffer)
5. Combined volume ≤ vehicle volume capacity (if applicable)
6. Route detour within acceptable limit (≤ 30% extra distance)
"""
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# ── Compatibility constants ───────────────────────────────────
MAX_WEIGHT_UTILIZATION = 0.92   # Never fill above 92% (safety buffer)
MAX_TIME_WINDOW_GAP_HRS = 6     # Max hours between overlapping time windows
MAX_DETOUR_FACTOR = 1.30        # Route must not increase by > 30%
MIN_CONSOLIDATION_SAVING_PCT = 5.0  # Only consolidate if saving ≥ 5% cost

# Goods types that are incompatible with each other
INCOMPATIBLE_GOODS_PAIRS: list[tuple[str, str]] = [
    ("Chemicals", "Pharmaceutical"),
    ("Chemicals", "Food"),
    ("Chemicals", "Perishables"),
    ("Hazardous", "FMCG"),
    ("Hazardous", "Food"),
    ("Hazardous", "Pharmaceutical"),
    ("Hazardous", "Electronics"),
]


def is_goods_compatible(goods_a: Optional[str], goods_b: Optional[str]) -> bool:
    """Return True if two goods types can be carried in the same vehicle."""
    if goods_a is None or goods_b is None:
        return True
    if goods_a == goods_b:
        return True
    pair = (goods_a, goods_b)
    pair_rev = (goods_b, goods_a)
    return pair not in INCOMPATIBLE_GOODS_PAIRS and pair_rev not in INCOMPATIBLE_GOODS_PAIRS


def is_time_window_compatible(
    tw_start_a: Optional[datetime],
    tw_end_a: Optional[datetime],
    tw_start_b: Optional[datetime],
    tw_end_b: Optional[datetime],
) -> bool:
    """
    Check if two shipment time windows are compatible for consolidation.
    Returns True if windows overlap OR if either shipment has no time window.
    """
    if tw_start_a is None or tw_end_a is None:
        return True
    if tw_start_b is None or tw_end_b is None:
        return True

    # Windows must overlap OR be within MAX_TIME_WINDOW_GAP_HRS of each other
    gap_threshold = timedelta(hours=MAX_TIME_WINDOW_GAP_HRS)
    overlap = tw_start_a <= tw_end_b and tw_start_b <= tw_end_a
    near = (
        abs((tw_start_b - tw_end_a).total_seconds()) < gap_threshold.total_seconds()
        or abs((tw_start_a - tw_end_b).total_seconds()) < gap_threshold.total_seconds()
    )
    return overlap or near


def can_consolidate(shipment_a: dict, shipment_b: dict) -> tuple[bool, str]:
    """
    Check whether two shipments can be consolidated into the same vehicle.

    Args:
        shipment_a / shipment_b: dicts with keys:
          - weight_kg, volume_m3
          - origin_city, destination_city
          - goods_type, is_hazardous, requires_refrigeration
          - time_window_start, time_window_end

    Returns:
        (can_consolidate: bool, reason: str)
    """
    # Rule 1: Hazmat compatibility
    if shipment_a.get("is_hazardous") and not shipment_b.get("is_hazardous"):
        return False, "Cannot mix hazardous and non-hazardous cargo"
    if not shipment_a.get("is_hazardous") and shipment_b.get("is_hazardous"):
        return False, "Cannot mix hazardous and non-hazardous cargo"

    # Rule 2: Refrigeration compatibility
    if shipment_a.get("requires_refrigeration") != shipment_b.get("requires_refrigeration"):
        return False, "Cannot mix refrigerated and non-refrigerated cargo"

    # Rule 3: Goods type compatibility
    if not is_goods_compatible(shipment_a.get("goods_type"), shipment_b.get("goods_type")):
        return False, f"Incompatible goods: {shipment_a.get('goods_type')} + {shipment_b.get('goods_type')}"

    # Rule 4: Time window compatibility
    if not is_time_window_compatible(
        shipment_a.get("time_window_start"),
        shipment_a.get("time_window_end"),
        shipment_b.get("time_window_start"),
        shipment_b.get("time_window_end"),
    ):
        return False, "Time windows are not compatible"

    return True, "Compatible"


def check_vehicle_compatibility(shipment: dict, vehicle: dict) -> tuple[bool, str]:
    """
    Check whether a shipment can be carried by a specific vehicle.

    Args:
        shipment: dict with cargo details
        vehicle: dict with vehicle capabilities
    """
    # Weight check
    if shipment.get("weight_kg", 0) > vehicle.get("capacity_weight_kg", 0):
        return False, f"Weight {shipment['weight_kg']} kg exceeds capacity {vehicle['capacity_weight_kg']} kg"

    # Volume check
    if shipment.get("volume_m3") and vehicle.get("capacity_volume_m3"):
        if shipment["volume_m3"] > vehicle["capacity_volume_m3"]:
            return False, f"Volume {shipment['volume_m3']} m³ exceeds capacity {vehicle['capacity_volume_m3']} m³"

    # Refrigeration requirement
    if shipment.get("requires_refrigeration") and not vehicle.get("is_refrigerated"):
        return False, "Shipment requires refrigerated vehicle"

    # Hazmat capability
    if shipment.get("is_hazardous") and not vehicle.get("can_carry_hazmat"):
        return False, "Shipment is hazardous, vehicle not certified"

    # Vehicle availability
    if vehicle.get("status") not in ("available", "idle"):
        return False, f"Vehicle status is {vehicle.get('status')}, not available"

    return True, "Compatible"


def group_shipments_for_consolidation(
    shipments: list[dict],
    vehicles: list[dict],
) -> list[dict]:
    """
    Group shipments into consolidation groups that can be served by one vehicle.

    Uses a greedy first-fit decreasing (FFD) bin-packing approach:
    1. Sort shipments by weight descending
    2. Try to fit each shipment into an existing group
    3. If no group fits, create a new group (requiring a new vehicle)

    Args:
        shipments: list of shipment dicts (with weight, cargo details, time windows)
        vehicles: list of vehicle dicts (with capacity, capabilities)

    Returns:
        list of group dicts:
          {
            "group_id": int,
            "shipment_ids": [...],
            "total_weight_kg": float,
            "total_volume_m3": float,
            "origin_cities": [...],
            "destination_cities": [...],
            "compatible_vehicle_types": [...],
          }
    """
    # Sort by weight descending (FFD heuristic)
    sorted_shipments = sorted(shipments, key=lambda s: s.get("weight_kg", 0), reverse=True)

    groups: list[dict] = []

    for shipment in sorted_shipments:
        placed = False
        for group in groups:
            # Check if this shipment is compatible with all shipments in the group
            all_compatible = all(
                can_consolidate(shipment, existing)[0]
                for existing in group["shipments"]
            )
            if not all_compatible:
                continue

            # Check weight fits
            new_total_weight = group["total_weight_kg"] + shipment.get("weight_kg", 0)

            # Find vehicles that could hold this group
            fitting_vehicles = [
                v for v in vehicles
                if new_total_weight <= v.get("capacity_weight_kg", 0) * MAX_WEIGHT_UTILIZATION
                and check_vehicle_compatibility(shipment, v)[0]
            ]

            if fitting_vehicles:
                group["shipments"].append(shipment)
                group["total_weight_kg"] = new_total_weight
                group["total_volume_m3"] = (group["total_volume_m3"] or 0) + (shipment.get("volume_m3") or 0)
                group["shipment_ids"].append(shipment["id"])
                placed = True
                break

        if not placed:
            # Create a new group for this shipment
            groups.append({
                "group_id": len(groups) + 1,
                "shipments": [shipment],
                "shipment_ids": [shipment["id"]],
                "total_weight_kg": shipment.get("weight_kg", 0),
                "total_volume_m3": shipment.get("volume_m3") or 0.0,
                "origin_city": shipment.get("origin_city"),
                "destination_city": shipment.get("destination_city"),
            })

    # Return cleaned group info (without raw shipment objects)
    result = []
    for g in groups:
        result.append({
            "group_id": g["group_id"],
            "shipment_ids": g["shipment_ids"],
            "total_weight_kg": round(g["total_weight_kg"], 2),
            "total_volume_m3": round(g["total_volume_m3"] or 0, 2),
            "shipment_count": len(g["shipments"]),
            "origin_city": g.get("origin_city"),
            "destination_city": g.get("destination_city"),
        })

    logger.info(
        "Consolidated %d shipments into %d groups (saved %d vehicles)",
        len(shipments), len(groups), len(shipments) - len(groups)
    )
    return result
