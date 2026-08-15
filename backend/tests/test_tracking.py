"""
Phase 4 Telematics and GPS Tracking Test Suite.
Verifies tracking APIs, GPS simulation control, fuel consumption,
low-fuel alert triggers, ETA calculations, and WebSocket authorization.
"""
import pytest
import uuid
from datetime import date, datetime, timedelta, timezone
from fastapi import Depends
from fastapi.testclient import TestClient

from app.main import app
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.route import Route
from app.models.analytics import VehicleLocationHistory
from app.models.notification import Notification
from app.core.database import SessionLocal, get_db

# ── Test Client Auth Override ──────────────────────────────────
mock_admin = User(
    email="tracking_admin@example.com",
    full_name="Tracking Admin",
    password_hash="test-hash",
    role="admin",
    is_active=True,
)

def mock_get_current_user(db = Depends(get_db)):
    # Query from active session to prevent DetachedInstanceError
    return db.query(User).filter(User.email == "tracking_admin@example.com").first()

app.dependency_overrides[get_current_user] = mock_get_current_user
client = TestClient(app)


# ── Seed helper ────────────────────────────────────────────────
@pytest.fixture(scope="module", autouse=True)
def seed_test_database():
    from app.core.database import Base, engine, SessionLocal as TestSessionLocal
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    
    # Seed mock admin user to DB
    db = TestSessionLocal()
    try:
        # Check if user already exists
        db.add(mock_admin)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

    response = client.post("/api/v1/seed/generate", json={"overwrite": True})
    assert response.status_code == 200


# ── 1. REST Endpoints ──────────────────────────────────────────

def test_list_vehicles_tracking():
    """Verify listing all vehicle states."""
    response = client.get("/api/v1/tracking/vehicles")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "vehicle_id" in data[0]
    assert "vehicle_status" in data[0]


def test_get_single_vehicle_state():
    """Verify fetching state of a single vehicle."""
    db = SessionLocal()
    try:
        vehicle = db.query(Vehicle).first()
        assert vehicle is not None
        v_id = str(vehicle.id)
    finally:
        db.close()

    response = client.get(f"/api/v1/tracking/vehicles/{v_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["registration_number"] == vehicle.registration_number


def test_get_non_existent_vehicle():
    """Verify 404 behavior for invalid vehicle UUIDs."""
    dummy_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/tracking/vehicles/{dummy_id}")
    assert response.status_code == 404


def test_location_history_endpoint():
    """Verify location history endpoint returns list."""
    db = SessionLocal()
    try:
        vehicle = db.query(Vehicle).first()
        v_id = str(vehicle.id)
    finally:
        db.close()

    response = client.get(f"/api/v1/tracking/vehicles/{v_id}/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ── 2. Simulation Controls ─────────────────────────────────────

def test_simulation_controls_lifecycle():
    """Verify starting, pausing, resuming, and stopping GPS simulation."""
    db = SessionLocal()
    try:
        vehicle = db.query(Vehicle).first()
        route = db.query(Route).filter(Route.vehicle_id == vehicle.id).first()
        v_id = str(vehicle.id)
        r_id = str(route.id) if route else None
    finally:
        db.close()

    # 1. Start simulation
    payload = {"vehicle_id": v_id, "action": "start", "route_id": r_id}
    response = client.post("/api/v1/tracking/simulate/start", json=payload)
    assert response.status_code == 200
    assert response.json()["engine_status"] == "running"
    assert response.json()["vehicle_status"] == "IN_TRANSIT"

    # 2. Pause simulation
    response = client.post("/api/v1/tracking/simulate/pause", json=payload)
    assert response.status_code == 200
    assert response.json()["engine_status"] == "idle"
    assert response.json()["vehicle_status"] == "STOPPED"

    # 3. Resume simulation
    response = client.post("/api/v1/tracking/simulate/resume", json=payload)
    assert response.status_code == 200
    assert response.json()["engine_status"] == "running"
    assert response.json()["vehicle_status"] == "IN_TRANSIT"

    # 4. Stop simulation
    response = client.post("/api/v1/tracking/simulate/stop", json=payload)
    assert response.status_code == 200
    
    # Check if cleaned up
    from app.services.tracking.gps_simulator import SIMULATIONS
    assert v_id not in SIMULATIONS


# ── 3. Simulation Unit Logic ───────────────────────────────────

def test_haversine_and_bearing():
    """Verify haversine and bearing calculation logic."""
    from app.services.tracking.gps_simulator import haversine_distance, calculate_bearing
    # Coordinates of Mumbai to Pune (~120km)
    dist = haversine_distance(19.0760, 72.8777, 18.5204, 73.8567)
    assert 110.0 <= dist <= 130.0

    bearing = calculate_bearing(19.0760, 72.8777, 18.5204, 73.8567)
    assert 90 <= bearing <= 180  # southeast


def test_fuel_consumption_and_low_fuel_alert():
    """Verify fuel decreases dynamically during tick and triggers low fuel status/alerts."""
    from app.services.tracking.gps_simulator import tick_simulations, SIMULATIONS, start_simulation
    
    db = SessionLocal()
    try:
        vehicle = db.query(Vehicle).first()
        route = db.query(Route).filter(Route.vehicle_id == vehicle.id).first()
        v_id = str(vehicle.id)
        r_id = str(route.id) if route else None
    finally:
        db.close()

    # Start simulation
    db = SessionLocal()
    try:
        start_simulation(uuid.UUID(v_id), uuid.UUID(r_id) if r_id else None, db)
    finally:
        db.close()

    assert v_id in SIMULATIONS
    
    # Force low fuel state
    SIMULATIONS[v_id]["fuel_level"] = 10.0  # 10 Liters
    SIMULATIONS[v_id]["fuel_capacity"] = 200.0  # 5% remaining
    
    # Tick simulation loop manually
    import asyncio
    asyncio.run(tick_simulations())

    # Verify status changed to LOW_FUEL
    assert SIMULATIONS[v_id]["vehicle_status"] == "LOW_FUEL"
    
    # Check alert was created
    db = SessionLocal()
    try:
        alert = db.query(Notification).filter(
            Notification.notification_type == "low_fuel_alert"
        ).first()
        assert alert is not None
        assert vehicle.registration_number in alert.title
    finally:
        db.close()
        
    # Clean up
    SIMULATIONS.pop(v_id, None)


def test_eta_calculation_logic():
    """Verify eta_calculator returns valid ETA metadata."""
    from app.services.tracking.eta_calculator import calculate_eta
    db = SessionLocal()
    try:
        res = calculate_eta(db, str(uuid.uuid4()), 120.0, 60.0, None)
        assert res["remaining_duration_min"] == 120  # (120km / 60kmh) * 60min = 120min
        assert res["risk_level"] == "LOW"
        assert "eta" in res
    finally:
        db.close()


# ── 4. WebSockets Auth ──────────────────────────────────────────

def test_websocket_forbidden_without_token():
    """Verify WebSocket connection rejects clients without token."""
    from starlette.websockets import WebSocketDisconnect
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect("/api/v1/tracking/ws") as websocket:
            websocket.receive_text()
    assert excinfo.value.code == 1008


def test_websocket_unauthorized_token():
    """Verify WebSocket connection rejects invalid tokens."""
    from starlette.websockets import WebSocketDisconnect
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect("/api/v1/tracking/ws?token=invalid") as websocket:
            websocket.receive_text()
    assert excinfo.value.code == 1008

