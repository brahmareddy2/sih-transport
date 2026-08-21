"""
Driver Assistant Service — Phase 8
Provides conversational intelligence for drivers:
- Trip planning & estimations (Delhi -> Hyderabad)
- Live trip progress & ETA
- Highway facilities search: Restaurants 🍛, Free Parking 🅿️, Clean Restrooms 🚻, Fuel Stations ⛽, Puncture Shops ⚙️
- Puncture & Emergency Breakdown assistance with safe calling hooks.
"""
from typing import Any, Dict, List, Optional
from app.services.voice.language_service import get_language_service
from app.services.optimization.distance_matrix import (
    INDIAN_CITIES,
    city_distance_km,
    travel_time_minutes,
    TOLL_RATE_INR_PER_KM,
    NH_FRACTION,
)
from app.services.optimization.cost_calculator import calculate_route_cost
from app.services.voice.communication import get_communication_service

# Highway facilities dataset for Indian freight corridors (NH44, NH48, NH16, NH27)
HIGHWAY_FACILITIES = {
    "restaurants": [
        {
            "id": "rest-1",
            "name": "Shiva Dhaba & Family Restaurant",
            "highway": "NH48 (Delhi-Jaipur Express Highway)",
            "distance_km": 4.2,
            "detour_min": 5,
            "cuisine": "North Indian / Pure Veg & Non-Veg Dhaba",
            "avg_cost_inr": 180,
            "rating": 4.6,
            "amenities": ["Truck Parking", "Clean Restrooms", "24/7 Chai"],
            "phone": "+91 98765 11223",
            "status": "OPEN",
        },
        {
            "id": "rest-2",
            "name": "Grand Highway Food Plaza (Nagpur Hub)",
            "highway": "NH44 North-South Corridor",
            "distance_km": 12.0,
            "detour_min": 8,
            "cuisine": "Multi-Cuisine / South & North Indian Thali",
            "avg_cost_inr": 220,
            "rating": 4.8,
            "amenities": ["Air Conditioned", "CCTV Truck Bay", "Clean Toilets"],
            "phone": "+91 94230 44556",
            "status": "OPEN",
        },
    ],
    "parking": [
        {
            "id": "park-1",
            "name": "NHAI Highway Truck Layby & Rest Bay",
            "highway": "NH48 Mile 78",
            "distance_km": 3.5,
            "detour_min": 2,
            "type": "Secure Heavy Vehicle Parking",
            "fee": "Free Parking",
            "capacity": "60 Trucks",
            "security": "24/7 Security & High-Mast Lighting",
            "rating": 4.5,
        },
        {
            "id": "park-2",
            "name": "Kisan Logistics Truck Terminal & Staging Bay",
            "highway": "NH44 Nagpur Ring Road",
            "distance_km": 8.0,
            "detour_min": 6,
            "type": "Gated Staging Yard",
            "fee": "₹50 / overnight",
            "capacity": "120 Trucks",
            "security": "Gated with CCTV & Guard",
            "rating": 4.7,
        },
    ],
    "restrooms": [
        {
            "id": "wc-1",
            "name": "NHAI Swachh Highway Plaza Restrooms",
            "highway": "NH48 Mile 45",
            "distance_km": 2.1,
            "detour_min": 2,
            "cleanliness_score": "5/5 Star Clean",
            "amenities": ["Running Water", "Western & Indian Toilets", "Hot Showers"],
            "fee": "Free / Public NHAI Facility",
        },
        {
            "id": "wc-2",
            "name": "BPCL Coco Highway Comfort Station",
            "highway": "NH44 Mile 180",
            "distance_km": 6.8,
            "detour_min": 4,
            "cleanliness_score": "4.8/5 Star",
            "amenities": ["Clean Restrooms", "Driver Bathrooms", "Drinking Water"],
            "fee": "Free for Drivers",
        },
    ],
    "fuel_stations": [
        {
            "id": "fuel-1",
            "name": "Indian Oil Highway Bunkering Plaza",
            "highway": "NH48 Express Mile 120",
            "distance_km": 5.4,
            "detour_min": 4,
            "diesel_price_inr": 93.0,
            "amenities": ["24/7 High-Speed Diesel", "DEF AdBlue", "Air Tower", "Driver Rest Stop"],
        },
        {
            "id": "fuel-2",
            "name": "BPCL Coco Bunkering Hub (Nagpur)",
            "highway": "NH44 Corridor",
            "distance_km": 14.5,
            "detour_min": 7,
            "diesel_price_inr": 92.5,
            "amenities": ["High-Flow Bunkering", "Truck Wash", "Driver Dormitory"],
        },
    ],
    "puncture_shops": [
        {
            "id": "punc-1",
            "name": "XYZ Highway Tubeless Tyre & Radial Care",
            "highway": "NH48 Mile 64 (Near Lonavala)",
            "distance_km": 2.4,
            "eta_minutes": 7,
            "services": ["Tubeless Puncture", "Radial Patching", "Wheel Balancing", "Nitrogen"],
            "phone": "+91 98765 44210",
            "price_note": "Price depends on puncture type (Ask provider)",
            "status": "24/7 OPEN",
        },
        {
            "id": "punc-2",
            "name": "Om Sai Highway Tyre Service",
            "highway": "NH44 North-South Corridor",
            "distance_km": 6.1,
            "eta_minutes": 12,
            "services": ["Heavy Truck Tyre Retreading", "Mobile Puncture Van", "Air Top-up"],
            "phone": "+91 94230 18832",
            "price_note": "Standard NHAI roadside rates",
            "status": "OPEN",
        },
    ],
}


class DriverAssistant:
    """Handles driver conversational queries, trip estimates, and highway amenities."""

    def __init__(self):
        self.lang_service = get_language_service()
        self.comm_service = get_communication_service()

    def plan_driver_trip(self, origin: str, destination: str, current_fuel_l: float = 180.0, language: str = "en") -> Dict[str, Any]:
        """Calculate trip route, distance, travel time, fuel requirements, and toll estimate."""
        orig = origin or "Delhi"
        dest = destination or "Hyderabad"

        from app.services.assistant.location_provider import get_location_provider
        provider = get_location_provider()
        corridor = provider.get_corridor_data(orig, dest)

        dist_km = corridor.get("total_distance_km", 1200.0)
        time_hours = corridor.get("driving_hours", 20.0)
        tolls_list = corridor.get("toll_plazas", [])
        toll_inr = sum(t.get("cost_inr", 0) for t in tolls_list) if tolls_list else (dist_km * NH_FRACTION * 3.0)

        # Extract midway stop from corridor major stops
        major_stops = corridor.get("major_stops", [])
        midpoint_name = "Highway Midway"
        if len(major_stops) > 2:
            midpoint_name = major_stops[len(major_stops) // 2].get("city", "Highway Midway")
        elif major_stops:
            midpoint_name = major_stops[-1].get("city", "Highway Midway")

        estimated_days = max(1, int(round(time_hours / 12.0)))
        cost_res = calculate_route_cost(
            total_distance_km=dist_km,
            empty_distance_km=0.0,
            fuel_efficiency_kmpl=4.0,
            fuel_type="diesel",
            vehicle_type="heavy_truck",
            travel_hours=time_hours,
            num_days=estimated_days,
        )

        fuel_req_l = round(cost_res.fuel_litres, 1)
        fuel_cost_inr = int(round(cost_res.fuel_cost_inr))
        total_cost_inr = int(round(cost_res.total_cost_inr))

        speech_text = self.lang_service.translate(
            "trip_calculated_summary",
            lang=language,
            origin=orig,
            destination=dest,
            distance_km=int(dist_km),
            hours=round(time_hours, 1),
            days=estimated_days,
            fuel_litres=int(fuel_req_l),
            fuel_cost=f"{fuel_cost_inr:,}",
            toll_cost=f"{int(toll_inr):,}",
            total_cost=f"{total_cost_inr:,}",
        )

        return {
            "text": speech_text,
            "speech_text": speech_text,
            "language": language,
            "requires_confirmation": True,
            "confirmation_type": "START_TRIP",
            "action_payload": {"origin": orig, "destination": dest},
            "card_type": "DRIVER_TRIP_CARD",
            "card_data": {
                "title": f"{orig.upper()} ➔ {dest.upper()}",
                "origin": orig,
                "destination": dest,
                "corridor_name": corridor.get("corridor_name"),
                "distance_km": round(dist_km, 1),
                "driving_hours": round(time_hours, 1),
                "estimated_days": estimated_days,
                "current_fuel_litres": current_fuel_l,
                "fuel_required_litres": fuel_req_l,
                "fuel_cost_inr": fuel_cost_inr,
                "toll_cost_inr": int(toll_inr),
                "total_cost_inr": total_cost_inr,
                "toll_plazas": tolls_list,
                "coordinates": corridor.get("coordinates", []),
                "parking": corridor.get("parking", []),
                "restrooms": corridor.get("restrooms", []),
                "recommended_stops": [
                    {"name": f"Origin Hub ({orig})", "type": "Start"},
                    {"name": f"{midpoint_name} Highway Gateway", "type": "Midpoint Rest & Food"},
                    {"name": f"Destination Hub ({dest})", "type": "Delivery"},
                ],
            },
            "options": [
                {"label": "▶️ START TRIP", "value": True, "accent": "#10b981"},
                {"label": "🔄 CHANGE ROUTE", "value": False, "accent": "#6366f1"},
            ],
        }

    def get_trip_progress(self, language: str = "en") -> Dict[str, Any]:
        """Return active driving progress and remaining telematics."""
        text = "Your trip from Delhi to Hyderabad is active. You are near Nagpur with 790 km remaining (ETA: Tomorrow 06:30 AM). Available fuel: 140L."
        return {
            "text": text,
            "speech_text": text,
            "language": language,
            "card_type": "TRIP_PROGRESS",
            "card_data": {
                "origin": "Delhi",
                "destination": "Hyderabad",
                "current_location": "Nagpur Bypass (Mile 790)",
                "remaining_distance_km": 790.0,
                "eta_hours": 12.5,
                "eta_time": "Tomorrow 06:30 AM",
                "remaining_fuel_litres": 140.0,
                "fuel_pct": 68.0,
                "speed_kmh": 58.0,
                "next_stop": "Grand Highway Food Plaza (12 km away)",
            },
        }

    def search_facilities(self, facility_type: str, language: str = "en") -> Dict[str, Any]:
        """Search nearby restaurants, parking, restrooms, fuel, or puncture shops."""
        key = facility_type.lower()
        items = HIGHWAY_FACILITIES.get(key, HIGHWAY_FACILITIES["restaurants"])
        title_map = {
            "restaurants": "🍛 Nearby Highway Food & Dhabas",
            "parking": "🅿️ Free Highway Truck Parking",
            "restrooms": "🚻 Clean Restrooms & Showers",
            "fuel_stations": "⛽ Highway Diesel & Fuel Bunkers",
            "puncture_shops": "⚙️ 24/7 Tyre & Puncture Shops",
        }
        title = title_map.get(key, "Highway Amenities")

        return {
            "text": f"Found {len(items)} {key.replace('_', ' ')} near your current route.",
            "speech_text": f"Found {len(items)} {key.replace('_', ' ')} on your route.",
            "language": language,
            "card_type": "FACILITIES_LIST",
            "card_data": {
                "category": key,
                "title": title,
                "facilities": items,
            },
        }

    def get_puncture_assistance(self, language: str = "en") -> Dict[str, Any]:
        """Puncture & breakdown response with nearest repair shops, call, navigate, and incident creation."""
        shops = HIGHWAY_FACILITIES["puncture_shops"]
        nearest = shops[0]

        text = f"Puncture assistance: Nearest service is {nearest['name']}, {nearest['distance_km']} km away (ETA: {nearest['eta_minutes']} min). Phone: {nearest['phone']}."
        return {
            "text": text,
            "speech_text": text,
            "language": language,
            "card_type": "PUNCTURE_ASSISTANCE",
            "card_data": {
                "title": "⚙️ Puncture & Tyre Emergency Assistance",
                "nearest_shop": nearest,
                "all_shops": shops,
                "action_buttons": [
                    {"label": "📞 CALL SHOP", "action": "CALL_PUNCTURE_SHOP", "phone": nearest["phone"]},
                    {"label": "📍 NAVIGATE", "action": "NAVIGATE_SHOP"},
                    {"label": "🚨 CREATE INCIDENT", "action": "CREATE_INCIDENT"},
                ],
            },
        }
