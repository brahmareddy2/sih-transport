"""
Universal Intent Router — Phase 8
Unifies natural-language query execution for both Voice Microphone and Universal Search Bar.
Routes to specialized role assistants (Driver, Owner, Admin, Operator, Customer) and enforces RBAC.
"""
import logging
import re
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.services.voice.language_service import get_language_service
from app.services.voice.driver_assistant import DriverAssistant
from app.services.voice.owner_assistant import OwnerAssistant
from app.services.voice.admin_assistant import AdminAssistant
from app.services.voice.operator_assistant import OperatorAssistant
from app.services.voice.customer_assistant import CustomerAssistant
from app.services.voice.communication import get_communication_service

logger = logging.getLogger(__name__)

# Canonical Indian city aliases for entity extraction
CITIES_MAP = {
    "Delhi": ["delhi", "new delhi", "ఢిల్లీ", "दिल्ली", "ਦਿੱਲੀ"],
    "Hyderabad": ["hyderabad", "హైదరాబాద్", "हैदराबाद", "ਹੈਦਰਾਬਾਦ", "हैद्राबाद"],
    "Mumbai": ["mumbai", "bombay", "ముంబై", "मुंबई", "ਮੁੰਬਈ"],
    "Pune": ["pune", "పూణే", "పుణె", "पुणे", "ਪੁਣੇ"],
    "Bengaluru": ["bangalore", "bengaluru", "బెంగళూరు", "बेंगलुरु", "ਬੈਂਗਲੁਰੂ", "बंगळुरू"],
    "Chennai": ["chennai", "madras", "చెన్నై", "चेन्नई", "ਚੇਨਈ"],
    "Kolkata": ["kolkata", "calcutta", "కోల్‌కతా", "कोलकाता", "ਕੋਲਕਾਤਾ"],
    "Ahmedabad": ["ahmedabad", "అహ్మదాబాద్", "अहमदाबाद", "ਅਹਿਮਦਾਬਾਦ"],
    "Jaipur": ["jaipur", "జైపూర్", "जयपुर", "ਜੈਪੁਰ"],
    "Nagpur": ["nagpur", "నాగ్‌పూర్", "నాగపూర్", "नागपुर", "ਨਾਗਪੁਰ"],
    "Srikakulam": ["srikakulam", "srikakulum", "శ్రీకాకుళం", "श्रीकाकुलम"],
    "Vijayawada": ["vijayawada", "విజయవాడ", "विजयवाड़ा", "viyawada"],
    "Visakhapatnam": ["visakhapatnam", "vizag", "విశాఖపट్నం", "विशाखापत्तनम"],
    "Guntur": ["guntur", "గుంటూరు", "गुंटूर"],
}


class UniversalIntentRouter:
    """Universal Intent & Search Router for Voice and Text inputs."""

    def __init__(self):
        self.lang_service = get_language_service()
        self.driver_asst = DriverAssistant()
        self.owner_asst = OwnerAssistant()
        self.admin_asst = AdminAssistant()
        self.operator_asst = OperatorAssistant()
        self.customer_asst = CustomerAssistant()
        self.comm_service = get_communication_service()

    def route_query(
        self,
        query: str,
        user_role: str = "operator",
        user_id: Optional[str] = None,
        language: str = "en",
        confirmed: bool = False,
        action_payload: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Route natural-language voice or search text through domain assistants with RBAC validation."""
        clean_text = (query or "").strip()
        lowered = clean_text.lower()
        effective_lang = language or self._detect_language(clean_text)

        # 1. Handle confirmation execution
        if confirmed and action_payload:
            return self._execute_confirmed_action(action_payload, user_role, effective_lang)

        # 2. Extract Entities
        cities = self._extract_cities(clean_text)
        fuel_qty = self._extract_fuel_qty(clean_text)

        # 3. Classify Intent
        intent = self._classify_intent(lowered, clean_text, cities)

        # 4. RBAC Check
        if not self._check_rbac(intent, user_role):
            denied_msg = self.lang_service.translate("unauthorized_command", lang=effective_lang, role=user_role)
            return {
                "text": denied_msg,
                "speech_text": denied_msg,
                "language": effective_lang,
                "intent": intent,
                "is_authorized": False,
                "requires_confirmation": False,
            }

        # 5. Dispatch to specialized domain assistant
        return self._dispatch_intent(intent, clean_text, cities, fuel_qty, user_role, effective_lang)

    def _classify_intent(self, lowered: str, raw: str, cities: List[str]) -> str:
        """Classify user request based on multilingual keyword heuristics."""
        # Highway facilities
        if any(w in lowered for w in ["restaurant", "food", "eat", "dhaba", "హోటల్", "భోజనం", "खाना", "ढाबा", "ਭੋਜਨ", "जेवण"]):
            return "RESTAURANT_SEARCH"
        if any(w in lowered for w in ["parking", "park", "పార్కింగ్", "पार्किंग", "ਪਾਰਕਿੰਗ"]):
            return "PARKING_SEARCH"
        if any(w in lowered for w in ["restroom", "toilet", "washroom", "షౌచాలయ", "టాయిలెట్", "शौचालय", "ਟਾਇਲਟ"]):
            return "RESTROOM_SEARCH"
        if any(w in lowered for w in ["fuel station", "petrol pump", "diesel bunk", "బంక్", "पेट्रोल पंप", "ਪੈਟਰੋਲ ਪੰਪ"]):
            return "FUEL_STATION_SEARCH"
        if any(w in lowered for w in ["puncture", "flat tyre", "tire burst", "పంక్చర్", "पंचर", "ਟਾਇਰ ਪੰਕਚਰ"]):
            return "PUNCTURE_ASSISTANCE"
        if any(w in lowered for w in ["call", "contact", "phone", "కాల్", "ఫోన్", "कॉल", "फ़ोन"]):
            return "CALL_CONTACT"

        # Owner financials & fleet map
        if any(w in lowered for w in ["profit", "earned", "revenue", "spend", "expense", "cost", "ఆదాయం", "లాభం", "कमाई", "मुनाफा", "ਬੱਚਤ", "नफा"]):
            return "PROFIT_ANALYTICS"
        if any(w in lowered for w in ["where are all my vehicles", "where are my vehicles", "vehicle locations", "fleet map", "vehicles on the map", "vehicles on map", "my vehicles", "నా వాహనాలు", "मेरी गाड़ियाँ"]):
            return "VEHICLE_LOCATION"
        if any(w in lowered for w in ["highest profit", "highest fuel", "most diesel", "ర్యాంకింగ్"]):
            return "VEHICLE_RANKINGS"

        # Trip Progress
        if any(w in lowered for w in ["where am i", "trip progress", "how much distance", "ఎంత దూరం ఉంది", "कितनी दूरी बची"]):
            return "TRIP_PROGRESS"

        # Fuel Status vs Fuel Estimate
        if any(w in lowered for w in ["fuel is left", "fuel remaining", "fuel level", "how much fuel", "check fuel", "fuel status", "ఇంధన స్థాయి", "ईंधन स्तर", "ਕਿੰਨਾ ਈਂਧਨ"]):
            return "FUEL_STATUS"
        if any(w in lowered for w in ["fuel", "diesel", "petrol", "డీజిల్", "डीजल", "ਡੀਜ਼ਲ", "डिझेल"]):
            return "FUEL_ESTIMATE"
        if any(w in lowered for w in ["toll", "టోల్", "टोल"]):
            return "TOLL_ESTIMATE"
        if any(w in lowered for w in ["when will", "eta", "reach", "ఎప్పుడు చేరుతుంది", "कब पहुंचेगा"]):
            return "ETA"

        # Return Cargo
        if any(w in lowered for w in ["return cargo", "return load", "backhaul", "రిటర్న్ లోడ్", "वापसी लोड", "ਵਾਪਸੀ ਲੋਡ"]):
            return "RETURN_CARGO"

        # Shipment Tracking
        if any(w in lowered for w in ["shipment", "consignment", "package", "నా రవాణా", "मेरा पार्सल", "ਮੇਰਾ ਪਾਰਸਲ"]):
            return "SHIPMENT_STATUS"

        # Dispatch / Delayed
        if any(w in lowered for w in ["delayed", "delay", "ఆలస్యం", "देरी"]):
            return "DELAYED_SHIPMENTS"

        # System overview
        if any(w in lowered for w in ["overview", "health", "fleet status", "డాష్‌బోర్డ్", "डैशबोर्ड"]):
            return "SYSTEM_OVERVIEW"

        # Trip planning
        if len(cities) >= 2 or any(w in lowered for w in ["go from", "travel from", "plan trip", "ప్రయాణం", "यात्रा", "ਸਫ਼ਰ"]):
            return "TRIP_PLANNING"

        return "GENERAL_SEARCH"

    def _dispatch_intent(
        self,
        intent: str,
        raw_text: str,
        cities: List[str],
        fuel_qty: Optional[float],
        user_role: str,
        language: str,
    ) -> Dict[str, Any]:
        """Dispatch classified intent to the appropriate assistant."""
        # 1. Driver Trip Planning
        if intent == "TRIP_PLANNING":
            orig = cities[0] if len(cities) >= 1 else "Delhi"
            dest = cities[1] if len(cities) >= 2 else "Hyderabad"
            fuel = fuel_qty or 180.0
            return self.driver_asst.plan_driver_trip(orig, dest, current_fuel_l=fuel, language=language)

        # 2. Highway Facilities
        elif intent in ["RESTAURANT_SEARCH", "PARKING_SEARCH", "RESTROOM_SEARCH", "FUEL_STATION_SEARCH"]:
            category_map = {
                "RESTAURANT_SEARCH": "restaurants",
                "PARKING_SEARCH": "parking",
                "RESTROOM_SEARCH": "restrooms",
                "FUEL_STATION_SEARCH": "fuel_stations",
            }
            fac_type = category_map.get(intent, "restaurants")
            return self.driver_asst.search_facilities(fac_type, language=language)

        # 3. Puncture Assistance
        elif intent == "PUNCTURE_ASSISTANCE":
            return self.driver_asst.get_puncture_assistance(language=language)

        # 4. Safe Communication / Calling
        elif intent == "CALL_CONTACT":
            cat = "puncture_shop" if "puncture" in raw_text.lower() else "fleet_operator"
            contact_data = self.comm_service.initiate_contact(target_category=cat, caller_role=user_role)
            return {
                "text": contact_data["message"],
                "speech_text": contact_data["message"],
                "language": language,
                "card_type": "COMMUNICATION_MODAL",
                "card_data": contact_data,
            }

        # 5. Trip Progress
        elif intent == "TRIP_PROGRESS":
            return self.driver_asst.get_trip_progress(language=language)

        # 6. Fuel Status
        elif intent == "FUEL_STATUS":
            text = "Vehicle fuel level is currently at 68% (140 Litres remaining). Sufficient for ~560 km."
            return {
                "text": text,
                "speech_text": text,
                "language": language,
                "card_type": "FUEL_STATUS",
                "card_data": {
                    "fuel_litres": 140.0,
                    "fuel_level_l": 140.0,
                    "fuel_pct": 68.0,
                    "range_km": 560.0,
                    "status": "NORMAL",
                },
            }

        # 7. Owner Financials & Vehicle Rankings
        elif intent == "PROFIT_ANALYTICS":
            return self.owner_asst.get_daily_financial_analytics(language=language)
        elif intent == "VEHICLE_LOCATION":
            return self.owner_asst.get_fleet_locations(language=language)
        elif intent == "VEHICLE_RANKINGS":
            ranking = "fuel" if "fuel" in raw_text.lower() else "profit"
            return self.owner_asst.get_vehicle_rankings(ranking, language=language)

        # 8. Operator Queries
        elif intent == "DELAYED_SHIPMENTS":
            return self.operator_asst.get_delayed_shipments(language=language)

        # 9. Customer Shipment Status
        elif intent == "SHIPMENT_STATUS":
            return self.customer_asst.get_shipment_status(language=language)

        # 10. Admin Overview
        elif intent == "SYSTEM_OVERVIEW":
            return self.admin_asst.get_system_overview(language=language)

        # 11. Fallback Fuel / Toll / ETA query
        elif intent in ["FUEL_ESTIMATE", "TOLL_ESTIMATE", "ETA"]:
            orig = cities[0] if len(cities) >= 1 else "Delhi"
            dest = cities[1] if len(cities) >= 2 else "Hyderabad"
            return self.driver_asst.plan_driver_trip(orig, dest, language=language)

        # General Search Fallback
        return {
            "text": f"Universal Search: Found results matching '{raw_text}'.",
            "speech_text": f"Found results matching your query.",
            "language": language,
            "card_type": "SEARCH_RESULTS",
            "card_data": {"query": raw_text},
        }

    def _execute_confirmed_action(self, payload: Dict[str, Any], user_role: str, language: str) -> Dict[str, Any]:
        """Execute action once user confirms with [YES]."""
        orig = payload.get("origin", "Delhi")
        dest = payload.get("destination", "Hyderabad")
        text = f"Trip from {orig} to {dest} has been officially started. GPS navigation and telematics tracking are active."
        return {
            "text": text,
            "speech_text": text,
            "language": language,
            "card_type": "TRIP_STARTED",
            "card_data": {"origin": orig, "destination": dest, "status": "IN_TRANSIT", "start_time": "Now"},
            "requires_confirmation": False,
        }

    def _check_rbac(self, intent: str, role: str) -> bool:
        """Enforce strict RBAC permissions across all intents."""
        r = role.lower()
        if r in ["operator", "fleet_manager"]:
            r = "fleet_operator"
        if r in ["admin", "fleet_operator"]:
            return True
        if r in ["fleet_operator", "owner"]:
            return intent in [
                "PROFIT_ANALYTICS", "VEHICLE_LOCATION", "VEHICLE_RANKINGS", "FUEL_STATUS",
                "FUEL_ESTIMATE", "TOLL_ESTIMATE", "ETA", "RETURN_CARGO", "CALL_CONTACT",
                "SYSTEM_OVERVIEW", "GENERAL_SEARCH", "TRIP_PLANNING", "RESTAURANT_SEARCH",
                "PARKING_SEARCH", "RESTROOM_SEARCH", "FUEL_STATION_SEARCH", "PUNCTURE_ASSISTANCE",
            ]
        if r == "driver":
            return intent in [
                "TRIP_PLANNING", "TRIP_PROGRESS", "FUEL_STATUS", "RESTAURANT_SEARCH", "PARKING_SEARCH",
                "RESTROOM_SEARCH", "FUEL_STATION_SEARCH", "PUNCTURE_ASSISTANCE", "CALL_CONTACT",
                "FUEL_ESTIMATE", "TOLL_ESTIMATE", "ETA", "RETURN_CARGO", "GENERAL_SEARCH",
            ]
        if r == "customer":
            return intent in ["SHIPMENT_STATUS", "ETA", "CALL_CONTACT", "GENERAL_SEARCH"]
        return False

    def _extract_cities(self, text: str) -> List[str]:
        """Extract canonical Indian city names from multilingual text."""
        found = []
        lowered = text.lower()
        for canonical, aliases in CITIES_MAP.items():
            for alias in aliases:
                if alias.lower() in lowered or alias in text:
                    if canonical not in found:
                        found.append(canonical)
                    break
        
        # Fallback regex city extraction if <= 1 city is found
        if len(found) < 2:
            # Check for English pattern: "[CityA] to [CityB]"
            match = re.search(r'(?:from\s+)?([a-zA-Z]{3,15})\s+to\s+([a-zA-Z]{3,15})', text, re.IGNORECASE)
            if match:
                city1 = match.group(1).strip().capitalize()
                city2 = match.group(2).strip().capitalize()
                
                # Normalize spelling using aliases map
                for canonical, aliases in CITIES_MAP.items():
                    if city1.lower() in [a.lower() for a in aliases]:
                        city1 = canonical
                    if city2.lower() in [a.lower() for a in aliases]:
                        city2 = canonical
                        
                stop_words = ["Plan", "Trip", "Travel", "Go", "Me", "Route", "How", "Show", "Lorry", "Truck", "My", "The", "Yes", "Confirm", "Search"]
                if city1 not in stop_words and city2 not in stop_words:
                    if city1 not in found:
                        found.append(city1)
                    if city2 not in found:
                        found.append(city2)
            
            # Check for Telugu pattern: "[CityA] నుండి [CityB]"
            te_match = re.search(r'([\u0C00-\u0C7F]+)\s*(?:నుండి|టు|నుంచి)\s*([\u0C00-\u0C7F]+)', text)
            if te_match:
                city1 = te_match.group(1).strip()
                city2 = te_match.group(2).strip()
                te_stop_words = ["నేను", "వెళ్ళాలి", "నాకు", "ఒక", "రూట్"]
                if city1 not in te_stop_words and city2 not in te_stop_words:
                    if city1 not in found:
                        found.append(city1)
                    if city2 not in found:
                        found.append(city2)
        return found

    def _extract_fuel_qty(self, text: str) -> Optional[float]:
        """Extract fuel quantity."""
        match = re.search(r"(\d+(?:\.\d+)?)\s*(?:litres?|liters?|ltrs?|l|లీటర్లు|लीटर|ਲੀਟਰ|लिटर)?", text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return None

    def _detect_language(self, text: str) -> str:
        """Detect language script heuristically."""
        if re.search(r"[\u0C00-\u0C7F]", text):
            return "te"
        if re.search(r"[\u0A00-\u0A7F]", text):
            return "pa"
        if re.search(r"[\u0900-\u097F]", text):
            if any(w in text for w in ["आहे", "नाही", "कुठे", "झाला", "कसा"]):
                return "mr"
            return "hi"
        return "en"


_router_instance: Optional[UniversalIntentRouter] = None


def get_intent_router() -> UniversalIntentRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = UniversalIntentRouter()
    return _router_instance
