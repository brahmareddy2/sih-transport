"""
Voice Intent Parser — Phase 8
Extracts intent and entities (origin, destination, fuel quantity, vehicle ID, incident type)
from multilingual voice and text queries in English, Telugu, Hindi, Punjabi, and Marathi.
"""
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Indian City Multilingual Aliases (12 hubs + major logistics nodes)
CITY_SYNONYMS: Dict[str, List[str]] = {
    "Delhi": ["delhi", "new delhi", "ఢిల్లీ", "दिल्ली", "ਦਿੱਲੀ", "दिल्ली"],
    "Hyderabad": ["hyderabad", "హైదరాబాద్", "హైదరాబాదు", "हैदराबाद", "ਹੈਦਰਾਬਾਦ", "हैद्राबाद"],
    "Mumbai": ["mumbai", "bombay", "ముంబై", "मुंबई", "ਮੁੰਬਈ"],
    "Pune": ["pune", "poona", "పూణే", "పుణె", "पुणे", "ਪੁਣੇ"],
    "Bangalore": ["bangalore", "bengaluru", "బెంగళూరు", "बेंगलुरु", "ਬੈਂਗਲੁਰੂ", "बंगळुरू"],
    "Chennai": ["chennai", "madras", "చెన్నై", "चेन्नई", "ਚੇਨਈ"],
    "Kolkata": ["kolkata", "calcutta", "కోల్‌కతా", "कोलकाता", "ਕੋਲਕਾਤਾ"],
    "Ahmedabad": ["ahmedabad", "అహ్మదాబాద్", "अहमदाबाद", "ਅਹਿਮਦਾਬਾਦ"],
    "Jaipur": ["jaipur", "జైపూర్", "जयपुर", "ਜੈਪੁਰ"],
    "Surat": ["surat", "సూరత్", "सूरत", "ਸੂਰਤ"],
    "Lucknow": ["lucknow", "లక్నో", "लखनऊ", "ਲਖਨਊ"],
    "Nagpur": ["nagpur", "నాగ్‌పూర్", "నాగపూర్", "नागपुर", "ਨਾਗਪੁਰ"],
}


@dataclass
class IntentResult:
    intent: str
    confidence: float
    entities: Dict[str, Any] = field(default_factory=dict)
    original_text: str = ""
    detected_language: str = "en"
    requires_confirmation: bool = False


class VoiceIntentParser:
    """Parses spoken/typed requests in 5 Indian languages into canonical logistics intents."""

    INTENT_KEYWORDS = {
        # ── Plan Trip ──────────────────────────────────────────
        "PLAN_TRIP": [
            "go from", "travel from", "route from", "plan trip", "book trip",
            "నుండి", "వెళ్లాలి", "ప్రయాణం", "వెళ్ళాలి",
            "से", "जाना है", "यात्रा", "ट्रिप प्लान", "रूट",
            "ਤੋਂ", "ਜਾਣਾ ਹੈ", "ਸਫ਼ਰ",
            "ते", "जायचे आहे", "प्रवास",
        ],
        # ── Check ETA & Timing ─────────────────────────────────
        "CHECK_ETA": [
            "when will", "reach", "arrival time", "eta", "how long",
            "ఎప్పుడు చేరుతుంది", "ఎంత సమయం", "చేరుకుంటుంది",
            "कब पहुँचेगा", "कब पहुंचेगा", "कितना समय", "पहुंचने का समय",
            "ਕਦੋਂ ਪਹੁੰਚੇਗਾ", "ਕਿੰਨਾ ਸਮਾਂ",
            "केव्हा पोहोचेल", "किती वेळ",
        ],
        # ── Check Fuel / Range ─────────────────────────────────
        "CHECK_FUEL": [
            "fuel", "diesel", "petrol", "mileage", "fuel level", "how much fuel",
            "డీజిల్", "ఇంధనం", "ఎంత డీజిల్", "ఇంధన స్థాయి",
            "डीजल", "ईंधन", "कितना डीजल", "माइलेज",
            "ਡੀਜ਼ਲ", "ਈਂਧਨ", "ਕਿੰਨਾ ਡੀਜ਼ਲ",
            "डिझेल", "इंधन", "किती डिझेल",
        ],
        # ── Emergency / Breakdown ──────────────────────────────
        "REPORT_BREAKDOWN": [
            "breakdown", "broke down", "engine stopped", "engine failure", "vehicle broken",
            "వాహనం ఆగిపోయింది", "బ్రేక్‌డౌన్", "ఇంజన్ సమస్య",
            "गाड़ी खराब हो गई", "ब्रेकडाउन", "इंजन खराब", "गाड़ी बंद",
            "ਗੱਡੀ ਖਰਾਬ ਹੋ ਗਈ", "ਇੰਜਣ ਬੰਦ",
            "गाडी बंद पडली", "इंजिन बिघाड", "ब्रेकडाऊन",
        ],
        # ── Tyre Puncture ──────────────────────────────────────
        "REPORT_TYRE_PUNCTURE": [
            "puncture", "flat tyre", "tire burst", "flat tire",
            "టైర్ పంక్చర్", "టైర్ పంచర్",
            "टायर पंचर", "टायर पंक्चर", "टायर फट गया",
            "ਟਾਇਰ ਪੰਕਚਰ",
            "टायर पंक्चर", "टायर फुटला",
        ],
        # ── Low Fuel Alert / Station Search ───────────────────
        "FIND_FUEL_STATION": [
            "find fuel station", "nearest fuel", "petrol pump", "diesel bunk", "low fuel",
            "సమీప ఇంధన స్టేషన్", "పెట్రోల్ బంక్", "డీజిల్ బంక్", "ఇంధనం తక్కువ",
            "निकटतम पेट्रोल पंप", "डीजल पंप", "ईंधन कम है", "फ्यूल स्टेशन",
            "ਨੇੜਲਾ ਪੈਟਰੋਲ ਪੰਪ", "ਡੀਜ਼ਲ ਪੰਪ",
            "जवळचे पेट्रोल पंप", "डिझेल पंप", "इंधन संपत आले",
        ],
        # ── Return Cargo / Backhaul ────────────────────────────
        "FIND_RETURN_CARGO": [
            "return load", "return cargo", "backhaul", "empty km", "return trip load",
            "తిరుగు ప్రయాణ లోడ్", "రిటర్న్ కార్గో", "రిటర్న్ లోడ్",
            "वापसी लोड", "रिटर्न कार्गो", "वापसी माल", "खाली किलोमीटर",
            "ਵਾਪਸੀ ਲੋਡ", "ਰਿਟਰਨ ਕਾਰਗੋ",
            "परतीचा माल", "रिटर्न लोड", "परतीचा प्रवास",
        ],
        # ── Check Shipment / Consignment ───────────────────────
        "CHECK_SHIPMENT": [
            "where is my shipment", "track shipment", "consignment", "package status", "order status",
            "నా రవాణా ఎక్కడ", "షిప్‌మెంట్ ఎక్కడ", "ఆర్డర్ స్థితి",
            "मेरा पार्सल कहाँ है", "शिपमेंट ट्रैक", "कंसाइनमेंट कहाँ है", "ऑर्डर स्टेटस",
            "ਮੇਰਾ ਪਾਰਸਲ ਕਿੱਥੇ ਹੈ", "ਸ਼ਿਪਮੈਂਟ ਟਰੈਕ",
            "माझे पार्सल कुठे आहे", "शिपमेंट स्थिती",
        ],
        # ── Fleet Overview / Dashboard ─────────────────────────
        "SHOW_DASHBOARD": [
            "fleet status", "active vehicles", "total vehicles", "how many vehicles", "savings", "overview",
            "ఫ్లీట్ స్థితి", "ఎన్ని వాహనాలు", "మొత్తం ఆదా", "డాష్‌బోర్డ్",
            "फ्लीट स्थिति", "कितने वाहन", "कुल बचत", "डैशबोर्ड", "सक्रिय गाड़ियाँ",
            "ਫਲੀਟ ਸਥਿਤੀ", "ਕੁੱਲ ਵਾਹਨ", "ਬੱਚਤ",
            "फ्लीट स्थिती", "एकूण वाहने", "डॅशबोर्ड",
        ],
        # ── Contact Operator / Emergency Help ──────────────────
        "CONTACT_OPERATOR": [
            "contact operator", "call manager", "help", "emergency", "support",
            "ఆపరేటర్‌ను సంప్రదించండి", "సహాయం", "ఎమర్జెన్సీ",
            "ऑपरेटर से संपर्क", "मदद", "सहायता", "इमरजेंसी",
            "ਮਦਦ", "ਆਪਰੇਟਰ ਨੂੰ ਕਾਲ",
            "मदत", "ऑपरेटरशी संपर्क", "आपत्कालीन",
        ],
    }

    CONFIRMATION_REQUIRED_INTENTS = {
        "PLAN_TRIP",
        "START_TRIP",
        "PAUSE_TRIP",
        "REPORT_BREAKDOWN",
        "REPORT_TYRE_PUNCTURE",
    }

    def detect_language(self, text: str) -> str:
        """Detect language script heuristically."""
        if re.search(r"[\u0C00-\u0C7F]", text):
            return "te"  # Telugu
        if re.search(r"[\u0A00-\u0A7F]", text):
            return "pa"  # Punjabi
        if re.search(r"[\u0900-\u097F]", text):
            # Marathi vs Hindi disambiguation
            if any(w in text.lower() for w in ["आहे", "नाही", "कुठे", "जायचे", "झाला", "कसा"]):
                return "mr"
            return "hi"
        return "en"

    def extract_cities(self, text: str) -> List[str]:
        """Extract matched canonical Indian cities from text."""
        lowered = text.lower()
        found_cities = []

        for canonical, synonyms in CITY_SYNONYMS.items():
            for syn in synonyms:
                pattern = r"\b" + re.escape(syn.lower()) + r"\b"
                if re.search(pattern, lowered) or syn in text:
                    if canonical not in found_cities:
                        found_cities.append(canonical)
                    break
        return found_cities

    def extract_fuel_litres(self, text: str) -> Optional[float]:
        """Extract fuel quantity in litres from text."""
        match = re.search(r"(\d+(?:\.\d+)?)\s*(?:litres?|liters?|ltrs?|l|లీటర్లు|लीटर|ਲੀਟਰ|लिटर)?", text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return None

    def extract_vehicle_id(self, text: str) -> Optional[str]:
        """Extract Indian vehicle registration plate pattern (e.g. MH02AB1234, DL01CD5678)."""
        match = re.search(r"\b([A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{3,4})\b", text.upper().replace(" ", "").replace("-", ""))
        if match:
            return match.group(1)
        return None

    def parse(self, text: str, user_language: Optional[str] = None) -> IntentResult:
        """Parse text into an IntentResult with extracted entities."""
        if not text or not text.strip():
            return IntentResult(
                intent="UNKNOWN",
                confidence=0.0,
                original_text="",
                detected_language=user_language or "en",
            )

        clean_text = text.strip()
        detected_lang = user_language or self.detect_language(clean_text)
        lowered = clean_text.lower()

        # Extract entities
        cities = self.extract_cities(clean_text)
        fuel_qty = self.extract_fuel_litres(clean_text)
        vehicle_reg = self.extract_vehicle_id(clean_text)

        entities: Dict[str, Any] = {}
        if len(cities) >= 2:
            entities["origin"] = cities[0]
            entities["destination"] = cities[1]
        elif len(cities) == 1:
            entities["destination"] = cities[0]

        if fuel_qty is not None and fuel_qty > 0:
            entities["fuel_litres"] = fuel_qty
        if vehicle_reg:
            entities["vehicle_registration"] = vehicle_reg

        # Match intent based on keyword heuristics
        best_intent = "UNKNOWN"
        best_score = 0.0

        for intent_name, keywords in self.INTENT_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw.lower() in lowered or kw in clean_text)
            if matches > 0:
                score = min(0.95, 0.5 + (matches * 0.2))
                if score > best_score:
                    best_score = score
                    best_intent = intent_name

        # If cities were extracted and intent is unknown, classify as PLAN_TRIP
        if best_intent == "UNKNOWN" and len(cities) >= 2:
            best_intent = "PLAN_TRIP"
            best_score = 0.85
        elif best_intent == "UNKNOWN" and len(cities) == 1:
            best_intent = "CHECK_ETA"
            best_score = 0.75

        requires_conf = best_intent in self.CONFIRMATION_REQUIRED_INTENTS

        return IntentResult(
            intent=best_intent,
            confidence=best_score if best_intent != "UNKNOWN" else 0.2,
            entities=entities,
            original_text=clean_text,
            detected_language=detected_lang,
            requires_confirmation=requires_conf,
        )
