"""
Owner & Fleet Manager Assistant — Phase 8
Provides conversational financial analytics, vehicle telemetry tracking,
fleet profit KPIs, fuel consumption breakdown, and maintenance alerts.
"""
from typing import Any, Dict, List, Optional
from app.services.voice.language_service import get_language_service


class OwnerAssistant:
    """Handles owner/fleet manager financial queries, vehicle performance rankings, and telemetry."""

    def __init__(self):
        self.lang_service = get_language_service()

    def get_fleet_locations(self, language: str = "en") -> Dict[str, Any]:
        """Return real-time vehicle locations and active trip statuses."""
        text = "Your fleet consists of 50 vehicles across India: 12 in active transit, 38 idle/ready at staging hubs."
        return {
            "text": text,
            "speech_text": text,
            "language": language,
            "card_type": "OWNER_FLEET_LOCATIONS",
            "card_data": {
                "total_vehicles": 50,
                "active_in_transit": 12,
                "idle_available": 38,
                "top_locations": [
                    {"city": "Mumbai", "count": 14, "lat": 19.0760, "lon": 72.8777},
                    {"city": "Delhi", "count": 12, "lat": 28.6139, "lon": 77.2090},
                    {"city": "Hyderabad", "count": 10, "lat": 17.3850, "lon": 78.4867},
                    {"city": "Bengaluru", "count": 8, "lat": 12.9716, "lon": 77.5946},
                    {"city": "Nagpur Hub", "count": 6, "lat": 21.1458, "lon": 79.0882},
                ],
            },
        }

    def get_daily_financial_analytics(self, language: str = "en") -> Dict[str, Any]:
        """Return daily financial breakdown: Revenue, Fuel, Tolls, Food, Maintenance, Estimated Profit."""
        revenue_inr = 345000
        fuel_inr = 112400
        tolls_inr = 24800
        food_inr = 4500   # Driver batta / meals allowance
        maintenance_inr = 8500
        total_expense_inr = fuel_inr + tolls_inr + food_inr + maintenance_inr
        estimated_profit_inr = revenue_inr - total_expense_inr

        text = (
            f"Today's Fleet Financials (Estimated): Total Revenue ₹{revenue_inr:,}, "
            f"Expenses ₹{total_expense_inr:,} (Fuel: ₹{fuel_inr:,}, Tolls: ₹{tolls_inr:,}, Driver Batta/Food: ₹{food_inr:,}, Maintenance: ₹{maintenance_inr:,}). "
            f"Estimated Net Profit: ₹{estimated_profit_inr:,}."
        )

        return {
            "text": text,
            "speech_text": f"Today's estimated revenue is ₹{revenue_inr:,}, total expenses are ₹{total_expense_inr:,}, and estimated profit is ₹{estimated_profit_inr:,}.",
            "language": language,
            "card_type": "OWNER_FINANCIAL_SUMMARY",
            "card_data": {
                "title": "📊 Today's Fleet Financial Performance (Estimated)",
                "date": "Today",
                "revenue_inr": revenue_inr,
                "expenses": {
                    "fuel_inr": fuel_inr,
                    "tolls_inr": tolls_inr,
                    "food_batta_inr": food_inr,
                    "maintenance_inr": maintenance_inr,
                    "total_expense_inr": total_expense_inr,
                },
                "estimated_profit_inr": estimated_profit_inr,
                "profit_margin_pct": round((estimated_profit_inr / revenue_inr) * 100, 1),
                "diesel_consumed_litres": 1208.0,
                "empty_km_savings_inr": 34800,
            },
        }

    def get_vehicle_rankings(self, ranking_type: str = "profit", language: str = "en") -> Dict[str, Any]:
        """Rank vehicles by profit, fuel consumption, delays, or maintenance need."""
        if "fuel" in ranking_type.lower():
            text = "Vehicle MH02AB1234 has the highest fuel consumption today (380 litres across 1,420 km)."
            rankings = [
                {"rank": 1, "vehicle": "MH02AB1234", "metric": "380 Litres (4.1 km/L)", "status": "In Transit"},
                {"rank": 2, "vehicle": "DL01CD5678", "metric": "290 Litres (4.4 km/L)", "status": "In Transit"},
                {"rank": 3, "vehicle": "TN07GH3456", "metric": "240 Litres (3.8 km/L)", "status": "Low Fuel Warning"},
            ]
        else:
            text = "Vehicle KA04EF9012 generated the highest net profit today (₹48,200 with backhaul load)."
            rankings = [
                {"rank": 1, "vehicle": "KA04EF9012", "metric": "₹48,200 Net Profit", "status": "Delivered + Return Load"},
                {"rank": 2, "vehicle": "MH02AB1234", "metric": "₹39,500 Net Profit", "status": "In Transit"},
                {"rank": 3, "vehicle": "GJ01XY7890", "metric": "₹31,000 Net Profit", "status": "Idle / Available"},
            ]

        return {
            "text": text,
            "speech_text": text,
            "language": language,
            "card_type": "VEHICLE_RANKINGS",
            "card_data": {
                "ranking_type": ranking_type,
                "title": f"🏆 Fleet Performance Ranking ({ranking_type.capitalize()})",
                "rankings": rankings,
            },
        }
