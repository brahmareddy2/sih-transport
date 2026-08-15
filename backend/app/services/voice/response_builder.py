"""
Response Builder — Phase 8
Constructs multilingual voice responses with TTS text, visual card payloads,
and confirmation dialog prompts.
"""
from typing import Any, Dict, List, Optional
from app.services.voice.language_service import get_language_service


class VoiceResponseBuilder:
    """Formats structured voice responses with visual cards and speech synthesis text."""

    def __init__(self):
        self.lang_service = get_language_service()

    def build_confirmation_prompt(
        self,
        intent: str,
        entities: Dict[str, Any],
        language: str = "en",
    ) -> Dict[str, Any]:
        """Generate confirmation question before executing sensitive intent."""
        if intent == "PLAN_TRIP":
            origin = entities.get("origin", "Delhi")
            destination = entities.get("destination", "Hyderabad")
            text = self.lang_service.translate(
                "plan_trip_confirm",
                lang=language,
                origin=origin,
                destination=destination,
            )
            return {
                "text": text,
                "speech_text": text,
                "requires_confirmation": True,
                "confirmation_type": "PLAN_TRIP",
                "action_payload": {"origin": origin, "destination": destination},
                "options": [
                    {"label": self.lang_service.translate("yes", lang=language), "value": True, "accent": "#10b981"},
                    {"label": self.lang_service.translate("no", lang=language), "value": False, "accent": "#ef4444"},
                ],
            }

        elif intent in ["REPORT_BREAKDOWN", "REPORT_TYRE_PUNCTURE"]:
            veh = entities.get("vehicle_registration", "Your Vehicle")
            text = f"Confirm reporting {intent.replace('_', ' ').lower()} for {veh}?"
            return {
                "text": text,
                "speech_text": text,
                "requires_confirmation": True,
                "confirmation_type": intent,
                "action_payload": entities,
                "options": [
                    {"label": self.lang_service.translate("yes", lang=language), "value": True, "accent": "#10b981"},
                    {"label": self.lang_service.translate("no", lang=language), "value": False, "accent": "#ef4444"},
                ],
            }

        text = self.lang_service.translate("is_this_correct", lang=language)
        return {
            "text": text,
            "speech_text": text,
            "requires_confirmation": True,
            "confirmation_type": intent,
            "action_payload": entities,
            "options": [
                {"label": self.lang_service.translate("yes", lang=language), "value": True, "accent": "#10b981"},
                {"label": self.lang_service.translate("no", lang=language), "value": False, "accent": "#ef4444"},
            ],
        }

    def build_trip_response(
        self,
        trip_data: Dict[str, Any],
        language: str = "en",
    ) -> Dict[str, Any]:
        """Build visual trip card and spoken summary."""
        origin = trip_data.get("origin", "Delhi")
        destination = trip_data.get("destination", "Hyderabad")
        distance_km = trip_data.get("distance_km", 1580.0)
        hours = trip_data.get("driving_hours", 26.5)
        days = trip_data.get("estimated_days", 2)
        fuel_litres = trip_data.get("fuel_litres", 395.0)
        fuel_cost = trip_data.get("fuel_cost_inr", 36735)
        toll_cost = trip_data.get("toll_cost_inr", 2850)
        total_cost = trip_data.get("total_cost_inr", 43500)

        speech_text = self.lang_service.translate(
            "trip_calculated_summary",
            lang=language,
            origin=origin,
            destination=destination,
            distance_km=int(distance_km),
            hours=round(hours, 1),
            days=days,
            fuel_litres=int(fuel_litres),
            fuel_cost=f"{fuel_cost:,}",
            toll_cost=f"{toll_cost:,}",
            total_cost=f"{total_cost:,}",
        )

        return {
            "text": speech_text,
            "speech_text": speech_text,
            "language": language,
            "requires_confirmation": False,
            "card_type": "TRIP_RESULT",
            "card_data": {
                "title": f"{origin.upper()} ➔ {destination.upper()}",
                "origin": origin,
                "destination": destination,
                "distance_km": distance_km,
                "driving_hours": hours,
                "estimated_days": days,
                "fuel_litres": fuel_litres,
                "fuel_cost_inr": fuel_cost,
                "toll_cost_inr": toll_cost,
                "total_cost_inr": total_cost,
                "route_path": trip_data.get("route_path", []),
                "fuel_stations": trip_data.get("fuel_stations", []),
                "stops": [origin, "Nagpur Gateway Hub", destination] if "Nagpur" not in [origin, destination] else [origin, destination],
            },
        }

    def build_eta_response(
        self,
        vehicle: str,
        destination: str,
        eta_minutes: int,
        delay_minutes: int = 0,
        language: str = "en",
    ) -> Dict[str, Any]:
        """Build ETA status response."""
        hours = round(eta_minutes / 60.0, 1)
        eta_time = f"{int(hours)}h {eta_minutes % 60}m"
        text = self.lang_service.translate(
            "eta_response",
            lang=language,
            vehicle=vehicle,
            destination=destination,
            hours=hours,
            eta_time=eta_time,
        )

        if delay_minutes > 0:
            delay_h = round(delay_minutes / 60.0, 1)
            warning = self.lang_service.translate("delay_warning", lang=language, delay_hours=delay_h)
            text = f"{text} {warning}"

        return {
            "text": text,
            "speech_text": text,
            "language": language,
            "requires_confirmation": False,
            "card_type": "ETA_STATUS",
            "card_data": {
                "vehicle": vehicle,
                "destination": destination,
                "eta_minutes": eta_minutes,
                "delay_minutes": delay_minutes,
            },
        }

    def build_fuel_response(
        self,
        fuel_litres: float,
        fuel_pct: float,
        range_km: float,
        language: str = "en",
    ) -> Dict[str, Any]:
        """Build fuel telemetry status response."""
        if fuel_pct < 15.0:
            text = self.lang_service.translate("low_fuel_alert", lang=language, fuel_pct=int(fuel_pct))
            return {
                "text": text,
                "speech_text": text,
                "language": language,
                "requires_confirmation": True,
                "confirmation_type": "FIND_FUEL_STATION",
                "card_type": "LOW_FUEL_ALERT",
                "card_data": {"fuel_litres": fuel_litres, "fuel_pct": fuel_pct, "range_km": range_km},
                "options": [
                    {"label": self.lang_service.translate("yes", lang=language), "value": True, "accent": "#10b981"},
                    {"label": self.lang_service.translate("no", lang=language), "value": False, "accent": "#ef4444"},
                ],
            }

        text = self.lang_service.translate(
            "fuel_status",
            lang=language,
            fuel_litres=int(fuel_litres),
            fuel_pct=int(fuel_pct),
            range_km=int(range_km),
        )
        return {
            "text": text,
            "speech_text": text,
            "language": language,
            "requires_confirmation": False,
            "card_type": "FUEL_STATUS",
            "card_data": {"fuel_litres": fuel_litres, "fuel_pct": fuel_pct, "range_km": range_km},
        }

    def build_breakdown_response(
        self,
        vehicle: str,
        location: str,
        plans: List[Dict[str, Any]],
        language: str = "en",
    ) -> Dict[str, Any]:
        """Build breakdown recovery options response."""
        text = self.lang_service.translate(
            "breakdown_help",
            lang=language,
            vehicle=vehicle,
            location=location,
            plan_count=len(plans),
        )
        return {
            "text": text,
            "speech_text": text,
            "language": language,
            "requires_confirmation": False,
            "card_type": "BREAKDOWN_RECOVERY",
            "card_data": {
                "vehicle": vehicle,
                "location": location,
                "plans": plans,
            },
        }

    def build_return_cargo_response(
        self,
        destination: str,
        matches: List[Dict[str, Any]],
        language: str = "en",
    ) -> Dict[str, Any]:
        """Build return cargo matching response."""
        top_match = matches[0] if matches else {}
        km_saved = top_match.get("empty_km_saved", 145.0)
        benefit = top_match.get("cost_saving_inr", 4850)

        text = self.lang_service.translate(
            "return_cargo_found",
            lang=language,
            destination=destination,
            count=len(matches),
            km_saved=int(km_saved),
            benefit=f"{benefit:,}",
        )
        return {
            "text": text,
            "speech_text": text,
            "language": language,
            "requires_confirmation": False,
            "card_type": "RETURN_CARGO_MATCHES",
            "card_data": {
                "destination": destination,
                "matches": matches,
            },
        }
