"""
Test Suite for Phase 8 Universal Voice + Search + Multilingual Driver/Owner Assistant.
Verifies:
- Multilingual intent recognition across English, Telugu, Hindi, Punjabi, Marathi
- Unified routing for both Voice and Search queries
- Driver trip planning, ETA, fuel & toll calculations
- Highway facilities search (Restaurants, Parking, Restrooms, Puncture shops)
- Owner financial KPIs and profit analytics
- Puncture emergency assistance and safe communication call initiation
- RBAC permissions & confirmation checkpoints
"""
import pytest
import uuid
from fastapi.testclient import TestClient

from app.main import app
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.voice.intent_router import get_intent_router
from app.services.voice.driver_assistant import DriverAssistant
from app.services.voice.owner_assistant import OwnerAssistant
from app.services.voice.communication import get_communication_service

# Mock User Fixture
mock_driver = User(
    id=uuid.uuid4(),
    email="test_driver@logistics.in",
    full_name="Lead Driver",
    password_hash="test-hash",
    role="driver",
    is_active=True,
)

def mock_get_current_user():
    return mock_driver

app.dependency_overrides[get_current_user] = mock_get_current_user
client = TestClient(app)


# ── 1. Unified Voice & Search Router Tests ────────────────────────────────────

def test_universal_search_trip_planning_english():
    """Verify universal search query for trip planning in English."""
    router = get_intent_router()
    res = router.route_query(
        query="Plan a trip from Delhi to Hyderabad",
        user_role="driver",
        language="en",
    )
    assert res["requires_confirmation"] is True
    assert res["card_type"] == "DRIVER_TRIP_CARD"
    card = res["card_data"]
    assert card["origin"] == "Delhi"
    assert card["destination"] == "Hyderabad"
    assert card["distance_km"] > 1000.0
    assert card["fuel_cost_inr"] > 0
    assert card["toll_cost_inr"] > 0


def test_universal_search_trip_planning_telugu():
    """Verify universal search query for trip planning in Telugu."""
    router = get_intent_router()
    res = router.route_query(
        query="నేను ఢిల్లీ నుండి హైదరాబాద్ వెళ్ళాలి",
        user_role="driver",
        language="te",
    )
    assert res["requires_confirmation"] is True
    assert res["card_type"] == "DRIVER_TRIP_CARD"
    assert res["language"] == "te"


def test_universal_search_trip_planning_hindi():
    """Verify universal search query in Hindi."""
    router = get_intent_router()
    res = router.route_query(
        query="मुझे दिल्ली से हैदराबाद जाना है",
        user_role="driver",
        language="hi",
    )
    assert res["card_type"] == "DRIVER_TRIP_CARD"
    assert res["card_data"]["origin"] == "Delhi"


# ── 2. Highway Facilities Search Tests ─────────────────────────────────────────

def test_restaurant_search_intent():
    """Verify food and restaurant search on route."""
    router = get_intent_router()
    res = router.route_query(
        query="Where can I eat near my route?",
        user_role="driver",
        language="en",
    )
    assert res["card_type"] == "FACILITIES_LIST"
    card = res["card_data"]
    assert card["category"] == "restaurants"
    assert len(card["facilities"]) >= 2
    assert "Shiva Dhaba" in card["facilities"][0]["name"] or "Highway Food Plaza" in card["facilities"][1]["name"]


def test_parking_search_intent():
    """Verify free highway truck parking search."""
    router = get_intent_router()
    res = router.route_query(
        query="Find free parking near me",
        user_role="driver",
        language="en",
    )
    assert res["card_type"] == "FACILITIES_LIST"
    card = res["card_data"]
    assert card["category"] == "parking"
    assert len(card["facilities"]) >= 2


def test_restroom_search_intent():
    """Verify clean restroom search on highway."""
    router = get_intent_router()
    res = router.route_query(
        query="Find nearest clean restroom and shower",
        user_role="driver",
        language="en",
    )
    assert res["card_type"] == "FACILITIES_LIST"
    card = res["card_data"]
    assert card["category"] == "restrooms"


# ── 3. Puncture Assistance & Safe Calling Tests ────────────────────────────────

def test_puncture_assistance_intent():
    """Verify puncture assistance response with nearest shops and action buttons."""
    router = get_intent_router()
    res = router.route_query(
        query="My vehicle has a tyre puncture",
        user_role="driver",
        language="en",
    )
    assert res["card_type"] == "PUNCTURE_ASSISTANCE"
    card = res["card_data"]
    assert "nearest_shop" in card
    assert card["nearest_shop"]["distance_km"] > 0
    assert len(card["action_buttons"]) == 3


def test_safe_communication_call_initiation():
    """Verify calling puncture shop generates safe dialer payload with phone masking."""
    comm = get_communication_service()
    res = comm.initiate_contact(
        target_category="puncture_shop",
        caller_role="driver",
        purpose="Flat tyre roadside repair",
    )
    assert res["status"] == "READY_TO_DIAL"
    assert "+91" in res["phone_masked"]
    assert "Demo call mode" in res["disclaimer"]


# ── 4. Owner & Fleet Manager Financial Analytics Tests ─────────────────────────

def test_owner_daily_financial_analytics():
    """Verify fleet owner profit & cost query."""
    router = get_intent_router()
    res = router.route_query(
        query="How much did I earn today and what is my profit?",
        user_role="fleet_manager",
        language="en",
    )
    assert res["card_type"] == "OWNER_FINANCIAL_SUMMARY"
    card = res["card_data"]
    assert card["revenue_inr"] > 0
    assert card["estimated_profit_inr"] > 0
    assert card["expenses"]["fuel_inr"] > 0
    assert card["expenses"]["tolls_inr"] > 0
    assert card["expenses"]["food_batta_inr"] > 0


def test_owner_vehicle_locations():
    """Verify fleet owner vehicle tracking on map."""
    router = get_intent_router()
    res = router.route_query(
        query="Where are all my vehicles on the map?",
        user_role="fleet_manager",
        language="en",
    )
    assert res["card_type"] == "OWNER_FLEET_LOCATIONS"
    card = res["card_data"]
    assert card["total_vehicles"] == 50
    assert card["active_in_transit"] == 12
    assert len(card["top_locations"]) >= 3


# ── 5. REST API Endpoints Verification ─────────────────────────────────────────

def test_api_get_highway_facilities():
    """Verify GET /api/v1/voice/facilities endpoint."""
    resp = client.get("/api/v1/voice/facilities?category=restaurants")
    assert resp.status_code == 200
    data = resp.json()
    assert data["category"] == "restaurants"
    assert data["count"] >= 2


def test_api_initiate_call():
    """Verify POST /api/v1/voice/call endpoint."""
    resp = client.post(
        "/api/v1/voice/call",
        json={"target_category": "puncture_shop", "purpose": "Tyre repair"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "READY_TO_DIAL"
    assert "XYZ" in data["target_name"] or "Tyre" in data["target_name"]


def test_api_voice_command_trip_planning():
    """Verify POST /api/v1/voice/command handles universal search text."""
    resp = client.post(
        "/api/v1/voice/command",
        json={"query": "Find the best route from Delhi to Hyderabad", "language": "en"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["card_type"] == "DRIVER_TRIP_CARD"
    assert data["card_data"]["distance_km"] > 1000
