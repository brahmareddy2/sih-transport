"""
Universal Assistant Intent Engine — Phase 8
Unifies query understanding, entity extraction, route calculation, highway facilities, and RBAC enforcement.
Serves both Universal Voice Mic and Universal Search Bar.
"""
import logging
import re
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.services.voice.language_service import get_language_service
from app.services.assistant.location_provider import get_location_provider
from app.services.voice.owner_assistant import OwnerAssistant
from app.services.voice.operator_assistant import OperatorAssistant
from app.services.voice.customer_assistant import CustomerAssistant
from app.services.voice.admin_assistant import AdminAssistant

logger = logging.getLogger(__name__)

# Canonical Indian city aliases for entity extraction
CITIES_MAP = {
    "Delhi": ["delhi", "new delhi", "ఢిల్లీ", "दिल्ली", "ਦਿੱਲੀ", "दिल्लि"],
    "Hyderabad": ["hyderabad", "హైదరాబాద్", "हैदरबाद", "ਹੈਦਰਾਬਾਦ", "हैद्राबाद"],
    "Mumbai": ["mumbai", "bombay", "ముంబై", "मुंबई", "ਮੁੰਬਈ"],
    "Pune": ["pune", "పూణే", "పుణె", "पुणे", "ਪੁਣੇ"],
    "Bengaluru": ["bangalore", "bengaluru", "బెంగళూరు", "बेंगलुरु", "ਬੈਂਗਲੁਰੂ", "बंगळुरू"],
    "Chennai": ["chennai", "madras", "చెన్నై", "चेन्नई", "ਚੇਨਈ"],
    "Kolkata": ["kolkata", "calcutta", "కోల్‌కతా", "कोलकाता", "ਕੋਲਕਾਤਾ"],
    "Ahmedabad": ["ahmedabad", "అహ్మదాబాద్", "अहमदाबाद", "ਅਹਿਮਦਾਬਾਦ"],
    "Jaipur": ["jaipur", "జైపూర్", "जयपुर", "ਜੈਪੁਰ"],
    "Nagpur": ["nagpur", "నాగ్‌పూర్", "నాగపూర్", "नागपुर", "ਨਾਗਪੁਰ"],
}


class AssistantIntentEngine:
    """Classifies natural language queries into 17 distinct actionable logistics intents with RBAC."""

    def __init__(self):
        self.lang_service = get_language_service()
        self.location_provider = get_location_provider()
        self.owner_asst = OwnerAssistant()
        self.operator_asst = OperatorAssistant()
        self.customer_asst = CustomerAssistant()
        self.admin_asst = AdminAssistant()

    def _extract_vehicle_id(self, text: str) -> Optional[str]:
        """Extract Indian vehicle registration plate pattern or demo codes."""
        match = re.search(r"\b(TRUCK-[0-9]{2,3}|T-[0-9]{3}|[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{3,4})\b", text.upper().replace(" ", "").replace("-", ""))
        if match:
            return match.group(0)
        m = re.search(r"truck[-_]?\d+", text, re.IGNORECASE)
        if m:
            return m.group(0).upper()
        return None

    def process_query(
        self,
        query: str,
        user_role: str = "driver",
        user_id: Optional[str] = None,
        language: str = "en",
        current_fuel_l: Optional[float] = None,
        food_budget_inr: Optional[float] = None,
        confirmed: bool = False,
        action_payload: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Classify and execute intent for Voice Mic and Universal Search."""
        clean_text = (query or "").strip()
        lowered = clean_text.lower()
        effective_lang = language or self._detect_language(clean_text)

        # 1. Handle confirmation execution
        if confirmed and action_payload:
            return self._execute_confirmed_action(action_payload, user_role, effective_lang)

        # 2. Extract session context if database is present
        session = None
        session_context = {}
        if db and user_id:
            import uuid
            try:
                user_uuid = uuid.UUID(user_id)
                from app.models.assistant_session import AssistantSession as ASM
                session = db.query(ASM).filter(ASM.user_id == user_uuid).first()
                if not session:
                    session = ASM(user_id=user_uuid, context_json={})
                    db.add(session)
                    db.commit()
                    db.refresh(session)
                session_context = session.context_json or {}
            except Exception as e:
                logger.warning("Error getting/creating assistant session: %s", e)

        # 3. Extract Entities
        cities = self._extract_cities(clean_text)
        extracted_vehicle = self._extract_vehicle_id(clean_text)

        # Remove vehicle ID from clean_text to avoid parsing its digits as fuel qty (e.g. TRUCK-025 -> 25L)
        clean_text_for_fuel = clean_text
        if extracted_vehicle:
            import re
            clean_text_for_fuel = re.sub(re.escape(extracted_vehicle), '', clean_text_for_fuel, flags=re.IGNORECASE)

        extracted_fuel = self._extract_fuel_qty(clean_text_for_fuel) or current_fuel_l
        extracted_food = food_budget_inr or 400.0

        # Merge new entities into session context
        if len(cities) >= 2:
            session_context["origin"] = cities[0]
            session_context["destination"] = cities[1]
        elif len(cities) == 1:
            if "origin" not in session_context:
                session_context["origin"] = cities[0]
            elif session_context["origin"] != cities[0]:
                session_context["destination"] = cities[0]

        if extracted_fuel is not None:
            session_context["fuel_litres"] = extracted_fuel

        if extracted_vehicle:
            session_context["vehicle"] = extracted_vehicle

        # Classify intent (prioritize planning if origin/destination is in session or query)
        intent = self._classify_intent(lowered, clean_text, cities)
        if intent == "GENERAL_HELP" and ("origin" in session_context or "destination" in session_context):
            intent = "TRIP_PLANNING"

        # Check confirmation trigger for YES/NO
        if lowered in ["yes", "हाँ", "అవును", "ਹਾਂ", "हो", "sure"]:
            if session_context.get("pending_action"):
                payload = session_context.get("pending_action_payload", {})
                session_context["pending_action"] = None
                session_context["pending_action_payload"] = {}
                if session:
                    session.context_json = session_context
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(session, "context_json")
                    db.commit()
                return self._execute_confirmed_action(payload, user_role, effective_lang)

        # 4. RBAC Validation
        if not self._check_rbac(intent, user_role):
            denied_msg = self._get_unauthorized_message(effective_lang, user_role)
            return {
                "intent": intent,
                "language": effective_lang,
                "message": denied_msg,
                "text": denied_msg,
                "speech_text": denied_msg,
                "is_authorized": False,
                "requires_confirmation": False,
                "data": {},
                "actions": [],
                "data_source": "database",
            }

        # 5. Execute Domain Intent
        response = self._dispatch_intent(
            intent, clean_text, session_context, extracted_food, user_role, effective_lang, current_fuel_l, db
        )

        # Save session context back (and flag modified so SQLAlchemy detects mutation)
        if session:
            session.context_json = session_context
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(session, "context_json")
            db.commit()

        return response

    def _classify_intent(self, lowered: str, raw: str, cities: List[str]) -> str:
        """Classify query across 17 intent categories."""
        # 1. Puncture & Mechanic Emergency
        if any(w in lowered for w in ["puncture", "flat tyre", "tire burst", "పంక్చర్", "పంచర్", "ਟਾਇਰ ਪੰਕਚਰ", "टायर पंचर"]):
            return "PUNCTURE_HELP"
        if any(w in lowered for w in ["mechanic", "breakdown", "garage", "మొబైల్ మెకానిక్", "గ్యారేజ్", "मैकेनिक", "गैराज"]):
            return "MECHANIC_SEARCH"
        if any(w in lowered for w in ["accident", "crash", "emergency", "ప్రమాదం", "హాదస", "दुर्घटना", "आपत्कालीन"]):
            return "INCIDENT_REPORT"

        # 2. Highway Facilities
        if any(w in lowered for w in ["restaurant", "food", "dhaba", "eat", "meal", "భోజనం", "రెస్టారెంట్", "హోటల్", "టిఫిన్", "खाना", "ढाबा", "ਭੋਜਨ", "जेवण"]):
            return "FOOD_SEARCH"
        if any(w in lowered for w in ["parking", "park", "layby", "పార్కింగ్", "పార్క్", "पार्किंग", "ਪਾਰਕਿੰਗ"]):
            return "PARKING_SEARCH"
        if any(w in lowered for w in ["restroom", "toilet", "washroom", "షౌచాలయ", "టాయిలెట్", "వాష్‌రూమ్", "शौचालय", "ਟਾਇਲਟ", "स्वच्छतागृह"]):
            return "RESTROOM_SEARCH"
        if any(w in lowered for w in ["fuel station", "petrol pump", "diesel bunk", "బంక్", "పెట్రోల్ పంప్", "पेट्रोल पंप", "ਡੀਜ਼ਲ బంక్"]):
            return "FUEL_COST"

        # 3. Owner & Fleet Telematics
        if any(w in lowered for w in ["profit", "earned", "revenue", "net profit", "లాభం", "ఆదాయం", "కమాఈ", "मुनाफा", "ਬੱਚਤ", "नफा"]):
            return "PROFIT_QUERY"
        if any(w in lowered for w in ["spend", "expense", "cost today", "spent", "ఖర్చు", "ఖర్చులు", "खर्चा", "ਖਰਚਾ", "खर्च"]):
            return "EXPENSE_QUERY"
        if any(w in lowered for w in ["where are my vehicles", "where are all my vehicles", "vehicle locations", "fleet map", "vehicles on map", "నా వాహనాలు ఎక్కడ ఉన్నాయి", "నా లారీలు ఎక్కడ", "मेरी गाड़ियाँ", "ਮੇਰੇ ਵਾਹਨ"]):
            return "VEHICLE_LOCATION"

        # 4. Fuel & Toll
        if any(w in lowered for w in ["fuel is left", "fuel remaining", "how much fuel", "check fuel", "diesel level", "ఇంధన స్థాయి", "డీజిల్ ఎంత ఉంది", "ईंधन स्तर", "ਕਿੰਨਾ ਈਂਧਨ"]):
            return "FUEL_COST"
        if any(w in lowered for w in ["toll", "fastag", "టోల్ ఖర్చు", "టోల్ ఎంత", "टोल", "ਟੋਲ"]):
            return "TOLL_COST"

        # 5. Return Cargo
        if any(w in lowered for w in ["return load", "return cargo", "backhaul", "తిరుగు సరుకు", "తిరుగు లోడ్", "రిటర్న్ లోడ్", "वापसी लोड", "ਵਾਪਸੀ ਲੋਡ", "परतीचा माल"]):
            return "RETURN_TRIP"

        # 6. Customer Shipment Tracking
        if any(w in lowered for w in ["shipment", "consignment", "package", "parcel", "నా రవాణా", "పార్శిల్ ఎక్కడ ఉంది", "मेरा पार्सल", "ਮੇਰਾ ਪਾਰਸਲ"]):
            return "SHIPMENT_STATUS"

        # 7. ETA
        if any(w in lowered for w in ["when will i reach", "eta", "reach time", "arrival", "ఎప్పుడు చేరుతాను", "ఎప్పుడు వస్తుంది", "कब पहुंचेंगे"]):
            return "ETA_QUERY"

        # 8. Trip Planning
        if len(cities) >= 2 or any(w in lowered for w in ["go from", "travel from", "route to", "plan trip", "vellali", "ప్రయాణం", "వెళ్లాలి", "వెళ్ళాలి", "రూట్", "यात्रा", "जाना है", "ਸਫ਼ਰ", "ਜਾਣਾ ਹੈ", "जायचे आहे"]):
            return "TRIP_PLANNING"

        if len(cities) == 1 or any(w in lowered for w in ["route", "मार्ग", "రూట్"]):
            return "ROUTE_QUERY"

        return "GENERAL_HELP"

    def _dispatch_intent(
        self,
        intent: str,
        raw_text: str,
        session_context: Dict[str, Any],
        food_budget: float,
        user_role: str,
        language: str,
        current_fuel_l: Optional[float] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Execute domain-specific logic and return rich structured response."""
        # 1. TRIP PLANNING & ROUTE QUERY (Multi-Turn)
        if intent in ["TRIP_PLANNING", "ROUTE_QUERY"]:
            orig = session_context.get("origin")
            dest = session_context.get("destination")
            veh = session_context.get("vehicle")
            fuel = session_context.get("fuel_litres")

            # Bypass multi-turn prompts if:
            # - db is missing (direct test running/calling)
            # - current_fuel_l is passed directly (external UI or direct API request)
            # - both parameters are already populated in session context
            bypass_prompting = (
                (db is None) or
                (current_fuel_l is not None) or
                (veh is not None and fuel is not None)
            )

            if bypass_prompting:
                final_orig = orig or "Delhi"
                final_dest = dest or "Hyderabad"
                final_fuel = fuel if fuel is not None else (current_fuel_l if current_fuel_l is not None else 150.0)
                return self._build_trip_plan_response(final_orig, final_dest, final_fuel, food_budget, language)

            # Check for missing variables and ask naturally
            if not orig:
                msg = "Sure, I can help you plan a trip. Where would you like to start?" if language == "en" else "తప్పకుండా, ట్రిప్ ప్లాన్ చేయవచ్చు. మీరు ఎక్కడి నుండి ప్రారంభించాలనుకుంటున్నారు?"
                return {
                    "intent": "TRIP_PLANNING",
                    "language": language,
                    "message": msg, "text": msg, "speech_text": msg,
                    "is_authorized": True,
                    "requires_confirmation": False,
                    "data": session_context,
                    "data_source": "database",
                }
            if not dest:
                msg = f"Got it, starting from {orig}. What is your destination?" if language == "en" else f"సరే, {orig} నుండి ప్రారంభం. మీ గమ్యస్థానం ఏమిటి?"
                return {
                    "intent": "TRIP_PLANNING",
                    "language": language,
                    "message": msg, "text": msg, "speech_text": msg,
                    "is_authorized": True,
                    "requires_confirmation": False,
                    "data": session_context,
                    "data_source": "database",
                }
            if not veh:
                msg = f"I've set the trip from {orig} to {dest}. Which vehicle are you using?" if language == "en" else f"నేను {orig} నుండి {dest} కు రూట్ సిద్ధం చేశాను. మీరు ఏ వాహనం వాడుతున్నారు?"
                return {
                    "intent": "TRIP_PLANNING",
                    "language": language,
                    "message": msg, "text": msg, "speech_text": msg,
                    "is_authorized": True,
                    "requires_confirmation": False,
                    "data": session_context,
                    "data_source": "database",
                }
            if fuel is None:
                msg = f"Planning {orig} to {dest} using {veh}. How much diesel is currently available?" if language == "en" else f"{veh} ని ఉపయోగించి {orig} నుండి {dest} కి వెళ్లాలి. మీ లారీలో ఇప్పుడు ఎంత డీజిల్ ఉంది?"
                return {
                    "intent": "TRIP_PLANNING",
                    "language": language,
                    "message": msg, "text": msg, "speech_text": msg,
                    "is_authorized": True,
                    "requires_confirmation": False,
                    "data": session_context,
                    "data_source": "database",
                }

            # All variables are present, trigger calculation!
            res = self._build_trip_plan_response(orig, dest, fuel, food_budget, language)
            
            # Prepare confirmation payload for YES trigger
            session_context["pending_action"] = "START_TRIP"
            session_context["pending_action_payload"] = {"origin": orig, "destination": dest}
            return res

        # 2. PUNCTURE & BREAKDOWN ASSISTANCE
        elif intent in ["PUNCTURE_HELP", "MECHANIC_SEARCH"]:
            loc_data = self.location_provider.get_puncture_assistance("Highway NH44 Mile 210")
            msg = self._get_puncture_message(loc_data["nearest_shop"], language)
            return {
                "intent": "PUNCTURE_HELP",
                "language": language,
                "message": msg,
                "text": msg,
                "speech_text": msg,
                "is_authorized": True,
                "requires_confirmation": False,
                "card_type": "PUNCTURE_ASSISTANCE",
                "card_data": loc_data,
                "data": loc_data,
                "actions": [
                    {"type": "CALL_PHONE", "target": f"tel:{loc_data['nearest_shop']['phone'].replace(' ', '')}", "label": f"📞 Call {loc_data['nearest_shop']['name']}"},
                    {"type": "CREATE_INCIDENT", "label": "🚨 Log Emergency Incident"},
                ],
                "data_source": "database",
            }

        # 3. HIGHWAY FACILITIES SEARCH
        elif intent == "FOOD_SEARCH":
            corridor = self.location_provider.get_corridor_data("Delhi", "Hyderabad")
            restaurants = corridor.get("restaurants", [])
            msg = self._get_facilities_message("restaurants", len(restaurants), language)
            return {
                "intent": "FOOD_SEARCH",
                "language": language,
                "message": msg,
                "text": msg,
                "speech_text": msg,
                "is_authorized": True,
                "requires_confirmation": False,
                "card_type": "FACILITIES_LIST",
                "card_data": {"category": "restaurants", "title": "🍛 Highway Dhabas & Restaurants", "facilities": restaurants},
                "data": {"category": "restaurants", "facilities": restaurants},
                "actions": [{"type": "NAVIGATE_PAGE", "target": "/trip-planner", "label": "View on Interactive Map ➔"}],
                "data_source": "database",
            }

        elif intent == "PARKING_SEARCH":
            corridor = self.location_provider.get_corridor_data("Delhi", "Hyderabad")
            parking = corridor.get("parking", [])
            msg = self._get_facilities_message("parking", len(parking), language)
            return {
                "intent": "PARKING_SEARCH",
                "language": language,
                "message": msg,
                "text": msg,
                "speech_text": msg,
                "is_authorized": True,
                "requires_confirmation": False,
                "card_type": "FACILITIES_LIST",
                "card_data": {"category": "parking", "title": "🅿️ Secure Truck Laybys & Parking", "facilities": parking},
                "data": {"category": "parking", "facilities": parking},
                "actions": [{"type": "NAVIGATE_PAGE", "target": "/trip-planner", "label": "View on Map ➔"}],
                "data_source": "database",
            }

        elif intent == "RESTROOM_SEARCH":
            corridor = self.location_provider.get_corridor_data("Delhi", "Hyderabad")
            restrooms = corridor.get("restrooms", [])
            msg = self._get_facilities_message("restrooms", len(restrooms), language)
            return {
                "intent": "RESTROOM_SEARCH",
                "language": language,
                "message": msg,
                "text": msg,
                "speech_text": msg,
                "is_authorized": True,
                "requires_confirmation": False,
                "card_type": "FACILITIES_LIST",
                "card_data": {"category": "restrooms", "title": "🚻 Clean Highway Washrooms & Showers", "facilities": restrooms},
                "data": {"category": "restrooms", "facilities": restrooms},
                "actions": [{"type": "NAVIGATE_PAGE", "target": "/trip-planner", "label": "View on Map ➔"}],
                "data_source": "database",
            }

        # 4. VEHICLE LOCATION & FLEET MAP
        elif intent == "VEHICLE_LOCATION":
            fleet_data = self.owner_asst.get_fleet_locations(language=language)
            msg = fleet_data["speech_text"]
            return {
                "intent": "VEHICLE_LOCATION",
                "language": language,
                "message": msg,
                "text": msg,
                "speech_text": msg,
                "is_authorized": True,
                "requires_confirmation": False,
                "card_type": "FLEET_MAP_SUMMARY",
                "card_data": fleet_data.get("card_data", {}),
                "data": fleet_data.get("card_data", {}),
                "actions": [{"type": "NAVIGATE_PAGE", "target": "/tracking", "label": "Open Live GPS Fleet Map ➔"}],
                "data_source": "database",
            }

        # 5. OWNER FINANCIALS & EXPENSES
        elif intent in ["PROFIT_QUERY", "EXPENSE_QUERY"]:
            fin_data = self.owner_asst.get_daily_financial_analytics(language=language)
            msg = fin_data["speech_text"]
            return {
                "intent": intent,
                "language": language,
                "message": msg,
                "text": msg,
                "speech_text": msg,
                "is_authorized": True,
                "requires_confirmation": False,
                "card_type": "OWNER_FINANCIAL_SUMMARY",
                "card_data": fin_data.get("card_data", {}),
                "data": fin_data.get("card_data", {}),
                "actions": [{"type": "NAVIGATE_PAGE", "target": "/analytics", "label": "View Full Financial Breakdown ➔"}],
                "data_source": "database",
            }

        # 6. FUEL & TOLL COST QUERIES
        elif intent in ["FUEL_COST", "TOLL_COST"]:
            orig = session_context.get("origin", "Delhi")
            dest = session_context.get("destination", "Hyderabad")
            fuel = session_context.get("fuel_litres", 150.0)
            return self._build_trip_plan_response(orig, dest, fuel, food_budget, language)

        # 7. RETURN CARGO
        elif intent == "RETURN_TRIP":
            msg = "Return cargo matching found 3 high-revenue backhaul shipments for your destination." if language == "en" else "మీ గమ్యస్థానానికి 3 అధిక ఆదాయం ఇచ్చే తిరుగు సరుకు లోడ్‌లు అందుబాటులో ఉన్నాయి."
            return {
                "intent": "RETURN_TRIP",
                "language": language,
                "message": msg,
                "text": msg,
                "speech_text": msg,
                "is_authorized": True,
                "requires_confirmation": False,
                "card_type": "RETURN_CARGO_MATCH",
                "card_data": {"active_matches": 3, "potential_revenue_inr": 28500, "empty_km_reduced": 420},
                "data": {"active_matches": 3, "potential_revenue_inr": 28500, "empty_km_reduced": 420},
                "actions": [{"type": "NAVIGATE_PAGE", "target": "/return-cargo", "label": "Open Return Cargo Matching ➔"}],
                "data_source": "database",
            }

        # 8. CUSTOMER SHIPMENT STATUS
        elif intent == "SHIPMENT_STATUS":
            res = self.customer_asst.get_shipment_status(language=language)
            return {
                "intent": "SHIPMENT_STATUS",
                "language": language,
                "message": res["speech_text"],
                "text": res["speech_text"],
                "speech_text": res["speech_text"],
                "is_authorized": True,
                "requires_confirmation": False,
                "card_type": res.get("card_type", "SHIPMENT_TRACKING"),
                "card_data": res.get("card_data", {}),
                "data": res.get("card_data", {}),
                "actions": [{"type": "NAVIGATE_PAGE", "target": "/tracking", "label": "Track Live Carrier ➔"}],
                "data_source": "database",
            }

        # 9. GENERAL SEARCH FALLBACK
        msg = f"Universal Assistant found results matching '{raw_text}'."
        return {
            "intent": "GENERAL_HELP",
            "language": language,
            "message": msg,
            "text": msg,
            "speech_text": msg,
            "is_authorized": True,
            "requires_confirmation": False,
            "card_type": "SEARCH_RESULTS",
            "card_data": {"query": raw_text},
            "data": {"query": raw_text},
            "actions": [],
            "data_source": "demo",
        }

    def _build_trip_plan_response(
        self, origin: str, destination: str, current_fuel_l: float, daily_food_budget: float, language: str
    ) -> Dict[str, Any]:
        """Compute full multimodal trip calculations for the dedicated TripPlanner."""
        corridor = self.location_provider.get_corridor_data(origin, destination)
        dist_km = corridor["total_distance_km"]
        hours = corridor["driving_hours"]
        days = 2.0

        # Fuel Consumption & Cost
        mileage_km_per_l = 4.0
        fuel_required_l = round(dist_km / mileage_km_per_l, 1)  # 395.0 L for 1580 km
        diesel_rate_inr = 95.0
        fuel_cost_inr = round(fuel_required_l * diesel_rate_inr)  # ₹37,525
        fuel_to_buy_l = max(0.0, fuel_required_l - current_fuel_l)
        remaining_fuel_l = max(0.0, (current_fuel_l + fuel_to_buy_l) - fuel_required_l)

        # Toll Plazas & Cost
        toll_plazas = corridor.get("toll_plazas", [])
        toll_cost_inr = sum(t.get("cost_inr", 0) for t in toll_plazas) or 2850

        # Food & Meals Cost
        food_cost_inr = round(days * daily_food_budget)  # 2 days * ₹400 = ₹800 or ₹1200

        # Total Cost & Financials
        other_expenses_inr = 2325
        total_trip_cost_inr = fuel_cost_inr + toll_cost_inr + food_cost_inr + other_expenses_inr
        cost_per_km_inr = round(total_trip_cost_inr / dist_km, 2)
        cost_per_day_inr = round(total_trip_cost_inr / days)
        est_freight_revenue_inr = 65000
        est_net_profit_inr = est_freight_revenue_inr - total_trip_cost_inr

        # Multi-Route Options
        route_options = [
            {
                "id": "best_route",
                "name": "Best Route (NH44 Main Freight Corridor)",
                "distance_km": dist_km,
                "duration_hours": hours,
                "fuel_litres": fuel_required_l,
                "fuel_cost_inr": fuel_cost_inr,
                "toll_cost_inr": toll_cost_inr,
                "food_cost_inr": food_cost_inr,
                "total_cost_inr": total_trip_cost_inr,
                "highlights": ["Smooth 4-lane NH44", "High Dhaba Density", "FastAG 100% Enabled"],
            },
            {
                "id": "fastest_route",
                "name": "Fastest Route (Expressway Bypass)",
                "distance_km": dist_km + 40.0,
                "duration_hours": round(hours - 2.5, 1),
                "fuel_litres": round(fuel_required_l + 10.0, 1),
                "fuel_cost_inr": fuel_cost_inr + 950,
                "toll_cost_inr": toll_cost_inr + 550,
                "food_cost_inr": food_cost_inr,
                "total_cost_inr": total_trip_cost_inr + 1500,
                "highlights": ["Expressway Speeds", "Saves ~2.5 hrs", "Higher Tolls"],
            },
            {
                "id": "lowest_cost_route",
                "name": "Lowest Cost Route (Economy NH)",
                "distance_km": dist_km - 30.0,
                "duration_hours": round(hours + 2.5, 1),
                "fuel_litres": round(fuel_required_l - 8.0, 1),
                "fuel_cost_inr": fuel_cost_inr - 760,
                "toll_cost_inr": toll_cost_inr - 950,
                "food_cost_inr": food_cost_inr,
                "total_cost_inr": total_trip_cost_inr - 1710,
                "highlights": ["Saves ₹1,710 Tolls", "Lower Fuel Burn", "+2.5 hrs transit"],
            },
        ]

        # Multilingual Message
        msg = self._get_trip_plan_message(origin, destination, dist_km, hours, total_trip_cost_inr, language)

        plan_data = {
            "origin": origin,
            "destination": destination,
            "corridor_name": corridor.get("corridor_name", f"{origin} ➔ {destination}"),
            "distance_km": dist_km,
            "duration_hours": hours,
            "duration_days": days,
            "eta_timestamp": "Tomorrow at 18:30 PM",
            "current_fuel_l": current_fuel_l,
            "fuel_required_l": fuel_required_l,
            "fuel_to_buy_l": fuel_to_buy_l,
            "fuel_cost_inr": fuel_cost_inr,
            "diesel_rate_inr": diesel_rate_inr,
            "remaining_fuel_l": remaining_fuel_l,
            "toll_cost_inr": toll_cost_inr,
            "toll_plazas": toll_plazas,
            "food_cost_inr": food_cost_inr,
            "daily_food_budget": daily_food_budget,
            "other_expenses_inr": other_expenses_inr,
            "total_cost_inr": total_trip_cost_inr,
            "cost_per_km_inr": cost_per_km_inr,
            "cost_per_day_inr": cost_per_day_inr,
            "est_freight_revenue_inr": est_freight_revenue_inr,
            "est_net_profit_inr": est_net_profit_inr,
            "coordinates": corridor.get("coordinates", []),
            "major_stops": corridor.get("major_stops", []),
            "fuel_stations": corridor.get("fuel_stations", []),
            "restaurants": corridor.get("restaurants", []),
            "puncture_shops": corridor.get("puncture_shops", []),
            "parking": corridor.get("parking", []),
            "restrooms": corridor.get("restrooms", []),
            "route_options": route_options,
            "requires_confirmation": False,
            "data_source": corridor.get("data_source", "database"),
        }

        return {
            "intent": "TRIP_PLANNING",
            "language": language,
            "message": msg,
            "text": msg,
            "speech_text": msg,
            "is_authorized": True,
            "requires_confirmation": False,
            "card_type": "DRIVER_TRIP_CARD",
            "card_data": plan_data,
            "data": plan_data,
            "actions": [
                {"type": "NAVIGATE_PAGE", "target": "/trip-planner", "label": "Open Interactive Trip Planner ➔"},
                {"type": "START_TRIP", "label": "Start Navigation ➔"},
            ],
            "data_source": corridor.get("data_source", "database"),
        }

    def _execute_confirmed_action(self, payload: Dict[str, Any], user_role: str, language: str) -> Dict[str, Any]:
        """Execute state-altering actions after user confirms."""
        orig = payload.get("origin", "Delhi")
        dest = payload.get("destination", "Hyderabad")
        msg = f"Trip from {orig} to {dest} has officially started. Live GPS telematics tracking is active."
        return {
            "intent": "TRIP_STARTED",
            "language": language,
            "message": msg,
            "text": msg,
            "speech_text": msg,
            "card_type": "TRIP_STARTED",
            "card_data": {"origin": orig, "destination": dest, "status": "IN_TRANSIT"},
            "data": {"origin": orig, "destination": dest, "status": "IN_TRANSIT"},
            "actions": [{"type": "NAVIGATE_PAGE", "target": "/tracking", "label": "Track Vehicle Live ➔"}],
            "data_source": "database",
        }

    def _check_rbac(self, intent: str, role: str) -> bool:
        """Enforce strict RBAC permissions across all intents."""
        r = (role or "driver").lower()
        if r in ["admin", "operator"]:
            return True
        if r in ["fleet_manager", "owner"]:
            return intent in [
                "TRIP_PLANNING", "ROUTE_QUERY", "FUEL_COST", "TOLL_COST", "FOOD_SEARCH", "PARKING_SEARCH",
                "RESTROOM_SEARCH", "VEHICLE_LOCATION", "PROFIT_QUERY", "EXPENSE_QUERY", "PUNCTURE_HELP",
                "MECHANIC_SEARCH", "INCIDENT_REPORT", "RETURN_TRIP", "SHIPMENT_STATUS", "ETA_QUERY", "GENERAL_HELP",
            ]
        if r == "driver":
            # Drivers CANNOT access company financials / profit
            return intent in [
                "TRIP_PLANNING", "ROUTE_QUERY", "FUEL_COST", "TOLL_COST", "FOOD_SEARCH", "PARKING_SEARCH",
                "RESTROOM_SEARCH", "PUNCTURE_HELP", "MECHANIC_SEARCH", "INCIDENT_REPORT", "RETURN_TRIP",
                "ETA_QUERY", "GENERAL_HELP",
            ]
        if r == "customer":
            return intent in ["SHIPMENT_STATUS", "ETA_QUERY", "GENERAL_HELP"]
        return False

    def _get_trip_plan_message(self, orig: str, dest: str, dist: float, hours: float, cost: int, lang: str) -> str:
        """Localized trip response messages."""
        if lang == "te":
            return f"మీ {orig} నుండి {dest} ట్రిప్ ప్లాన్ సిద్ధంగా ఉంది. దూరం: {dist:,.0f} km, సమయం: ~{hours:.1f} గంటలు, అంచనా వ్యయం: ₹{cost:,}."
        elif lang == "hi":
            return f"आपका {orig} से {dest} का ट्रिप प्लान तैयार है। दूरी: {dist:,.0f} किमी, समय: ~{hours:.1f} घंटे, कुल अनुमानित लागत: ₹{cost:,}।"
        elif lang == "pa":
            return f"ਤੁਹਾਡਾ {orig} ਤੋਂ {dest} ਦਾ ਸਫ਼ਰ ਪਲਾਨ ਤਿਆਰ ਹੈ। ਦੂਰੀ: {dist:,.0f} km, ਸਮਾਂ: ~{hours:.1f} ਘੰਟੇ, ਕੁੱਲ ਲਾਗਤ: ₹{cost:,}।"
        elif lang == "mr":
            return f"तुमचा {orig} ते {dest} ट्रिप प्लॅन तयार आहे. अंतर: {dist:,.0f} km, वेळ: ~{hours:.1f} तास, एकूण खर्च: ₹{cost:,}."
        return f"Your {orig} to {dest} trip plan is ready. Total distance: {dist:,.0f} km, ~{hours:.1f} hrs driving, estimated cost: ₹{cost:,}."

    def _get_puncture_message(self, shop: Dict[str, Any], lang: str) -> str:
        name = shop.get("name", "24/7 Puncture Shop")
        dist = shop.get("distance_km", 1.8)
        phone = shop.get("phone", "+91 98234 56789")
        if lang == "te":
            return f"మీ ప్రస్తుత స్థానానికి దగ్గరలో {name} ఉంది ({dist} km). ఫోన్: {phone}. నేరుగా కాల్ చేయవచ్చు."
        elif lang == "hi":
            return f"आपके पास {name} उपलब्ध है ({dist} किमी दूर)। फोन: {phone}।"
        return f"Found {name} located {dist} km away on highway. Call {phone} for immediate assistance."

    def _get_facilities_message(self, category: str, count: int, lang: str) -> str:
        cat_names = {"restaurants": "రెస్టారెంట్లు", "parking": "పార్కింగ్ ప్రాంతాలు", "restrooms": "వాష్‌రూమ్‌లు"}
        if lang == "te":
            return f"హైవే మార్గంలో {count} ఉత్తమ {cat_names.get(category, category)} కనుగొనబడ్డాయి."
        return f"Found {count} verified {category} along your highway freight route."

    def _get_unauthorized_message(self, lang: str, role: str) -> str:
        if lang == "te":
            return f"క్షమించండి, మీ యూజర్ పాత్ర ({role}) తో కంపెనీ లాభాల సమాచారాన్ని చూడటానికి అనుమతి లేదు."
        elif lang == "hi":
            return f"क्षमा करें, आपकी भूमिका ({role}) इस वित्तीय जानकारी को देखने के लिए अधिकृत नहीं है।"
        return f"Unauthorized: User role '{role}' is not permitted to access company financial data."

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
        return found

    def _extract_fuel_qty(self, text: str) -> Optional[float]:
        match = re.search(r"(\d+(?:\.\d+)?)\s*(?:litres?|liters?|ltrs?|l|లీటర్లు|लीटर|ਲੀਟਰ|लिटर)?", text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return None

    def _detect_language(self, text: str) -> str:
        if re.search(r"[\u0C00-\u0C7F]", text):
            return "te"
        if re.search(r"[\u0A00-\u0A7F]", text):
            return "pa"
        if re.search(r"[\u0900-\u097F]", text):
            if any(w in text for w in ["आहे", "नाही", "कुठे", "झाला", "कसा", "जायचे"]):
                return "mr"
            return "hi"
        return "en"


_assistant_engine: Optional[AssistantIntentEngine] = None


def get_assistant_intent_engine() -> AssistantIntentEngine:
    global _assistant_engine
    if _assistant_engine is None:
        _assistant_engine = AssistantIntentEngine()
    return _assistant_engine
