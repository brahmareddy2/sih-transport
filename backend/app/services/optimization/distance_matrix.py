"""
Distance and travel-time calculations for Indian logistics routes.

Uses Haversine great-circle distance between GPS coordinates and applies
realistic average speeds by road type to estimate travel time.

Indian speed model (source: NHAI / field experience):
  - National Highway (NH): avg 70 km/h
  - State Highway (SH)  : avg 50 km/h
  - Local / urban       : avg 30 km/h
  - Mixed (default)     : avg 55 km/h
"""
import math
from typing import Optional

# ── 12 Indian Cities with GPS coordinates ────────────────────
INDIAN_CITIES: dict[str, dict] = {
    "Mumbai": {
        "lat": 19.0760, "lon": 72.8777,
        "state": "Maharashtra", "zone": "west",
        "is_metro": True,
    },
    "Delhi": {
        "lat": 28.7041, "lon": 77.1025,
        "state": "Delhi", "zone": "north",
        "is_metro": True,
    },
    "Bangalore": {
        "lat": 12.9716, "lon": 77.5946,
        "state": "Karnataka", "zone": "south",
        "is_metro": True,
    },
    "Hyderabad": {
        "lat": 17.3850, "lon": 78.4867,
        "state": "Telangana", "zone": "south",
        "is_metro": True,
    },
    "Chennai": {
        "lat": 13.0827, "lon": 80.2707,
        "state": "Tamil Nadu", "zone": "south",
        "is_metro": True,
    },
    "Kolkata": {
        "lat": 22.5726, "lon": 88.3639,
        "state": "West Bengal", "zone": "east",
        "is_metro": True,
    },
    "Pune": {
        "lat": 18.5204, "lon": 73.8567,
        "state": "Maharashtra", "zone": "west",
        "is_metro": False,
    },
    "Ahmedabad": {
        "lat": 23.0225, "lon": 72.5714,
        "state": "Gujarat", "zone": "west",
        "is_metro": False,
    },
    "Jaipur": {
        "lat": 26.9124, "lon": 75.7873,
        "state": "Rajasthan", "zone": "north",
        "is_metro": False,
    },
    "Lucknow": {
        "lat": 26.8467, "lon": 80.9462,
        "state": "Uttar Pradesh", "zone": "north",
        "is_metro": False,
    },
    "Nagpur": {
        "lat": 21.1458, "lon": 79.0882,
        "state": "Maharashtra", "zone": "central",
        "is_metro": False,
    },
    "Surat": {
        "lat": 21.1702, "lon": 72.8311,
        "state": "Gujarat", "zone": "west",
        "is_metro": False,
    },
}

CITY_NAMES = list(INDIAN_CITIES.keys())

# ── Road-type speed assumptions (km/h) ───────────────────────
ROAD_SPEEDS = {
    "nh_only": 70,   # National Highway express
    "mixed": 55,     # Typical inter-city mix NH + SH
    "sh": 50,        # State highway dominant
    "local": 30,     # Urban / intra-city
    "urban": 25,     # Dense urban congestion
}

# ── Toll rate per km by vehicle type (₹/km on NH) ────────────
TOLL_RATE_INR_PER_KM: dict[str, float] = {
    "mini_truck": 1.50,
    "tempo": 1.50,
    "medium_truck": 2.20,
    "large_truck": 3.00,
    "trailer": 4.50,
}

# Fraction of total distance that is NH (toll-bearing) for inter-city routes
NH_FRACTION = 0.65  # ~65% of inter-city distance is on NH in India

# ── Diesel price (INR/litre) ─────────────────────────────────
DIESEL_PRICE_INR_PER_L = 93.0   # All-India average (2024)
CO2_PER_LITRE_DIESEL_KG = 2.68  # IPCC emission factor


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Compute great-circle distance in km between two GPS points
    using the Haversine formula.
    """
    R = 6371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def road_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Estimate actual road distance from straight-line Haversine distance.
    Indian roads have a detour factor of ~1.25–1.40 depending on terrain.
    """
    straight = haversine_km(lat1, lon1, lat2, lon2)
    if straight < 50:
        detour_factor = 1.35   # Urban / intra-city — more winding
    elif straight < 200:
        detour_factor = 1.28   # Short inter-city
    else:
        detour_factor = 1.22   # Long-haul — NH is more direct
    return round(straight * detour_factor, 1)


def travel_time_minutes(
    distance_km: float,
    road_type: str = "mixed",
    loading_time_min: int = 30,
    unloading_time_min: int = 30,
) -> int:
    """
    Estimate travel time including loading/unloading buffer.
    Returns total minutes.
    """
    speed = ROAD_SPEEDS.get(road_type, ROAD_SPEEDS["mixed"])
    drive_hours = distance_km / speed
    drive_minutes = drive_hours * 60
    return int(drive_minutes + loading_time_min + unloading_time_min)


def city_distance_km(origin: str, destination: str) -> float:
    """Compute road distance between two named Indian cities."""
    if origin == destination:
        return 0.0
    o = INDIAN_CITIES[origin]
    d = INDIAN_CITIES[destination]
    return road_distance_km(o["lat"], o["lon"], d["lat"], d["lon"])


def city_travel_time_min(origin: str, destination: str, road_type: str = "mixed") -> int:
    """Compute travel time (minutes) between two named Indian cities."""
    dist = city_distance_km(origin, destination)
    return travel_time_minutes(dist, road_type, loading_time_min=0, unloading_time_min=0)


def build_distance_matrix(cities: list[str]) -> list[list[float]]:
    """
    Build an N×N distance matrix (km) for a list of city names.
    Used by the OR-Tools VRP solver.
    """
    n = len(cities)
    matrix = [[0.0] * n for _ in range(n)]
    for i, c1 in enumerate(cities):
        for j, c2 in enumerate(cities):
            if i != j:
                matrix[i][j] = city_distance_km(c1, c2)
    return matrix


def build_time_matrix(cities: list[str], road_type: str = "mixed") -> list[list[int]]:
    """
    Build an N×N travel-time matrix (minutes) for a list of city names.
    Used by the OR-Tools VRP solver for time-window constraints.
    """
    n = len(cities)
    matrix = [[0] * n for _ in range(n)]
    for i, c1 in enumerate(cities):
        for j, c2 in enumerate(cities):
            if i != j:
                matrix[i][j] = city_travel_time_min(c1, c2, road_type)
    return matrix


def coords_for_city(city: str) -> tuple[float, float]:
    """Return (lat, lon) for a city name."""
    c = INDIAN_CITIES[city]
    return c["lat"], c["lon"]


def same_zone(city1: str, city2: str) -> bool:
    """Return True if both cities are in the same logistics zone."""
    return INDIAN_CITIES[city1]["zone"] == INDIAN_CITIES[city2]["zone"]
