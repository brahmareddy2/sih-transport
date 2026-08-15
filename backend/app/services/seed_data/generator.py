"""
Master synthetic data generator for the Logistics DSS.

Orchestrates generation of:
  - 50 vehicles
  - 50 drivers
  - 500 shipments
  - 300 historical trips (routes)
  - 80 incidents

SEED=42 for reproducibility.
"""
import logging
import random
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import numpy as np

from app.services.seed_data import (
    SEED, CITIES, CITY_ADDRESSES, CITY_COORDS, GOODS_NAMES, GOODS_WEIGHTS_PROB,
    VEHICLE_SPECS, generate_registration
)

logger = logging.getLogger(__name__)

# Reset seeds before generation
random.seed(SEED)
np.random.seed(SEED)

# ── Indian male/female first names ────────────────────────────
MALE_FIRST_NAMES = [
    "Rajesh", "Suresh", "Ramesh", "Mahesh", "Ganesh", "Dinesh", "Mukesh",
    "Naresh", "Umesh", "Hitesh", "Vikram", "Ajay", "Vijay", "Sanjay",
    "Ranjit", "Harjit", "Gurjit", "Manjit", "Balvir", "Jasvir",
    "Arjun", "Rahul", "Amit", "Anil", "Sunil", "Kapil", "Pankaj",
    "Vivek", "Deepak", "Ashok", "Pramod", "Vinod", "Manoj", "Santosh",
    "Ramakrishna", "Venkatesh", "Srinivas", "Mohan", "Sohan", "Ratan",
    "Pradeep", "Shiv", "Dev", "Anand", "Bhushan", "Girish", "Nilesh",
    "Rakesh", "Harish", "Sudhir",
]

LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Singh", "Kumar", "Yadav", "Patel",
    "Mehta", "Jain", "Shah", "Reddy", "Naidu", "Nair", "Pillai",
    "Iyer", "Krishnan", "Rao", "Murthy", "Gowda", "Shetty",
    "Bose", "Das", "Dutta", "Ghosh", "Banerjee", "Chakraborty",
    "Chatterjee", "Mukherjee", "Mishra", "Tripathi", "Pandey",
    "Tiwari", "Shukla", "Saxena", "Agarwal", "Malhotra", "Kapoor",
    "Khanna", "Arora", "Bhatia", "Chopra", "Gill", "Dhaliwal",
    "Sidhu", "Grewal", "Sandhu", "Bajwa", "Khatri", "Sethi", "Taneja",
]

# License types (Indian commercial vehicle driver categories)
LICENSE_TYPES = ["HMV", "HPMV", "LMV"]  # Heavy / Heavy+Passenger / Light

# Vehicle type distribution: 10 mini, 10 tempo, 15 medium, 10 large, 5 trailer
VEHICLE_TYPE_DISTRIBUTION = (
    ["mini_truck"] * 10 +
    ["tempo"] * 10 +
    ["medium_truck"] * 15 +
    ["large_truck"] * 10 +
    ["trailer"] * 5
)

# Driver license requirements by vehicle type
VEHICLE_LICENSE_MAP = {
    "mini_truck": "LMV",
    "tempo": "HMV",
    "medium_truck": "HMV",
    "large_truck": "HPMV",
    "trailer": "HPMV",
}

NOW = datetime.now(timezone.utc)
TODAY = date.today()


def generate_vehicles(n: int = 50) -> list[dict]:
    """Generate n realistic Indian commercial vehicles."""
    random.seed(SEED)
    np.random.seed(SEED)

    vehicles = []
    city_pool = CITIES * (n // len(CITIES) + 1)
    random.shuffle(city_pool)

    for i, v_type in enumerate(VEHICLE_TYPE_DISTRIBUTION[:n]):
        spec = VEHICLE_SPECS[v_type]
        make = random.choice(spec["makes"])
        model = spec["models"][make]
        city = city_pool[i]
        eff = round(random.uniform(*spec["efficiency_kmpl"]), 1)

        # Odometer: between 20k and 350k km
        odometer = round(random.uniform(20000, 350000), 0)
        # Service interval: every 30k km
        last_service = odometer - random.uniform(0, 25000)
        next_service = last_service + 30000

        # Status distribution: 75% available, 10% in_transit, 10% maintenance, 5% idle
        status_choices = ["available"] * 75 + ["in_transit"] * 10 + ["maintenance"] * 10 + ["idle"] * 5
        status = random.choice(status_choices)

        # Insurance and permit expiry
        insurance_months = random.randint(1, 24)
        permit_months = random.randint(1, 36)

        # Special capabilities
        is_refrigerated = v_type in ("large_truck", "trailer") and random.random() < 0.15
        can_carry_hazmat = v_type in ("large_truck", "trailer") and random.random() < 0.20

        reg = generate_registration(city, i)
        year = random.randint(2015, 2023)

        vehicles.append({
            "id": str(uuid.uuid4()),
            "registration_number": reg,
            "vehicle_type": v_type,
            "make": make,
            "model_name": model,
            "year": year,
            "capacity_weight_kg": spec["capacity_kg"],
            "capacity_volume_m3": spec["volume_m3"],
            "fuel_type": "diesel",
            "fuel_efficiency_kmpl": eff,
            "fuel_tank_capacity_l": spec["tank_l"],
            "current_fuel_level_l": round(random.uniform(spec["tank_l"] * 0.2, spec["tank_l"]), 1),
            "current_lat": CITY_COORDS[city][0] + random.uniform(-0.05, 0.05),
            "current_lon": CITY_COORDS[city][1] + random.uniform(-0.05, 0.05),
            "current_city": city,
            "odometer_km": odometer,
            "status": status,
            "last_service_date": TODAY - timedelta(days=int(random.uniform(30, 365))),
            "next_service_due_km": next_service,
            "insurance_expiry": TODAY + timedelta(days=insurance_months * 30),
            "permit_expiry": TODAY + timedelta(days=permit_months * 30),
            "is_refrigerated": is_refrigerated,
            "can_carry_hazmat": can_carry_hazmat,
            "home_depot_city": city,
        })

    logger.info("Generated %d vehicles", len(vehicles))
    return vehicles


def generate_drivers(n: int = 50, vehicles: list[dict] = None) -> list[dict]:
    """Generate n realistic Indian truck drivers."""
    random.seed(SEED + 1)

    drivers = []
    used_names: set[str] = set()
    vehicles = vehicles or []

    for i in range(n):
        first = random.choice(MALE_FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        # Ensure unique name combinations
        name = f"{first} {last}"
        attempt = 0
        while name in used_names and attempt < 20:
            first = random.choice(MALE_FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            name = f"{first} {last}"
            attempt += 1
        used_names.add(name)

        city = random.choice(CITIES)
        experience = random.randint(2, 25)

        # License based on experience (senior = HPMV, junior = HMV/LMV)
        if experience >= 10:
            license_type = "HPMV"
        elif experience >= 5:
            license_type = "HMV"
        else:
            license_type = random.choice(["HMV", "LMV"])

        # License expiry: 1–5 years from now
        license_expiry = TODAY + timedelta(days=random.randint(180, 1800))

        # Performance metrics
        total_trips = random.randint(experience * 30, experience * 80)
        on_time_rate = round(random.uniform(72.0, 98.5), 1)

        # Status: 65% available
        status_choices = (
            ["available"] * 65 + ["on_trip"] * 15 +
            ["off_duty"] * 10 + ["on_leave"] * 7 + ["unavailable"] * 3
        )
        status = random.choice(status_choices)

        # Assign vehicle if available and not already assigned
        assigned_vehicle_id = None
        if i < len(vehicles) and vehicles[i]["status"] not in ("maintenance", "breakdown"):
            assigned_vehicle_id = vehicles[i]["id"]

        # Employee ID: DRV-YYYY-NNNNN
        employee_id = f"DRV-{2020 + i // 15}-{str(i + 1).zfill(5)}"

        # License number: state initials + year + sequence
        state_prefix = city[:2].upper()
        license_num = f"{state_prefix}{2015 + experience % 8}{str(i + 100).zfill(5)}"

        # Phone number (Indian format: 6–9 prefix, 10 digits)
        phone_prefix = random.choice([6, 7, 8, 9])
        phone = f"+91{phone_prefix}{random.randint(100000000, 999999999)}"

        drivers.append({
            "id": str(uuid.uuid4()),
            "employee_id": employee_id,
            "license_number": license_num,
            "license_type": license_type,
            "license_expiry": license_expiry,
            "assigned_vehicle_id": assigned_vehicle_id,
            "status": status,
            "home_city": city,
            "experience_years": experience,
            "total_trips": total_trips,
            "on_time_delivery_rate": on_time_rate,
            "hours_driven_today": round(random.uniform(0, 8), 1),
            "hours_driven_this_week": round(random.uniform(0, 48), 1),
            "full_name": name,
            "phone": phone,
        })

    logger.info("Generated %d drivers", len(drivers))
    return drivers


def generate_shipments(n: int = 500) -> list[dict]:
    """Generate n realistic Indian logistics shipments."""
    random.seed(SEED + 2)
    np.random.seed(SEED + 2)

    shipments = []
    priority_choices = (
        ["urgent"] * 5 + ["high"] * 20 + ["normal"] * 60 + ["low"] * 15
    )

    for i in range(n):
        # Pick origin and destination (different cities)
        origin = random.choice(CITIES)
        dest = random.choice([c for c in CITIES if c != origin])

        # Goods type
        goods = random.choices(GOODS_NAMES, weights=GOODS_WEIGHTS_PROB, k=1)[0]

        # Weight: log-normal distribution (100–20000 kg)
        # Different distributions per goods type
        weight_params = {
            "FMCG": (7.0, 0.8),             # ~1100 kg median
            "Automotive": (8.5, 0.6),        # ~4900 kg median
            "Pharmaceutical": (6.5, 0.7),    # ~665 kg median
            "Electronics": (6.8, 0.7),       # ~898 kg median
            "Textiles": (7.5, 0.8),          # ~1808 kg median
            "Chemicals": (8.8, 0.5),         # ~6634 kg median
            "Perishables": (7.0, 0.6),       # ~1097 kg median
            "Machinery": (9.5, 0.7),         # ~13360 kg median
        }
        mu, sigma = weight_params.get(goods, (7.5, 0.8))
        weight = round(np.clip(np.random.lognormal(mu, sigma), 50, 20000), 0)

        # Volume: derived from weight and density
        density_ranges = {
            "FMCG": (200, 400),
            "Automotive": (300, 600),
            "Pharmaceutical": (150, 350),
            "Electronics": (100, 250),
            "Textiles": (100, 250),
            "Chemicals": (500, 1000),
            "Perishables": (200, 500),
            "Machinery": (500, 800),
        }
        density_min, density_max = density_ranges.get(goods, (200, 400))
        density_kgm3 = random.uniform(density_min, density_max)
        volume = round(weight / density_kgm3, 2)

        # Special requirements
        is_hazardous = goods == "Chemicals" and random.random() < 0.35
        requires_refrigeration = goods == "Perishables" and random.random() < 0.70
        if goods == "Pharmaceutical" and random.random() < 0.20:
            requires_refrigeration = True

        # Time windows: pickup within 6–72 hours, delivery window 4–48 hours
        hours_ahead = random.uniform(6, 72)
        pickup_time = NOW + timedelta(hours=hours_ahead)
        window_duration = random.uniform(4, 48)
        tw_start = pickup_time + timedelta(hours=random.uniform(2, 12))
        tw_end = tw_start + timedelta(hours=window_duration)

        priority = random.choice(priority_choices)
        if goods in ("Pharmaceutical", "Perishables"):
            priority = random.choice(["urgent", "high", "normal"])

        # Declared value (INR) — roughly proportional to weight and goods type
        value_per_kg = {
            "FMCG": random.uniform(50, 200),
            "Automotive": random.uniform(100, 500),
            "Pharmaceutical": random.uniform(500, 3000),
            "Electronics": random.uniform(1000, 8000),
            "Textiles": random.uniform(80, 400),
            "Chemicals": random.uniform(30, 200),
            "Perishables": random.uniform(20, 150),
            "Machinery": random.uniform(200, 1000),
        }
        value = round(weight * value_per_kg.get(goods, 100), 2)

        # Shipment number: SHP-2024-NNNNN
        shipment_num = f"SHP-2024-{str(i + 1).zfill(5)}"

        # Status: pending (for future optimization) or already processed
        if i < 300:  # First 300 are "historical" — already completed or in transit
            status_pool = ["delivered"] * 60 + ["in_transit"] * 20 + ["assigned"] * 10
            status = random.choice(status_pool)
        else:  # Last 200 are pending (available for optimization)
            status = "pending"

        origin_addr = random.choice(CITY_ADDRESSES[origin])
        dest_addr = random.choice(CITY_ADDRESSES[dest])

        shipments.append({
            "id": str(uuid.uuid4()),
            "shipment_number": shipment_num,
            "origin_city": origin,
            "origin_address": origin_addr,
            "origin_lat": CITY_COORDS[origin][0] + random.uniform(-0.05, 0.05),
            "origin_lon": CITY_COORDS[origin][1] + random.uniform(-0.05, 0.05),
            "destination_city": dest,
            "destination_address": dest_addr,
            "destination_lat": CITY_COORDS[dest][0] + random.uniform(-0.05, 0.05),
            "destination_lon": CITY_COORDS[dest][1] + random.uniform(-0.05, 0.05),
            "weight_kg": weight,
            "volume_m3": volume,
            "goods_type": goods,
            "is_hazardous": is_hazardous,
            "requires_refrigeration": requires_refrigeration,
            "priority": priority,
            "requested_pickup_time": pickup_time,
            "time_window_start": tw_start,
            "time_window_end": tw_end,
            "declared_value_inr": value,
            "status": status,
        })

    logger.info("Generated %d shipments", len(shipments))
    return shipments


def generate_trips_and_incidents(
    vehicles: list[dict],
    drivers: list[dict],
    n_trips: int = 300,
    n_incidents: int = 80,
) -> tuple[list[dict], list[dict]]:
    """
    Generate historical trip records and incidents.
    Returns (trips, incidents).
    """
    random.seed(SEED + 3)
    np.random.seed(SEED + 3)

    trips = []
    incidents = []

    avail_vehicles = [v for v in vehicles if v["status"] not in ("breakdown",)]
    avail_drivers = [d for d in drivers if d["status"] != "unavailable"]

    for i in range(n_trips):
        vehicle = random.choice(avail_vehicles)
        driver = random.choice(avail_drivers)

        origin = random.choice(CITIES)
        dest = random.choice([c for c in CITIES if c != origin])

        # Historical trip: started 1–90 days ago
        days_ago = random.uniform(1, 90)
        start_time = NOW - timedelta(days=days_ago)

        # Distance and duration
        from app.services.optimization.distance_matrix import city_distance_km, city_travel_time_min
        dist = city_distance_km(origin, dest)
        base_time_min = city_travel_time_min(origin, dest)

        # Actual vs planned — some trips are delayed
        is_delayed = random.random() < 0.13  # 13% delayed
        delay_min = random.randint(30, 240) if is_delayed else 0
        actual_duration = base_time_min + delay_min

        end_time = start_time + timedelta(minutes=actual_duration)

        # Fuel: actual = estimated ± 10%
        eff = vehicle["fuel_efficiency_kmpl"]
        estimated_fuel = round(dist / eff, 2)
        actual_fuel = round(estimated_fuel * random.uniform(0.90, 1.12), 2)

        # Costs in INR
        diesel_price = 93.0
        fuel_cost = round(actual_fuel * diesel_price, 2)
        toll_rate = {"mini_truck": 1.5, "tempo": 1.5, "medium_truck": 2.2, "large_truck": 3.0, "trailer": 4.5}
        toll_cost = round(dist * 0.65 * toll_rate.get(vehicle["vehicle_type"], 2.0), 2)

        status = "delayed" if is_delayed else random.choice(["completed"] * 90 + ["cancelled"] * 10)

        route_num = f"RT-{2024 if days_ago > 30 else 2025}-{str(i + 1).zfill(5)}"

        trips.append({
            "id": str(uuid.uuid4()),
            "route_number": route_num,
            "vehicle_id": vehicle["id"],
            "driver_id": driver["id"],
            "origin_city": origin,
            "destination_city": dest,
            "total_distance_km": round(dist, 1),
            "estimated_duration_min": base_time_min,
            "actual_duration_min": actual_duration,
            "estimated_fuel_l": estimated_fuel,
            "actual_fuel_l": actual_fuel,
            "estimated_fuel_cost_inr": round(estimated_fuel * diesel_price, 2),
            "actual_fuel_cost_inr": fuel_cost,
            "estimated_toll_inr": toll_cost * 0.95,
            "actual_toll_inr": toll_cost,
            "estimated_co2_kg": round(estimated_fuel * 2.68, 2),
            "actual_co2_kg": round(actual_fuel * 2.68, 2),
            "planned_start_time": start_time,
            "actual_start_time": start_time + timedelta(minutes=random.randint(0, 30)),
            "planned_end_time": start_time + timedelta(minutes=base_time_min),
            "actual_end_time": end_time,
            "status": status,
            "road_type": "mixed",
        })

    # Generate incidents
    incident_types = [
        ("breakdown", 0.40),
        ("flat_tyre", 0.25),
        ("traffic_block", 0.20),
        ("weather", 0.10),
        ("accident", 0.05),
    ]
    inc_names = [x[0] for x in incident_types]
    inc_probs = [x[1] for x in incident_types]

    severity_levels = ["low", "medium", "high", "critical"]
    for i in range(n_incidents):
        trip = random.choice(trips)
        inc_type = random.choices(inc_names, weights=inc_probs, k=1)[0]
        severity = random.choices(
            severity_levels, weights=[0.30, 0.45, 0.20, 0.05], k=1
        )[0]

        resolution_hours = {
            "breakdown": random.uniform(1, 12),
            "flat_tyre": random.uniform(0.5, 2),
            "traffic_block": random.uniform(0.5, 4),
            "weather": random.uniform(1, 8),
            "accident": random.uniform(2, 24),
        }[inc_type]

        inc_time = (trip["actual_start_time"] or NOW) + timedelta(
            hours=random.uniform(0.5, 5)
        )

        incidents.append({
            "id": str(uuid.uuid4()),
            "incident_number": f"INC-2024-{str(i + 1).zfill(5)}",
            "route_id": trip["id"],
            "vehicle_id": trip["vehicle_id"],
            "driver_id": trip["driver_id"],
            "incident_type": inc_type,
            "severity": severity,
            "reported_at": inc_time,
            "resolved_at": inc_time + timedelta(hours=resolution_hours),
            "description": _incident_description(inc_type, severity),
            "status": "resolved",
            "delay_caused_min": int(resolution_hours * 60),
            "city": random.choice(CITIES),
        })

    logger.info("Generated %d trips and %d incidents", len(trips), len(incidents))
    return trips, incidents


def _incident_description(inc_type: str, severity: str) -> str:
    descriptions = {
        "breakdown": [
            "Engine overheating on NH-48 near toll plaza",
            "Fuel pump failure, vehicle stationary on highway shoulder",
            "Brake failure reported, vehicle parked safely",
            "Electrical fault, vehicle unable to restart",
        ],
        "flat_tyre": [
            "Front tyre puncture on NH-44",
            "Rear left tyre blowout on bypass road",
            "Multiple tyre damage from road debris",
        ],
        "traffic_block": [
            "Accident ahead causing 3-hour traffic standstill on NH-48",
            "Road repair work blocking two lanes on SH-60",
            "Protest blocking entry to city, alternate route taken",
        ],
        "weather": [
            "Heavy rainfall causing flooding on low-lying highway section",
            "Dense fog reducing visibility to under 50m on NH",
            "Cyclone warning causing port closure and delay",
        ],
        "accident": [
            "Minor collision with private vehicle at intersection",
            "Vehicle skidded on wet road, minor damage",
            "Loading/unloading area accident",
        ],
    }
    opts = descriptions.get(inc_type, ["Unspecified incident"])
    return random.choice(opts) + f" [severity: {severity}]"


def run_full_seed() -> dict:
    """
    Master function to generate all synthetic data.
    Returns a summary dict.
    """
    logger.info("Starting full synthetic data generation (SEED=%d)", SEED)

    vehicles = generate_vehicles(50)
    drivers = generate_drivers(50, vehicles)
    shipments = generate_shipments(500)
    trips, incidents = generate_trips_and_incidents(vehicles, drivers, 300, 80)

    return {
        "vehicles": vehicles,
        "drivers": drivers,
        "shipments": shipments,
        "trips": trips,
        "incidents": incidents,
        "summary": {
            "seed": SEED,
            "vehicles_count": len(vehicles),
            "drivers_count": len(drivers),
            "shipments_count": len(shipments),
            "trips_count": len(trips),
            "incidents_count": len(incidents),
            "pending_shipments": sum(1 for s in shipments if s["status"] == "pending"),
            "available_vehicles": sum(1 for v in vehicles if v["status"] == "available"),
            "available_drivers": sum(1 for d in drivers if d["status"] == "available"),
        },
    }
