"""
Automated Test Suite for Universal Logistics Assistant & Intent Engine
Validates:
- Multilingual intent classification (Telugu, Hindi, Punjabi, Marathi, English)
- Trip planning calculations (Delhi -> Hyderabad: distance, duration, fuel, tolls, food, total cost)
- Fuel available subtraction and remaining litres
- Itemized toll costs along NH44 corridor
- Food budget daily calculation
- Puncture & Breakdown assistance with direct calling hook
- Highway facilities search (restaurants, parking, restrooms)
- Vehicle location & fleet map queries
- Owner profit & expense analytics with data_source tags
- Strict RBAC enforcement (driver blocked from viewing company financials)
- Return trip reminders
- Assistant API endpoints (/api/v1/assistant/query, /api/v1/assistant/trip-plan)
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.assistant.intent_engine import AssistantIntentEngine, get_assistant_intent_engine
from app.services.assistant.location_provider import get_location_provider

_mock_admin = User(
    id=__import__("uuid").UUID("00000000-0000-0000-0000-000000000099"),
    email="assistant_admin@example.com",
    full_name="Assistant Admin",
    password_hash="test-hash",
    role="admin",
    is_active=True,
)

def mock_get_current_user():
    return _mock_admin

app.dependency_overrides[get_current_user] = mock_get_current_user
client = TestClient(app)


@pytest.fixture
def engine():
    return get_assistant_intent_engine()


# ── 1. Multilingual Intent Classification Tests ─────────────────────────────

def test_multilingual_trip_planning_intents(engine):
    """Verify all 5 languages correctly classify TRIP_PLANNING intent."""
    test_cases = [
        ("ఢిల్లీ నుండి హైదరాబాద్ వెళ్లాలి", "te", "TRIP_PLANNING"),
        ("నేను ఢిల్లీ నుండి హైదరాబాద్ వెళ్ళాలి", "te", "TRIP_PLANNING"),
        ("दिल्ली से हैदराबाद जाना है", "hi", "TRIP_PLANNING"),
        ("ਮੈਨੂੰ ਦਿੱਲੀ ਤੋਂ ਹੈਦਰਾਬਾਦ ਜਾਣਾ ਹੈ", "pa", "TRIP_PLANNING"),
        ("मला दिल्लीहून हैदराबादला जायचे आहे", "mr", "TRIP_PLANNING"),
        ("I want to travel from Delhi to Hyderabad", "en", "TRIP_PLANNING"),
        ("Route from Delhi to Hyderabad", "en", "TRIP_PLANNING"),
    ]
    for query, expected_lang, expected_intent in test_cases:
        res = engine.process_query(query=query, user_role="driver")
        assert res["intent"] == expected_intent, f"Failed for query: {query}"
        assert res["data"]["distance_km"] > 1000
        assert res["data"]["total_cost_inr"] > 0


def test_puncture_assistance_intent(engine):
    """Verify puncture assistance is triggered in Telugu and English."""
    res_te = engine.process_query(query="నా లారీ పంక్చర్ అయ్యింది", user_role="driver")
    assert res_te["intent"] == "PUNCTURE_HELP"
    assert "nearest_shop" in res_te["data"]
    assert res_te["data"]["nearest_shop"]["phone"] != ""
    assert any("tel:" in a.get("target", "") for a in res_te["actions"])

    res_en = engine.process_query(query="My truck tire is punctured on highway", user_role="driver")
    assert res_en["intent"] == "PUNCTURE_HELP"


def test_owner_profit_intent(engine):
    """Verify profit query in Telugu and English for owner role."""
    res_te = engine.process_query(query="ఈరోజు నా లాభం ఎంత?", user_role="owner")
    assert res_te["intent"] == "PROFIT_QUERY"
    assert res_te["is_authorized"] is True
    assert "revenue_inr" in res_te["data"]
    assert res_te["data"]["estimated_profit_inr"] > 0

    res_en = engine.process_query(query="Today's profit and revenue", user_role="owner")
    assert res_en["intent"] == "PROFIT_QUERY"
    assert res_en["data_source"] in ["database", "demo"]


def test_vehicle_location_intent(engine):
    """Verify fleet vehicle location map query."""
    res_te = engine.process_query(query="నా వాహనాలు ఎక్కడ ఉన్నాయి?", user_role="fleet_manager")
    assert res_te["intent"] == "VEHICLE_LOCATION"
    assert res_te["is_authorized"] is True
    assert "total_vehicles" in res_te["data"]
    assert res_te["data"]["total_vehicles"] > 0


def test_food_search_intent(engine):
    """Verify highway dhaba search in Telugu and English."""
    res_te = engine.process_query(query="దగ్గరలో మంచి రెస్టారెంట్", user_role="driver")
    assert res_te["intent"] == "FOOD_SEARCH"
    assert len(res_te["data"]["facilities"]) > 0

    res_en = engine.process_query(query="Best restaurant near me on highway", user_role="driver")
    assert res_en["intent"] == "FOOD_SEARCH"


# ── 2. Trip Calculations (Fuel, Tolls, Food, Total Cost) ───────────────────

def test_trip_planning_financial_calculations(engine):
    """Verify Delhi -> Hyderabad complete cost breakdown."""
    plan = engine.process_query(
        query="Delhi to Hyderabad",
        user_role="driver",
        current_fuel_l=150.0,
        food_budget_inr=400.0,
    )
    data = plan["data"]
    assert data["distance_km"] == 1580.0
    assert data["duration_hours"] == 26.5
    assert data["duration_days"] == 2.0

    # Fuel checks: 1580 km @ 4 km/L = 395 L. Current = 150 L. Buy = 245 L.
    assert data["fuel_required_l"] == 395.0
    assert data["fuel_to_buy_l"] == 245.0
    assert data["fuel_cost_inr"] == 37525  # 395 * 95

    # Toll checks: 6 toll plazas = ₹2,850
    assert data["toll_cost_inr"] == 2850
    assert len(data["toll_plazas"]) >= 6

    # Food checks: 2 days @ ₹400 = ₹800
    assert data["food_cost_inr"] == 800

    # Total cost = 37525 + 2850 + 800 + 1925 = 43500
    assert data["total_cost_inr"] == 43500
    assert data["cost_per_km_inr"] == 27.53
    assert data["est_net_profit_inr"] == (65000 - 43500)

    # Route options must contain 3 distinct routes
    assert len(data["route_options"]) == 3
    assert data["route_options"][0]["id"] == "best_route"
    assert data["route_options"][1]["id"] == "fastest_route"
    assert data["route_options"][2]["id"] == "lowest_cost_route"


# ── 3. RBAC Enforcement Tests ───────────────────────────────────────────────

def test_rbac_driver_denied_profit_queries(engine):
    """Verify commercial drivers are rejected from accessing company financials."""
    res = engine.process_query(query="Show all company profits", user_role="driver", language="en")
    assert res["is_authorized"] is False
    assert "Unauthorized" in res["message"]

    res_te = engine.process_query(query="ఈరోజు నా లాభం ఎంత?", user_role="driver", language="te")
    assert res_te["is_authorized"] is False
    assert "అనుమతి లేదు" in res_te["message"]


def test_rbac_owner_allowed_profit_queries(engine):
    """Verify owner and fleet manager can access profit data."""
    res_owner = engine.process_query(query="Today's profit", user_role="owner")
    assert res_owner["is_authorized"] is True
    assert res_owner["intent"] == "PROFIT_QUERY"

    res_fleet = engine.process_query(query="How much did I spend today?", user_role="fleet_manager")
    assert res_fleet["is_authorized"] is True


# ── 4. Return Trip & Facilities Tests ───────────────────────────────────────

def test_return_trip_reminder(engine):
    """Verify return trip cargo search query."""
    res = engine.process_query(query="Check return load", user_role="driver")
    assert res["intent"] == "RETURN_TRIP"
    assert res["data"]["potential_revenue_inr"] > 0
    assert res["data"]["empty_km_reduced"] > 0


def test_parking_and_restroom_search(engine):
    """Verify parking and restroom amenities search."""
    res_park = engine.process_query(query="Free truck parking on highway", user_role="driver")
    assert res_park["intent"] == "PARKING_SEARCH"
    assert len(res_park["data"]["facilities"]) > 0

    res_wc = engine.process_query(query="Clean restroom and washroom", user_role="driver")
    assert res_wc["intent"] == "RESTROOM_SEARCH"
    assert len(res_wc["data"]["facilities"]) > 0


# ── 5. Assistant API Endpoints Integration Tests ────────────────────────────

def test_api_assistant_query_endpoint():
    """Verify POST /api/v1/assistant/query endpoint."""
    resp = client.post(
        "/api/v1/assistant/query",
        json={"query": "Delhi to Hyderabad route", "language": "en", "current_fuel_l": 150.0},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "TRIP_PLANNING"
    assert data["data"]["distance_km"] == 1580.0
    assert data["data"]["total_cost_inr"] == 43500


def test_api_assistant_trip_plan_endpoint():
    """Verify GET /api/v1/assistant/trip-plan endpoint."""
    resp = client.get(
        "/api/v1/assistant/trip-plan?origin=Delhi&destination=Hyderabad&current_fuel_l=150&food_budget_inr=400&language=te"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "TRIP_PLANNING"
    assert data["data"]["toll_cost_inr"] == 2850
    assert data["data"]["data_source"] == "database"
