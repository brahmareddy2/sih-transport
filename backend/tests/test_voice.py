"""
Unit and Integration Tests for Phase 8: Universal Voice-First & Simple Mode User Experience.
Verifies:
- Language catalog & translations (English, Telugu, Hindi, Punjabi, Marathi)
- Multilingual intent parsing across 5 languages
- Trip planning calculation (Delhi -> Hyderabad: distance, ETA, diesel, tolls, cost)
- Fuel check & low-fuel emergency detection
- Breakdown & incident recovery voice response
- Return cargo search intent
- RBAC permissions & unauthorized voice command rejection
- Voice confirmation pipeline
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.voice.language_service import get_language_service, SUPPORTED_LANGUAGES
from app.services.voice.intent_parser import VoiceIntentParser
from app.services.voice.voice_service import get_voice_service

mock_user = User(
    id=uuid.uuid4(),
    email="test_voice_operator@logistics.in",
    full_name="Voice Test Operator",
    password_hash="test-hash",
    role="operator",
    is_active=True,
)

def mock_get_current_user():
    return mock_user

app.dependency_overrides[get_current_user] = mock_get_current_user
client = TestClient(app)


# ── 1. Language Service Tests ──────────────────────────────────────────────────

def test_language_service_catalogue():
    """Verify 5 Indian languages are registered with valid speech codes."""
    lang_svc = get_language_service()
    languages = lang_svc.get_supported_languages()
    codes = [l["code"] for l in languages]

    assert len(languages) == 5
    assert "en" in codes
    assert "te" in codes
    assert "hi" in codes
    assert "pa" in codes
    assert "mr" in codes

    assert lang_svc.get_speech_code("te") == "te-IN"
    assert lang_svc.get_speech_code("hi") == "hi-IN"
    assert lang_svc.get_speech_code("pa") == "pa-IN"
    assert lang_svc.get_speech_code("mr") == "mr-IN"


def test_language_translations():
    """Verify translation interpolation across multiple languages."""
    lang_svc = get_language_service()

    # English
    en = lang_svc.translate("plan_trip_confirm", lang="en", origin="Delhi", destination="Hyderabad")
    assert "Delhi" in en and "Hyderabad" in en

    # Telugu
    te = lang_svc.translate("plan_trip_confirm", lang="te", origin="Delhi", destination="Hyderabad")
    assert "Delhi" in te and "Hyderabad" in te and "ప్రయాణించాలనుకుంటున్నారని" in te

    # Hindi
    hi = lang_svc.translate("plan_trip_confirm", lang="hi", origin="Delhi", destination="Hyderabad")
    assert "Delhi" in hi and "Hyderabad" in hi and "यात्रा करना चाहते हैं" in hi


# ── 2. Multilingual Intent Parsing Tests ───────────────────────────────────────

def test_multilingual_trip_intent_parsing():
    """Verify trip planning intent recognition in English, Telugu, Hindi, Punjabi, Marathi."""
    parser = VoiceIntentParser()

    # English
    res_en = parser.parse("I want to go from Delhi to Hyderabad")
    assert res_en.intent == "PLAN_TRIP"
    assert res_en.entities.get("origin") == "Delhi"
    assert res_en.entities.get("destination") == "Hyderabad"
    assert res_en.requires_confirmation is True

    # Telugu
    res_te = parser.parse("నేను ఢిల్లీ నుండి హైదరాబాద్ వెళ్ళాలి")
    assert res_te.intent == "PLAN_TRIP"
    assert res_te.entities.get("origin") == "Delhi"
    assert res_te.entities.get("destination") == "Hyderabad"
    assert res_te.detected_language == "te"

    # Hindi
    res_hi = parser.parse("मुझे दिल्ली से हैदराबाद जाना है")
    assert res_hi.intent == "PLAN_TRIP"
    assert res_hi.entities.get("origin") == "Delhi"
    assert res_hi.entities.get("destination") == "Hyderabad"

    # Punjabi
    res_pa = parser.parse("ਮੈਂ ਦਿੱਲੀ ਤੋਂ ਹੈਦਰਾਬਾਦ ਜਾਣਾ ਹੈ")
    assert res_pa.intent == "PLAN_TRIP"
    assert res_pa.entities.get("origin") == "Delhi"
    assert res_pa.entities.get("destination") == "Hyderabad"

    # Marathi
    res_mr = parser.parse("मला दिल्ली ते हैदराबाद प्रवास करायचा आहे")
    assert res_mr.intent == "PLAN_TRIP"
    assert res_mr.entities.get("origin") == "Delhi"
    assert res_mr.entities.get("destination") == "Hyderabad"


def test_fuel_and_eta_intent_parsing():
    """Verify fuel quantity extraction and ETA query parsing."""
    parser = VoiceIntentParser()

    # Fuel query with quantity
    fuel_res = parser.parse("How much fuel is left with 120 litres?")
    assert fuel_res.intent == "CHECK_FUEL"
    assert fuel_res.entities.get("fuel_litres") == 120.0

    # Telugu ETA
    eta_te = parser.parse("నా వాహనం హైదరాబాద్కు ఎప్పుడు చేరుతుంది?")
    assert eta_te.intent == "CHECK_ETA"
    assert eta_te.entities.get("destination") == "Hyderabad"

    # Breakdown report
    breakdown_res = parser.parse("My vehicle broke down on the highway")
    assert breakdown_res.intent == "REPORT_BREAKDOWN"


# ── 3. Voice Service Domain Execution Tests ────────────────────────────────────

def test_trip_planning_calculation():
    """Verify Delhi -> Hyderabad route estimation (distance ~1580km, hours, tolls, fuel)."""
    service = get_voice_service()
    res = service.process_voice_query(
        query="Plan a trip from Delhi to Hyderabad",
        user_role="driver",
        language="en",
        confirmed=True,
        action_payload={"intent": "PLAN_TRIP", "entities": {"origin": "Delhi", "destination": "Hyderabad"}},
    )

    assert res["card_type"] == "TRIP_RESULT"
    card = res["card_data"]
    assert card["origin"] == "Delhi"
    assert card["destination"] == "Hyderabad"
    assert card["distance_km"] > 1000.0
    assert card["fuel_litres"] > 0
    assert card["toll_cost_inr"] > 0
    assert card["total_cost_inr"] > 0
    assert len(card["fuel_stations"]) >= 2


def test_breakdown_recovery_options():
    """Verify voice breakdown reports generate scored recovery options."""
    service = get_voice_service()
    res = service.process_voice_query(
        query="My vehicle broke down",
        user_role="driver",
        language="en",
        confirmed=True,
        action_payload={"intent": "REPORT_BREAKDOWN", "entities": {"vehicle_registration": "MH02AB1234"}},
    )

    assert res["card_type"] == "BREAKDOWN_RECOVERY"
    assert len(res["card_data"]["plans"]) >= 2
    assert res["card_data"]["plans"][0]["score"] > 0


def test_return_cargo_voice_flow():
    """Verify finding return cargo via voice query."""
    service = get_voice_service()
    res = service.process_voice_query(
        query="Find return load from Hyderabad",
        user_role="fleet_manager",
        language="en",
        confirmed=False,
    )

    assert res["card_type"] == "RETURN_CARGO_MATCHES"
    assert len(res["card_data"]["matches"]) >= 1
    assert res["card_data"]["matches"][0]["empty_km_saved"] > 0


# ── 4. Security & RBAC Voice Tests ─────────────────────────────────────────────

def test_voice_rbac_rejection_for_customer():
    """Verify customer cannot trigger operator-only fleet commands."""
    service = get_voice_service()
    res = service.process_voice_query(
        query="Show entire fleet status and active vehicles",
        user_role="customer",
        language="en",
    )

    assert res["is_authorized"] is False
    assert "Access Denied" in res["text"] or "not authorized" in res["text"]


def test_confirmation_pipeline():
    """Verify sensitive actions ask for confirmation before executing."""
    service = get_voice_service()
    res = service.process_voice_query(
        query="Plan trip from Delhi to Hyderabad",
        user_role="driver",
        language="en",
        confirmed=False,
    )

    assert res["requires_confirmation"] is True
    assert res["confirmation_type"] == "PLAN_TRIP"
    assert len(res["options"]) == 2


# ── 5. Voice REST API Endpoints Tests ──────────────────────────────────────────

def test_api_get_languages():
    """Verify GET /api/v1/voice/languages endpoint."""
    resp = client.get("/api/v1/voice/languages")
    assert resp.status_code == 200
    langs = resp.json()
    assert len(langs) == 5


def test_api_voice_intent():
    """Verify POST /api/v1/voice/intent endpoint."""
    resp = client.post(
        "/api/v1/voice/intent",
        json={"text": "I want to go from Delhi to Hyderabad", "language": "en"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "PLAN_TRIP"
    assert data["entities"]["origin"] == "Delhi"


def test_api_voice_command_end_to_end():
    """Verify POST /api/v1/voice/command endpoint end-to-end."""
    resp = client.post(
        "/api/v1/voice/command",
        json={"query": "How much fuel is left in my vehicle?", "language": "en"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["card_type"] == "FUEL_STATUS"
    assert data["card_data"]["fuel_litres"] > 0
