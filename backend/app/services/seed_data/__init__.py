"""
Synthetic data generator for Cargo Pilot.

Generates reproducible demo data with SEED=42.
Data is internally consistent across vehicles, drivers, shipments, and trips.
"""
import random
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import numpy as np

# ── SEED for reproducibility ──────────────────────────────────
SEED = 42
random.seed(SEED)
np.random.seed(SEED)


# ── Indian city coordinates (must match distance_matrix.py) ──
CITIES = [
    "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai",
    "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Lucknow",
    "Nagpur", "Surat",
]

# City-specific address templates
CITY_ADDRESSES = {
    "Mumbai": [
        "Plot 45, MIDC Industrial Area, Andheri East, Mumbai",
        "Warehouse Block C, Bhiwandi Logistics Park, Thane",
        "Unit 12, Navi Mumbai APMC, Vashi",
        "Industrial Zone, Dharavi, Mumbai",
        "Gate 7, Kalamboli Freight Station, Navi Mumbai",
    ],
    "Delhi": [
        "A-45, Okhla Industrial Area Phase 2, New Delhi",
        "Plot 78, Patparganj Industrial Estate, Delhi",
        "Warehouse No 3, Loni Industrial Area, Ghaziabad",
        "Sector 5, IMT Manesar, Gurugram",
        "Bay 22, CONCOR ICD Tughlakabad, Delhi",
    ],
    "Bangalore": [
        "Plot 34, Peenya Industrial Area, Bangalore",
        "Unit 5A, Electronics City Phase 1, Bangalore",
        "Warehouse 7, Whitefield Industrial Area, Bangalore",
        "Plot 12, Bommasandra Industrial Area, Bangalore",
        "Shed 9, Nelamangala Logistics Hub, Bangalore",
    ],
    "Hyderabad": [
        "Plot 67, APIIC Industrial Park, Nacharam, Hyderabad",
        "Unit 3, IDA Jeedimetla, Hyderabad",
        "Warehouse B2, Patancheru Industrial Area, Hyderabad",
        "Plot 23, Fab City, Shamshabad, Hyderabad",
        "Shed 4, Kothur Logistics Park, Hyderabad",
    ],
    "Chennai": [
        "Plot 15, SIPCOT Industrial Complex, Hosur Road, Chennai",
        "Unit 7, Ambattur Industrial Estate, Chennai",
        "Warehouse C, Sriperumbudur SEZ, Chennai",
        "Plot 89, MEPZ, Tambaram, Chennai",
        "Bay 3, Chennai Port Container Freight Station",
    ],
    "Kolkata": [
        "Plot 22, Dankuni Industrial Complex, Howrah",
        "Unit 5, Bantala Leather Complex, Kolkata",
        "Warehouse 8, Uluberia Industrial Growth Centre",
        "Plot 44, Falta SEZ, South 24 Parganas",
        "Bay 12, CONCOR ICD Dankuni, Hooghly",
    ],
    "Pune": [
        "Plot 34, Bhosari MIDC, Pune",
        "Unit 12, Chakan Industrial Area, Pune",
        "Warehouse 5, Ranjangaon MIDC, Pune",
        "Plot 78, Hinjewadi Phase 3, Pune",
        "Bay 4, Talegaon MIDC, Pune",
    ],
    "Ahmedabad": [
        "Plot 23, GIDC Vatva Industrial Estate, Ahmedabad",
        "Unit 8, Naroda Industrial Estate, Ahmedabad",
        "Warehouse 12, Sanand GIDC, Ahmedabad",
        "Plot 45, Odhav Industrial Area, Ahmedabad",
        "Bay 6, Kandla SEZ Logistics Park, Ahmedabad",
    ],
    "Jaipur": [
        "Plot 56, Sitapura Industrial Area, Jaipur",
        "Unit 3, Mansarovar Industrial Zone, Jaipur",
        "Warehouse 7, Bindayaka Industrial Area, Jaipur",
        "Plot 89, RIICO Industrial Area, Bhiwadi, Alwar",
        "Bay 2, Mahindra World City, Jaipur",
    ],
    "Lucknow": [
        "Plot 34, Amausi Industrial Area, Lucknow",
        "Unit 8, Kanpur Road Industrial Zone, Lucknow",
        "Warehouse 5, Trans-Gomti Industrial Area, Lucknow",
        "Plot 12, Sarojini Nagar Industrial Area, Lucknow",
        "Bay 3, UPSIDA Industrial Area, Lucknow",
    ],
    "Nagpur": [
        "Plot 67, MIDC Butibori Industrial Area, Nagpur",
        "Unit 5, Hingna Industrial Zone, Nagpur",
        "Warehouse 9, MIHAN SEZ, Nagpur",
        "Plot 23, Amravati Road Industrial Area, Nagpur",
        "Bay 7, Nagpur Logistics Hub, Wardha Road",
    ],
    "Surat": [
        "Plot 45, GIDC Sachin Industrial Estate, Surat",
        "Unit 12, Kim GIDC, Surat",
        "Warehouse 6, Hazira Industrial Zone, Surat",
        "Plot 78, Pandesara Industrial Estate, Surat",
        "Bay 5, Magdalla Port Freight Station, Surat",
    ],
}

# City coordinates for shipment generation
CITY_COORDS = {
    "Mumbai":    (19.0760, 72.8777),
    "Delhi":     (28.7041, 77.1025),
    "Bangalore": (12.9716, 77.5946),
    "Hyderabad": (17.3850, 78.4867),
    "Chennai":   (13.0827, 80.2707),
    "Kolkata":   (22.5726, 88.3639),
    "Pune":      (18.5204, 73.8567),
    "Ahmedabad": (23.0225, 72.5714),
    "Jaipur":    (26.9124, 75.7873),
    "Lucknow":   (26.8467, 80.9462),
    "Nagpur":    (21.1458, 79.0882),
    "Surat":     (21.1702, 72.8311),
}

# Indian goods types with realistic weight distributions
GOODS_TYPES = [
    ("FMCG", 0.35),
    ("Automotive", 0.18),
    ("Pharmaceutical", 0.12),
    ("Electronics", 0.10),
    ("Textiles", 0.10),
    ("Chemicals", 0.07),
    ("Perishables", 0.05),
    ("Machinery", 0.03),
]
GOODS_NAMES = [g[0] for g in GOODS_TYPES]
GOODS_WEIGHTS_PROB = [g[1] for g in GOODS_TYPES]

# Indian vehicle makes and models
VEHICLE_SPECS = {
    "mini_truck": {
        "makes": ["Tata", "Mahindra", "Bajaj"],
        "models": {"Tata": "Ace", "Mahindra": "Jeeto", "Bajaj": "Maxima"},
        "capacity_kg": 750,
        "volume_m3": 5.0,
        "efficiency_kmpl": (7.5, 9.0),   # min, max
        "tank_l": 40,
    },
    "tempo": {
        "makes": ["Tata", "Mahindra", "Eicher"],
        "models": {"Tata": "407", "Mahindra": "Bolero Pickup", "Eicher": "Pro 1049"},
        "capacity_kg": 2500,
        "volume_m3": 12.0,
        "efficiency_kmpl": (6.0, 8.0),
        "tank_l": 60,
    },
    "medium_truck": {
        "makes": ["Tata", "Eicher", "Ashok Leyland"],
        "models": {"Tata": "1109", "Eicher": "Pro 3015", "Ashok Leyland": "Dost+"},
        "capacity_kg": 7500,
        "volume_m3": 30.0,
        "efficiency_kmpl": (4.5, 6.0),
        "tank_l": 100,
    },
    "large_truck": {
        "makes": ["Tata", "Ashok Leyland", "Bharat Benz"],
        "models": {"Tata": "2518", "Ashok Leyland": "2523", "Bharat Benz": "2523R"},
        "capacity_kg": 15000,
        "volume_m3": 55.0,
        "efficiency_kmpl": (3.8, 5.0),
        "tank_l": 200,
    },
    "trailer": {
        "makes": ["Volvo", "Scania", "Tata"],
        "models": {"Volvo": "FH", "Scania": "R500", "Tata": "Prima 4940"},
        "capacity_kg": 25000,
        "volume_m3": 90.0,
        "efficiency_kmpl": (3.0, 4.0),
        "tank_l": 400,
    },
}

# Indian registration number format: state-code + district + alpha + number
STATE_CODES = {
    "Mumbai": "MH12", "Delhi": "DL8C", "Bangalore": "KA05",
    "Hyderabad": "TS09", "Chennai": "TN01", "Kolkata": "WB06",
    "Pune": "MH14", "Ahmedabad": "GJ01", "Jaipur": "RJ14",
    "Lucknow": "UP32", "Nagpur": "MH31", "Surat": "GJ05",
}


def generate_registration(city: str, seq: int) -> str:
    """Generate a realistic Indian vehicle registration number."""
    prefix = STATE_CODES.get(city, "MH12")
    alpha = chr(ord("A") + (seq // 10) % 26) + chr(ord("A") + seq % 26)
    number = str(1000 + seq).zfill(4)
    return f"{prefix}{alpha}{number}"
