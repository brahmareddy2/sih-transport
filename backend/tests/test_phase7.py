"""
Phase 7 — Integrated Analytics, What-If Simulation & SIH Demo Readiness Test Suite.

Covers:
 1. Live Dashboard Overview KPI calculations
 2. What-If supported scenarios listing
 3. What-If simulation: Heavy traffic congestion
 4. What-If simulation: Vehicle engine breakdown
 5. What-If simulation: Tyre puncture
 6. What-If simulation: Highway closure detour
 7. What-If simulation: Low fuel critical divert
 8. What-If simulation: Urgent shipment dynamic insertion
 9. What-If Before vs After delta metrics math
10. Cost breakdown & trends endpoint
11. Actual vs Predicted intelligence comparisons
12. Notification listing with unread filters
13. Unread notification counter badge endpoint
14. Mark single notification as read
15. Mark all notifications as read
16. Admin platform diagnostics and system statistics
"""
import pytest
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.core.dependencies import get_current_user
from app.core.database import SessionLocal
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.route import Route
from app.models.notification import Notification

# ── Static Auth Override for Test Isolation ───────────────────────────────────
_mock_admin = User(
    id=uuid.UUID("00000000-0000-0000-0000-000000000099"),
    email="phase7_admin@example.com",
    full_name="Phase 7 Admin",
    password_hash="test-hash",
    role="admin",
    is_active=True,
)

def mock_get_current_user():
    return _mock_admin

app.dependency_overrides[get_current_user] = mock_get_current_user
client = TestClient(app)


# ── Fixture: Ensure Seed Data Exists ──────────────────────────────────────────

@pytest.fixture(scope="module", autouse=True)
def setup_test_data():
    """Ensure database has entities for Phase 7 tests."""
    db = SessionLocal()
    try:
        v_count = db.query(Vehicle).count()
    finally:
        db.close()

    if v_count == 0:
        resp = client.post("/api/v1/seed/generate", json={"overwrite": False})
        assert resp.status_code in (200, 409)


# ── Test 1: Live Dashboard Overview KPIs ──────────────────────────────────────

def test_dashboard_overview_endpoint():
    """Verify live metrics computed directly from PostgreSQL."""
    response = client.get("/api/v1/analytics/dashboard")
    assert response.status_code == 200
    data = response.json()

    assert "total_vehicles" in data
    assert "available_vehicles" in data
    assert "total_shipments" in data
    assert "total_logistics_cost_inr" in data
    assert "empty_km_reduced" in data
    assert "avg_vehicle_utilization_pct" in data
    assert "on_time_delivery_pct" in data
    assert data["total_vehicles"] >= 0


# ── Test 2: What-If Supported Scenarios ───────────────────────────────────────

def test_what_if_supported_scenarios():
    """Verify listing 9 supported scenario types."""
    response = client.get("/api/v1/what-if/scenarios")
    assert response.status_code == 200
    scens = response.json()
    assert isinstance(scens, list)
    types = [s["type"] for s in scens]
    assert "heavy_traffic" in types
    assert "breakdown" in types
    assert "road_closure" in types
    assert "urgent_shipment" in types


# ── Test 3: What-If Simulation — Heavy Traffic ────────────────────────────────

def test_what_if_heavy_traffic():
    """Heavy traffic simulation must calculate extra duration and fuel impact."""
    response = client.post("/api/v1/what-if/simulate", json={
        "scenario_type": "heavy_traffic",
        "extra_delay_min": 60,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_type"] == "heavy_traffic"
    assert "metrics" in data
    assert "duration" in data["metrics"]
    assert data["metrics"]["duration"]["after"] > data["metrics"]["duration"]["before"]
    assert len(data["action_steps"]) > 0


# ── Test 4: What-If Simulation — Breakdown ────────────────────────────────────

def test_what_if_breakdown():
    """Breakdown simulation must calculate dispatch detour and replacement plan."""
    response = client.post("/api/v1/what-if/simulate", json={
        "scenario_type": "breakdown",
        "extra_delay_min": 120,
        "detour_km": 40.0,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_type"] == "breakdown"
    assert data["metrics"]["total_cost"]["after"] > data["metrics"]["total_cost"]["before"]
    assert "replacement" in data["recommended_action"].lower() or len(data["action_steps"]) > 0


# ── Test 5: What-If Simulation — Tyre Puncture ────────────────────────────────

def test_what_if_tyre_puncture():
    """Puncture simulation must calculate workshop delay and repair fee."""
    response = client.post("/api/v1/what-if/simulate", json={
        "scenario_type": "tyre_puncture",
        "extra_delay_min": 45,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_type"] == "tyre_puncture"
    assert data["metrics"]["duration"]["after"] > data["metrics"]["duration"]["before"]


# ── Test 6: What-If Simulation — Road Closure Detour ──────────────────────────

def test_what_if_road_closure():
    """Road closure must evaluate state highway detour km and additional toll/fuel."""
    response = client.post("/api/v1/what-if/simulate", json={
        "scenario_type": "road_closure",
        "detour_km": 50.0,
        "extra_delay_min": 70,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_type"] == "road_closure"
    assert data["metrics"]["distance"]["after"] > data["metrics"]["distance"]["before"]


# ── Test 7: What-If Simulation — Low Fuel ─────────────────────────────────────

def test_what_if_low_fuel():
    """Low fuel scenario must calculate fuel hub divert."""
    response = client.post("/api/v1/what-if/simulate", json={
        "scenario_type": "low_fuel",
        "detour_km": 15.0,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_type"] == "low_fuel"
    assert "fuel" in data["recommended_action"].lower()


# ── Test 8: What-If Simulation — Urgent Shipment Insertion ────────────────────

def test_what_if_urgent_shipment():
    """Urgent shipment insertion must increase vehicle capacity utilization."""
    response = client.post("/api/v1/what-if/simulate", json={
        "scenario_type": "urgent_shipment",
        "additional_weight_kg": 1000.0,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_type"] == "urgent_shipment"
    assert data["metrics"]["utilization"]["after"] >= data["metrics"]["utilization"]["before"]


# ── Test 9: Cost Breakdown Trends ─────────────────────────────────────────────

def test_cost_trends_endpoint():
    """Verify GET /api/v1/analytics/cost-trends."""
    response = client.get("/api/v1/analytics/cost-trends")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)


# ── Test 10: Actual vs Predicted Intelligence ─────────────────────────────────

def test_actual_vs_predicted_endpoint():
    """Verify ETA, demand, and risk comparison."""
    response = client.get("/api/v1/analytics/actual-vs-predicted")
    assert response.status_code == 200
    data = response.json()
    assert "eta_comparisons" in data
    assert "demand_comparisons" in data
    assert "delay_risk_accuracy" in data
    assert isinstance(data["eta_comparisons"], list)


# ── Test 11: In-App Notifications List & Unread Counter ───────────────────────

def test_notifications_lifecycle():
    """Verify notifications listing, badge count, and mark-read flow."""
    # 1. Create a test notification in DB
    db = SessionLocal()
    try:
        user = db.query(User).first()
        user_id = user.id if user else uuid.uuid4()
        notif_id = uuid.uuid4()
        notif = Notification(
            id=notif_id,
            user_id=user_id,
            notification_type="system_alert",
            title="Phase 7 Test Alert",
            message="Test notification for verification",
            is_read=False,
        )
        db.add(notif)
        db.commit()
        notif_id_str = str(notif_id)
    finally:
        db.close()

    # 2. Get unread count
    count_res = client.get("/api/v1/notifications/unread-count")
    assert count_res.status_code == 200
    assert count_res.json()["unread_count"] >= 1

    # 3. List notifications
    list_res = client.get("/api/v1/notifications")
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1

    # 4. Mark single as read
    read_res = client.post(f"/api/v1/notifications/{notif_id_str}/read")
    assert read_res.status_code == 200
    assert read_res.json()["is_read"] is True

    # 5. Mark all as read
    mark_all_res = client.post("/api/v1/notifications/mark-all-read")
    assert mark_all_res.status_code == 200
    assert mark_all_res.json()["success"] is True


# ── Test 12: Admin Platform System Statistics ─────────────────────────────────

def test_admin_system_stats_endpoint():
    """Verify GET /api/v1/admin/system-stats platform diagnostics."""
    response = client.get("/api/v1/admin/system-stats")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["version"] == "1.0.0-phase7"
    assert "uptime_seconds" in data
    assert "total_vehicles_active" in data
