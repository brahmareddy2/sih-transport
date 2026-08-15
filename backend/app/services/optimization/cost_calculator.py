"""
Cost calculation engine for Indian logistics routes.

Calculates:
  - Fuel cost (INR) based on distance and vehicle efficiency
  - Toll cost (INR) using rule-based NH toll rates
  - Driver cost (INR) flat daily + overtime
  - CO2 emissions (kg)
  - Empty km penalty (INR)
  - Total route cost (INR)
"""
from dataclasses import dataclass
from typing import Optional

from app.services.optimization.distance_matrix import (
    DIESEL_PRICE_INR_PER_L,
    CO2_PER_LITRE_DIESEL_KG,
    TOLL_RATE_INR_PER_KM,
    NH_FRACTION,
)


# ── Fuel prices by type (INR/litre) ──────────────────────────
FUEL_PRICES: dict[str, float] = {
    "diesel": 93.0,
    "petrol": 103.0,
    "cng": 78.0,   # per kg (approx equivalent)
    "ev": 0.0,     # operating cost handled separately
}

# ── Driver cost parameters (INR) ─────────────────────────────
DRIVER_DAILY_WAGE_INR = 650.0       # ₹650/day base wage
DRIVER_OVERTIME_INR_PER_HOUR = 60.0 # ₹60/hour for hours > 8
DRIVER_BATTA_PER_DAY = 150.0        # Per-diem / meal allowance

# ── Vehicle operating cost (₹/km) beyond fuel ────────────────
VEHICLE_OPEX_PER_KM: dict[str, float] = {
    "mini_truck":   2.5,
    "tempo":        3.0,
    "medium_truck": 4.5,
    "large_truck":  6.0,
    "trailer":      9.0,
}

# ── CO2 emission factors ──────────────────────────────────────
CO2_FACTOR_KG_PER_L: dict[str, float] = {
    "diesel": 2.68,
    "petrol": 2.31,
    "cng": 1.97,
    "ev": 0.82,   # indirect (grid emission factor India)
}


@dataclass
class RouteCostResult:
    """Detailed cost breakdown for a single route leg or full route."""
    distance_km: float
    fuel_litres: float
    fuel_cost_inr: float
    toll_cost_inr: float
    driver_cost_inr: float
    vehicle_opex_inr: float
    empty_km: float
    empty_km_cost_inr: float
    co2_kg: float
    total_cost_inr: float
    cost_per_kg_inr: float = 0.0
    cost_per_km_inr: float = 0.0

    def to_dict(self) -> dict:
        return {
            "distance_km": round(self.distance_km, 1),
            "fuel_litres": round(self.fuel_litres, 2),
            "fuel_cost_inr": round(self.fuel_cost_inr, 2),
            "toll_cost_inr": round(self.toll_cost_inr, 2),
            "driver_cost_inr": round(self.driver_cost_inr, 2),
            "vehicle_opex_inr": round(self.vehicle_opex_inr, 2),
            "empty_km": round(self.empty_km, 1),
            "empty_km_cost_inr": round(self.empty_km_cost_inr, 2),
            "co2_kg": round(self.co2_kg, 2),
            "total_cost_inr": round(self.total_cost_inr, 2),
            "cost_per_kg_inr": round(self.cost_per_kg_inr, 4),
            "cost_per_km_inr": round(self.cost_per_km_inr, 2),
        }


def calculate_fuel_cost(
    distance_km: float,
    fuel_efficiency_kmpl: float,
    fuel_type: str = "diesel",
) -> tuple[float, float]:
    """
    Returns (fuel_litres, fuel_cost_inr).
    For EV: returns (0, 0) — handled separately as per-km charge.
    """
    if fuel_efficiency_kmpl <= 0:
        return 0.0, 0.0
    litres = distance_km / fuel_efficiency_kmpl
    price = FUEL_PRICES.get(fuel_type, FUEL_PRICES["diesel"])
    cost = litres * price
    return round(litres, 2), round(cost, 2)


def calculate_toll_cost(
    distance_km: float,
    vehicle_type: str,
    road_type: str = "mixed",
) -> float:
    """
    Rule-based toll estimation.

    Only NH (National Highway) segments have tolls.
    NH fraction varies by road type:
      - nh_only: 100% toll-bearing
      - mixed:   65% toll-bearing
      - local:   0% toll-bearing
    """
    nh_fractions = {
        "nh_only": 1.0,
        "mixed": 0.65,
        "sh": 0.35,
        "local": 0.0,
        "urban": 0.0,
    }
    nh_frac = nh_fractions.get(road_type, 0.65)
    toll_km = distance_km * nh_frac
    rate = TOLL_RATE_INR_PER_KM.get(vehicle_type, 2.0)
    return round(toll_km * rate, 2)


def calculate_driver_cost(
    total_hours: float,
    num_days: int = 1,
    include_batta: bool = True,
) -> float:
    """
    Driver wage: ₹650/day base + ₹60/hour overtime (>8h/day) + ₹150/day batta.
    """
    base = DRIVER_DAILY_WAGE_INR * num_days
    overtime_hours = max(0.0, total_hours - 8.0 * num_days)
    overtime = overtime_hours * DRIVER_OVERTIME_INR_PER_HOUR
    batta = DRIVER_BATTA_PER_DAY * num_days if include_batta else 0.0
    return round(base + overtime + batta, 2)


def calculate_co2_kg(fuel_litres: float, fuel_type: str = "diesel") -> float:
    """CO2 equivalent emissions in kg."""
    factor = CO2_FACTOR_KG_PER_L.get(fuel_type, CO2_FACTOR_KG_PER_L["diesel"])
    return round(fuel_litres * factor, 2)


def calculate_route_cost(
    total_distance_km: float,
    empty_distance_km: float,
    fuel_efficiency_kmpl: float,
    fuel_type: str,
    vehicle_type: str,
    road_type: str = "mixed",
    travel_hours: float = 0.0,
    num_days: int = 1,
    payload_kg: float = 0.0,
) -> RouteCostResult:
    """
    Full route cost calculation combining all cost components.

    Args:
        total_distance_km: Total km including empty legs
        empty_distance_km: km driven without any cargo
        fuel_efficiency_kmpl: Vehicle fuel efficiency
        fuel_type: diesel / petrol / cng / ev
        vehicle_type: mini_truck / tempo / medium_truck / large_truck / trailer
        road_type: nh_only / mixed / sh / local / urban
        travel_hours: total driving hours (for driver cost)
        num_days: number of days the trip spans
        payload_kg: total weight of cargo carried

    Returns:
        RouteCostResult with detailed breakdown
    """
    fuel_l, fuel_cost = calculate_fuel_cost(total_distance_km, fuel_efficiency_kmpl, fuel_type)
    toll_cost = calculate_toll_cost(total_distance_km, vehicle_type, road_type)
    driver_cost = calculate_driver_cost(travel_hours, num_days)
    opex_per_km = VEHICLE_OPEX_PER_KM.get(vehicle_type, 4.0)
    vehicle_opex = round(total_distance_km * opex_per_km, 2)
    co2_kg = calculate_co2_kg(fuel_l, fuel_type)

    # Empty km cost — opportunity cost at opex rate
    empty_opex = round(empty_distance_km * opex_per_km, 2)

    total = fuel_cost + toll_cost + driver_cost + vehicle_opex
    cost_per_kg = round(total / payload_kg, 4) if payload_kg > 0 else 0.0
    cost_per_km = round(total / total_distance_km, 2) if total_distance_km > 0 else 0.0

    return RouteCostResult(
        distance_km=total_distance_km,
        fuel_litres=fuel_l,
        fuel_cost_inr=fuel_cost,
        toll_cost_inr=toll_cost,
        driver_cost_inr=driver_cost,
        vehicle_opex_inr=vehicle_opex,
        empty_km=empty_distance_km,
        empty_km_cost_inr=empty_opex,
        co2_kg=co2_kg,
        total_cost_inr=total,
        cost_per_kg_inr=cost_per_kg,
        cost_per_km_inr=cost_per_km,
    )


def utilization_percentage(payload_kg: float, capacity_kg: float) -> float:
    """Weight-based vehicle utilization %."""
    if capacity_kg <= 0:
        return 0.0
    return round(min(100.0, (payload_kg / capacity_kg) * 100), 1)
