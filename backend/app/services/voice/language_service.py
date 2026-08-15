"""
Language Service — Phase 8
Manages Indian languages, translation dictionaries, localized response templates,
and Speech Synthesis language identifiers.

Supported Languages:
- en: English (en-IN)
- te: Telugu / తెలుగు (te-IN)
- hi: Hindi / हिन्दी (hi-IN)
- pa: Punjabi / ਪੰਜਾਬੀ (pa-IN)
- mr: Marathi / मराठी (mr-IN)
"""
from typing import Dict, List, Optional

SUPPORTED_LANGUAGES = [
    {
        "code": "en",
        "name": "English",
        "native_name": "English",
        "speech_code": "en-IN",
        "flag": "🌐",
    },
    {
        "code": "te",
        "name": "Telugu",
        "native_name": "తెలుగు",
        "speech_code": "te-IN",
        "flag": "🇮🇳",
    },
    {
        "code": "hi",
        "name": "Hindi",
        "native_name": "हिन्दी",
        "speech_code": "hi-IN",
        "flag": "🇮🇳",
    },
    {
        "code": "pa",
        "name": "Punjabi",
        "native_name": "ਪੰਜਾਬੀ",
        "speech_code": "pa-IN",
        "flag": "🇮🇳",
    },
    {
        "code": "mr",
        "name": "Marathi",
        "native_name": "मराठी",
        "speech_code": "mr-IN",
        "flag": "🇮🇳",
    },
]

# ── Multilingual Translation Dictionary ───────────────────────────────────────
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # ── Greetings & General Prompts ────────────────────────────
    "listening": {
        "en": "Listening...",
        "te": "వింటున్నాను...",
        "hi": "सुन रहा हूँ...",
        "pa": "ਸੁਣ ਰਿਹਾ ਹਾਂ...",
        "mr": "ऐकत आहे...",
    },
    "i_understood": {
        "en": "I understood: {text}",
        "te": "నేను అర్థం చేసుకున్నాను: {text}",
        "hi": "मैंने समझा: {text}",
        "pa": "ਮੈਂ ਸਮਝਿਆ: {text}",
        "mr": "मला समजले: {text}",
    },
    "is_this_correct": {
        "en": "Is this correct?",
        "te": "ఇది సరైనదేనా?",
        "hi": "क्या यह सही है?",
        "pa": "ਕੀ ਇਹ ਸਹੀ ਹੈ?",
        "mr": "हे बरोबर आहे का?",
    },
    "yes": {
        "en": "Yes",
        "te": "అవును",
        "hi": "हाँ",
        "pa": "ਹਾਂ",
        "mr": "होय",
    },
    "no": {
        "en": "No",
        "te": "కాదు",
        "hi": "नहीं",
        "pa": "ਨਹੀਂ",
        "mr": "नाही",
    },
    "did_not_understand": {
        "en": "I didn't understand. Please say that again or type your request.",
        "te": "నాకు అర్థం కాలేదు. దయచేసి మళ్ళీ చెప్పండి లేదా టైప్ చేయండి.",
        "hi": "मुझे समझ नहीं आया। कृपया दोबारा बोलें या टाइप करें।",
        "pa": "ਮੈਨੂੰ ਸਮਝ ਨਹੀਂ ਆਇਆ। ਕਿਰਪਾ ਕਰਕੇ ਦੁਬਾਰਾ ਬੋਲੋ ਜਾਂ ਟਾਈਪ ਕਰੋ।",
        "mr": "मला समजले नाही. कृपया पुन्हा बोला किंवा टाईप करा.",
    },
    "voice_unavailable": {
        "en": "Voice is unavailable. You can type your request.",
        "te": "వాయిస్ అందుబాటులో లేదు. మీరు మీ అభ్యర్థనను టైప్ చేయవచ్చు.",
        "hi": "आवाज़ अनुपलब्ध है। आप अपना अनुरोध टाइप कर सकते हैं।",
        "pa": "ਆਵਾਜ਼ ਉਪਲਬਧ ਨਹੀਂ ਹੈ। ਤੁਸੀਂ ਆਪਣੀ ਬੇਨਤੀ ਟਾਈਪ ਕਰ ਸਕਦੇ ਹੋ।",
        "mr": "व्हॉइस उपलब्ध नाही. तुम्ही तुमची विनंती टाईप करू शकता.",
    },

    # ── Trip Planning ──────────────────────────────────────────
    "plan_trip_confirm": {
        "en": "I understood that you want to travel from {origin} to {destination}. Is that correct?",
        "te": "మీరు {origin} నుండి {destination} కు ప్రయాణించాలనుకుంటున్నారని నేను అర్థం చేసుకున్నాను. ఇది సరైనదేనా?",
        "hi": "मैंने समझा कि आप {origin} से {destination} तक यात्रा करना चाहते हैं। क्या यह सही है?",
        "pa": "ਮੈਂ ਸਮਝਿਆ ਕਿ ਤੁਸੀਂ {origin} ਤੋਂ {destination} ਤੱਕ ਜਾਣਾ ਚਾਹੁੰਦੇ ਹੋ। ਕੀ ਇਹ ਸਹੀ ਹੈ?",
        "mr": "मला समजले की तुम्हाला {origin} ते {destination} प्रवास करायचा आहे. हे बरोबर आहे का?",
    },
    "ask_fuel_level": {
        "en": "How much diesel is currently available in your vehicle?",
        "te": "మీ వాహనంలో ప్రస్తుతం ఎంత డీజిల్ అందుబాటులో ఉంది?",
        "hi": "आपके वाहन में वर्तमान में कितना डीजल उपलब्ध है?",
        "pa": "ਤੁਹਾਡੇ ਵਾਹਨ ਵਿੱਚ ਇਸ ਸਮੇਂ ਕਿੰਨਾ ਡੀਜ਼ਲ ਉਪਲਬਧ ਹੈ?",
        "mr": "तुमच्या वाहनात सध्या किती डिझेल उपलब्ध आहे?",
    },
    "trip_calculated_summary": {
        "en": "Trip from {origin} to {destination}: Distance ~{distance_km} km, Driving time ~{hours} hours ({days} days), Diesel ~{fuel_litres} L (₹{fuel_cost}), Toll ~₹{toll_cost}. Total estimated cost: ₹{total_cost}.",
        "te": "{origin} నుండి {destination} ట్రిప్: దూరం ~{distance_km} కి.మీ, ప్రయాణ సమయం ~{hours} గంటలు ({days} రోజులు), డీజిల్ ~{fuel_litres} లీటర్లు (₹{fuel_cost}), టోల్ ~₹{toll_cost}. మొత్తం అంచనా వ్యయం: ₹{total_cost}.",
        "hi": "{origin} से {destination} की यात्रा: दूरी ~{distance_km} किमी, यात्रा समय ~{hours} घंटे ({days} दिन), डीजल ~{fuel_litres} लीटर (₹{fuel_cost}), टोल ~₹{toll_cost}। कुल अनुमानित लागत: ₹{total_cost}।",
        "pa": "{origin} ਤੋਂ {destination} ਦਾ ਸਫ਼ਰ: ਦੂਰੀ ~{distance_km} ਕਿਲੋਮੀਟਰ, ਸਮਾਂ ~{hours} ਘੰਟੇ ({days} ਦਿਨ), ਡੀਜ਼ਲ ~{fuel_litres} ਲੀਟਰ (₹{fuel_cost}), ਟੋਲ ~₹{toll_cost}। ਕੁੱਲ ਅਨੁਮਾਨਿਤ ਲਾਗਤ: ₹{total_cost}।",
        "mr": "{origin} ते {destination} प्रवास: अंतर ~{distance_km} किमी, वेळ ~{hours} तास ({days} दिवस), डिझेल ~{fuel_litres} लिटर (₹{fuel_cost}), टोल ~₹{toll_cost}. एकूण अंदाजे खर्च: ₹{total_cost}.",
    },

    # ── Status & Telematics ────────────────────────────────────
    "eta_response": {
        "en": "Your vehicle {vehicle} will reach {destination} in approximately {hours} hours ({eta_time}).",
        "te": "మీ వాహనం {vehicle} సుమారు {hours} గంటల్లో ({eta_time}) {destination}కు చేరుకుంటుంది.",
        "hi": "आपका वाहन {vehicle} लगभग {hours} घंटे ({eta_time}) में {destination} पहुँच जाएगा।",
        "pa": "ਤੁਹਾਡਾ ਵਾਹਨ {vehicle} ਲਗਭਗ {hours} ਘੰਟਿਆਂ ਵਿੱਚ ({eta_time}) {destination} ਪਹੁੰਚ ਜਾਵੇਗਾ।",
        "mr": "तुमचे वाहन {vehicle} साधारण {hours} तासांत ({eta_time}) {destination} ला पोहोचेल.",
    },
    "delay_warning": {
        "en": "Traffic congestion detected. Expect approximately {delay_hours} hours delay.",
        "te": "ట్రాఫిక్ రద్దీ గుర్తించబడింది. సుమారు {delay_hours} గంటల ఆలస్యం కావచ్చు.",
        "hi": "यातायात भीड़ का पता चला है। लगभग {delay_hours} घंटे की देरी होने की संभावना है।",
        "pa": "ਟ੍ਰੈਫਿਕ ਜਾਮ ਹੈ। ਲਗਭਗ {delay_hours} ਘੰਟੇ ਦੀ ਦੇਰੀ ਹੋ ਸਕਦੀ ਹੈ।",
        "mr": "वाहतूक कोंडी आढळली. साधारण {delay_hours} तास उशीर होऊ शकतो.",
    },
    "fuel_status": {
        "en": "Current fuel level is {fuel_litres} L ({fuel_pct}%). Remaining driving range is approximately {range_km} km.",
        "te": "ప్రస్తుత ఇంధన స్థాయి {fuel_litres} లీటర్లు ({fuel_pct}%). మిగిలిన డ్రైవింగ్ దూరం సుమారు {range_km} కి.మీ.",
        "hi": "वर्तमान ईंधन स्तर {fuel_litres} लीटर ({fuel_pct}%) है। शेष ड्राइविंग रेंज लगभग {range_km} किमी है।",
        "pa": "ਮੌਜੂਦਾ ਈਂਧਨ ਪੱਧਰ {fuel_litres} ਲੀਟਰ ({fuel_pct}%) ਹੈ। ਬਾਕੀ ਡਰਾਈਵਿੰਗ ਰੇਂਜ ਲਗਭਗ {range_km} ਕਿਲੋਮੀਟਰ ਹੈ।",
        "mr": "सध्याची इंधन पातळी {fuel_litres} लिटर ({fuel_pct}%) आहे. उर्वरित ड्रायव्हिंग रेंज सुमारे {range_km} किमी आहे.",
    },

    # ── Low Fuel & Emergency ───────────────────────────────────
    "low_fuel_alert": {
        "en": "Warning: Fuel is critically low ({fuel_pct}%). Would you like me to find the nearest suitable fuel station?",
        "te": "హెచ్చరిక: ఇంధనం చాలా తక్కువగా ఉంది ({fuel_pct}%). సమీపంలోని అనువైన ఇంధన స్టేషన్‌ను కనుగొనమంటారా?",
        "hi": "चेतावनी: ईंधन बहुत कम है ({fuel_pct}%)। क्या आप चाहते हैं कि मैं निकटतम उपयुक्त ईंधन स्टेशन खोजूँ?",
        "pa": "ਚੇਤਾਵਨੀ: ਈਂਧਨ ਬਹੁਤ ਘੱਟ ਹੈ ({fuel_pct}%)। ਕੀ ਤੁਸੀਂ ਨੇੜਲੇ ਈਂਧਨ ਸਟੇਸ਼ਨ ਦੀ ਖੋਜ ਚਾਹੁੰਦੇ ਹੋ?",
        "mr": "इशारा: इंधन खूप कमी आहे ({fuel_pct}%). जवळचे योग्य इंधन स्टेशन शोधू का?",
    },
    "fuel_station_found": {
        "en": "Nearest Fuel Station: {station_name}, {distance_km} km away ({detour_min} min detour). Estimated fuel cost: ₹{estimated_cost}.",
        "te": "సమీప ఇంధన స్టేషన్: {station_name}, {distance_km} కి.మీ దూరంలో ({detour_min} నిమిషాల ప్రయాణం). అంచనా ఇంధన వ్యయం: ₹{estimated_cost}.",
        "hi": "निकटतम ईंधन स्टेशन: {station_name}, {distance_km} किमी दूर ({detour_min} मिनट का चक्कर)। अनुमानित ईंधन लागत: ₹{estimated_cost}।",
        "pa": "ਨੇੜਲਾ ਈਂਧਨ ਸਟੇਸ਼ਨ: {station_name}, {distance_km} ਕਿਲੋਮੀਟਰ ਦੂਰ ({detour_min} ਮਿੰਟ ਦਾ ਚੱਕਰ)। ਅਨੁਮਾਨਿਤ ਈਂਧਨ ਲਾਗਤ: ₹{estimated_cost}।",
        "mr": "जवळचे इंधन स्टेशन: {station_name}, {distance_km} किमी अंतरावर ({detour_min} मिनिटांचा वळसा). अंदाजे इंधन खर्च: ₹{estimated_cost}.",
    },
    "breakdown_help": {
        "en": "Don't worry. I am helping you. I have identified vehicle {vehicle} at {location} and found {plan_count} AI recovery options for your operator to approve.",
        "te": "చింతించకండి. నేను మీకు సహాయం చేస్తున్నాను. నేను {location} వద్ద వాహనం {vehicle} ను గుర్తించాను మరియు మీ ఆపరేటర్ ఆమోదం కోసం {plan_count} AI రికవరీ ఎంపికలను కనుగొన్నాను.",
        "hi": "चिंता मत कीजिए। मैं आपकी सहायता कर रहा हूँ। मैंने {location} पर वाहन {vehicle} की पहचान की है और ऑपरेटर की स्वीकृति के लिए {plan_count} AI रिकवरी विकल्प तैयार किए हैं।",
        "pa": "ਚਿੰਤਾ ਨਾ ਕਰੋ। ਮੈਂ ਤੁਹਾਡੀ ਮਦਦ ਕਰ ਰਿਹਾ ਹਾਂ। ਮੈਂ {location} ਤੇ ਵਾਹਨ {vehicle} ਦੀ ਪਛਾਣ ਕੀਤੀ ਹੈ ਅਤੇ ਆਪਰੇਟਰ ਦੀ ਮਨਜ਼ੂਰੀ ਲਈ {plan_count} ਰਿਕਵਰੀ ਵਿਕਲਪ ਤਿਆਰ ਕੀਤੇ ਹਨ।",
        "mr": "काळजी करू नका. मी तुम्हाला मदत करत आहे. मी {location} येथे वाहन {vehicle} ओळखले आहे आणि ऑपरेटरच्या मंजुरीसाठी {plan_count} AI रिकव्हरी पर्याय तयार केले आहेत.",
    },

    # ── Return Trip Cargo ──────────────────────────────────────
    "return_trip_prompt": {
        "en": "Your trip to {destination} is almost complete. Would you like to check compatible return cargo to reduce empty kilometers?",
        "te": "{destination} కు మీ ట్రిప్ దాదాపు పూర్తయింది. ఖాళీ కిలోమీటర్లను తగ్గించడానికి అనువైన తిరుగు ప్రయాణ లోడ్‌ను తనిఖీ చేయమంటారా?",
        "hi": "{destination} की आपकी यात्रा लगभग पूरी हो गई है। क्या आप खाली किलोमीटर कम करने के लिए वापसी कार्गो लोड देखना चाहते हैं?",
        "pa": "{destination} ਦਾ ਤੁਹਾਡਾ ਸਫ਼ਰ ਲਗਭਗ ਪੂਰਾ ਹੋ ਗਿਆ ਹੈ। ਕੀ ਤੁਸੀਂ ਖਾਲੀ ਕਿਲੋਮੀਟਰ ਘਟਾਉਣ ਲਈ ਵਾਪਸੀ ਕਾਰਗੋ ਲੋਡ ਦੇਖਣਾ ਚਾਹੁੰਦੇ ਹੋ?",
        "mr": "{destination} चा तुमचा प्रवास जवळजवळ पूर्ण झाला आहे. रिकामे किलोमीटर कमी करण्यासाठी परतीचा माल तपासू का?",
    },
    "return_cargo_found": {
        "en": "Found {count} return cargo options from {destination}. Top match saves {km_saved} empty-km and earns approximately ₹{benefit}.",
        "te": "{destination} నుండి {count} తిరుగు ప్రయాణ కార్గో ఎంపికలు కనుగొనబడ్డాయి. అగ్ర మ్యాచ్ {km_saved} ఖాళీ కి.మీలను ఆదా చేస్తుంది మరియు సుమారు ₹{benefit} సంపాదిస్తుంది.",
        "hi": "{destination} से {count} वापसी कार्गो विकल्प मिले। शीर्ष मैच {km_saved} खाली किमी बचाता है और लगभग ₹{benefit} की बचत कराता है।",
        "pa": "{destination} ਤੋਂ {count} ਵਾਪਸੀ ਕਾਰਗੋ ਵਿਕਲਪ ਮਿਲੇ। ਸਿਖਰਲਾ ਮੈਚ {km_saved} ਖਾਲੀ ਕਿਲੋਮੀਟਰ ਬਚਾਉਂਦਾ ਹੈ ਅਤੇ ਲਗਭਗ ₹{benefit} ਲਾਭ ਦਿੰਦਾ ਹੈ।",
        "mr": "{destination} वरून {count} परतीचे माल पर्याय सापडले. सर्वोत्तम मॅच {km_saved} रिकामे किमी वाचवते आणि सुमारे ₹{benefit} चा फायदा मिळवून देते.",
    },

    # ── Role & Fleet Stats ─────────────────────────────────────
    "fleet_overview": {
        "en": "Fleet Status: {total} total vehicles, {active} in transit, {idle} available, {incidents} active incidents, and ₹{savings} total cost savings.",
        "te": "ఫ్లీట్ స్థితి: మొత్తం {total} వాహనాలు, {active} ప్రయాణంలో ఉన్నాయి, {idle} అందుబాటులో ఉన్నాయి, {incidents} సక్రియ సంఘటనలు, మరియు ₹{savings} మొత్తం ఖర్చు ఆదా.",
        "hi": "फ्लीट स्थिति: कुल {total} वाहन, {active} ट्रांजिट में, {idle} उपलब्ध, {incidents} सक्रिय घटनाएं, और ₹{savings} कुल बचत।",
        "pa": "ਫਲੀਟ ਸਥਿਤੀ: ਕੁੱਲ {total} ਵਾਹਨ, {active} ਚਲ ਰਹੇ ਹਨ, {idle} ਉਪਲਬਧ, {incidents} ਸਰਗਰਮ ਘਟਨਾਵਾਂ, ਅਤੇ ₹{savings} ਕੁੱਲ ਬੱਚਤ।",
        "mr": "फ्लीट स्थिती: एकूण {total} वाहने, {active} मार्गावर, {idle} उपलब्ध, {incidents} सक्रिय घटना, आणि ₹{savings} एकूण बचत.",
    },
    "unauthorized_command": {
        "en": "Access Denied: Your role ({role}) is not authorized to execute this voice command.",
        "te": "ప్రాప్యత నిరాకరించబడింది: ఈ వాయిస్ కమాండ్‌ను అమలు చేయడానికి మీ పాత్రకు ({role}) అనుమతి లేదు.",
        "hi": "पहुंच अस्वीकृत: आपकी भूमिका ({role}) इस वॉयस कमांड को निष्पादित करने के लिए अधिकृत नहीं है।",
        "pa": "ਪਹੁੰਚ ਤੋਂ ਇਨਕਾਰ: ਤੁਹਾਡੀ ਭੂਮਿਕਾ ({role}) ਨੂੰ ਇਹ ਵੌਇਸ ਕਮਾਂਡ ਚਲਾਉਣ ਦਾ ਅਧਿਕਾਰ ਨਹੀਂ ਹੈ।",
        "mr": "प्रवेश नाकारला: तुमची भूमिका ({role}) हा व्हॉइस आदेश चालवण्यासाठी अधिकृत नाही.",
    },
}


class LanguageService:
    """Provides translation and localization for all supported Indian languages."""

    @staticmethod
    def get_supported_languages() -> List[Dict]:
        return SUPPORTED_LANGUAGES

    @staticmethod
    def get_speech_code(language_code: str) -> str:
        """Return BCP-47 speech recognition code (e.g. te-IN)."""
        lang = next((l for l in SUPPORTED_LANGUAGES if l["code"] == language_code.lower()), None)
        return lang["speech_code"] if lang else "en-IN"

    @staticmethod
    def translate(key: str, lang: str = "en", **kwargs) -> str:
        """Translate a template key to target language with keyword interpolation."""
        lang_code = (lang or "en").lower().split("-")[0]
        entry = TRANSLATIONS.get(key, {})
        template = entry.get(lang_code) or entry.get("en") or key

        try:
            return template.format(**kwargs)
        except Exception:
            return template


_language_service_instance: Optional[LanguageService] = None


def get_language_service() -> LanguageService:
    global _language_service_instance
    if _language_service_instance is None:
        _language_service_instance = LanguageService()
    return _language_service_instance
