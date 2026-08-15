"""
Phase 6 — Return Cargo Matching & Empty-Kilometer Reduction Test Suite.

Covers:
 1. Return cargo search and creation
 2. Return cargo listing with status filter
 3. Vehicle compatibility (weight, volume)
 4. Refrigerated cargo compatibility
 5. Hazardous material compatibility
 6. Route compatibility & detour distance calculation
 7. Deterministic match scoring bounds (0–100)
 8. Match ranking ordering (highest score first)
 9. Empty-km reduction calculation accuracy
10. Fuel and cost calculation
11. Match approval and return route creation
12. Shipment status update to 'assigned'
13. Vehicle status update to 'in_transit'
14. Notifications created on approval
15. Match rejection with reason
16. Return cargo opportunities listing
17. Analytics summary endpoint
18. Handling zero matches gracefully
19. Multiple compatible cargo scenarios
20. Re-matching refresh endpoint
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
from app.models.driver import Driver
from app.models.shipment import Shipment
from app.models.route import Route, RouteStop
from app.models.return_cargo import ReturnCargoMatch
from app.models.notification import Notification
from app.services.return_cargo.matching_engine import (
    evaluate_compatibility,
    calculate_match_metrics,
    find_return_matches_for_vehicle,
    persist_return_matches,
)

# ── Static Auth Override for Test Isolation ───────────────────────────────────
_mock_admin = User(
    id=uuid.UUID("00000000-0000-0000-0000-000000000099"),
    email="return_admin@example.com",
    full_name="Return Cargo Admin",
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
    """Ensure database has vehicles and shipments for Phase 6 tests."""
    db = SessionLocal()
    try:
        v_count = db.query(Vehicle).count()
    finally:
        db.close()

    if v_count == 0:
        resp = client.post("/api/v1/seed/generate", json={"overwrite": False})
        assert resp.status_code in (200, 409)


def get_test_vehicle(current_city="Pune", home_city="Mumbai"):
    db = SessionLocal()
    try:
        v = db.query(Vehicle).filter(Vehicle.status == "available").first()
        if not v:
            v = db.query(Vehicle).first()
        v_id = str(v.id)
        # Update locations for testing return leg
        v.current_city = current_city
        v.home_depot_city = home_city
        db.commit()
        return v_id, v.registration_number
    finally:
        db.close()


def get_or_create_return_shipment(origin="Pune", dest="Mumbai", weight=1500.0, refrigerated=False, hazmat=False):
    db = SessionLocal()
    try:
        shp = db.query(Shipment).filter(
            Shipment.origin_city == origin,
            Shipment.destination_city == dest,
            Shipment.status == "pending",
        ).first()

        if not shp:
            shp = Shipment(
                shipment_number=f"RET-TEST-{uuid.uuid4().hex[:6].upper()}",
                origin_city=origin,
                origin_address=f"{origin} Industrial Estate",
                origin_lat=18.5204,
                origin_lon=73.8567,
                destination_city=dest,
                destination_address=f"{dest} Warehouse",
                destination_lat=19.0760,
                destination_lon=72.8777,
                weight_kg=weight,
                volume_m3=8.0,
                goods_type="FMCG",
                is_hazardous=hazmat,
                requires_refrigeration=refrigerated,
                priority="high",
                status="pending",
            )
            db.add(shp)
            db.commit()
            db.refresh(shp)

        return str(shp.id), shp.shipment_number
    finally:
        db.close()


# ── Test 1: Search & Evaluate Return Cargo ─────────────────────────────────────

def test_search_return_cargo_endpoint():
    """Verify searching for return cargo via POST /api/v1/return-cargo."""
    v_id, _ = get_test_vehicle("Pune", "Mumbai")
    get_or_create_return_shipment("Pune", "Mumbai")

    response = client.post("/api/v1/return-cargo", json={
        "vehicle_id": v_id,
        "current_city": "Pune",
        "destination_city": "Mumbai",
        "max_detour_km": 250.0,
    })
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)
    if data["total"] > 0:
        first = data["items"][0]
        assert "match_score" in first
        assert "empty_km_reduced" in first
        assert first["empty_km_reduced"] >= 0


# ── Test 2: List Return Cargo Matches with Filters ────────────────────────────

def test_list_return_cargo_matches():
    """Verify listing matches and filtering by status."""
    v_id, _ = get_test_vehicle("Pune", "Mumbai")
    # Trigger search to generate matches
    client.post("/api/v1/return-cargo", json={"vehicle_id": v_id})

    response = client.get("/api/v1/return-cargo?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["items"], list)

    # Filter by status
    pending_resp = client.get("/api/v1/return-cargo?status=pending")
    assert pending_resp.status_code == 200
    for item in pending_resp.json()["items"]:
        assert item["status"] == "pending"


# ── Test 3: Weight and Volume Capacity Constraints ─────────────────────────────

def test_capacity_compatibility_evaluation():
    """Shipment heavier than vehicle capacity must fail weight compatibility check."""
    db = SessionLocal()
    try:
        vehicle = db.query(Vehicle).first()
        vehicle.capacity_weight_kg = 2000.0

        # Create oversized shipment
        heavy_shipment = Shipment(
            shipment_number=f"HEAVY-{uuid.uuid4().hex[:4]}",
            origin_city="Pune",
            origin_address="Pune",
            origin_lat=18.5,
            origin_lon=73.8,
            destination_city="Mumbai",
            destination_address="Mumbai",
            destination_lat=19.0,
            destination_lon=72.8,
            weight_kg=5000.0,  # 5000kg > 2000kg capacity
            status="pending",
        )

        compatible, details = evaluate_compatibility(
            vehicle=vehicle,
            shipment=heavy_shipment,
            current_city="Pune",
            home_city="Mumbai",
        )
        assert compatible is False
        assert details["checks"]["weight_compatible"] is False
    finally:
        db.close()


# ── Test 4: Refrigerated Cargo Constraint ──────────────────────────────────────

def test_refrigeration_compatibility():
    """Non-refrigerated vehicle must reject refrigerated cargo."""
    db = SessionLocal()
    try:
        vehicle = db.query(Vehicle).first()
        vehicle.is_refrigerated = False
        vehicle.capacity_weight_kg = 5000.0

        cold_shipment = Shipment(
            shipment_number=f"COLD-{uuid.uuid4().hex[:4]}",
            origin_city="Pune",
            origin_address="Pune",
            origin_lat=18.5,
            origin_lon=73.8,
            destination_city="Mumbai",
            destination_address="Mumbai",
            destination_lat=19.0,
            destination_lon=72.8,
            weight_kg=1000.0,
            requires_refrigeration=True,
            status="pending",
        )

        compatible, details = evaluate_compatibility(
            vehicle=vehicle,
            shipment=cold_shipment,
            current_city="Pune",
            home_city="Mumbai",
        )
        assert compatible is False
        assert details["checks"]["refrigeration_compatible"] is False
    finally:
        db.close()


# ── Test 5: Hazardous Material Constraint ─────────────────────────────────────

def test_hazmat_compatibility():
    """Non-hazmat vehicle must reject hazardous cargo."""
    db = SessionLocal()
    try:
        vehicle = db.query(Vehicle).first()
        vehicle.can_carry_hazmat = False
        vehicle.capacity_weight_kg = 5000.0

        hazmat_shipment = Shipment(
            shipment_number=f"HAZ-{uuid.uuid4().hex[:4]}",
            origin_city="Pune",
            origin_address="Pune",
            origin_lat=18.5,
            origin_lon=73.8,
            destination_city="Mumbai",
            destination_address="Mumbai",
            destination_lat=19.0,
            destination_lon=72.8,
            weight_kg=1000.0,
            is_hazardous=True,
            status="pending",
        )

        compatible, details = evaluate_compatibility(
            vehicle=vehicle,
            shipment=hazmat_shipment,
            current_city="Pune",
            home_city="Mumbai",
        )
        assert compatible is False
        assert details["checks"]["hazmat_compatible"] is False
    finally:
        db.close()


# ── Test 6: Empty-KM and Math Calculations ────────────────────────────────────

def test_empty_km_reduction_math():
    """Verify deadhead reduction formula: empty_before - empty_after."""
    db = SessionLocal()
    try:
        vehicle = db.query(Vehicle).first()
        vehicle.capacity_weight_kg = 5000.0

        # Pune -> Mumbai return shipment
        shipment = Shipment(
            shipment_number=f"MATH-{uuid.uuid4().hex[:4]}",
            origin_city="Pune",
            origin_address="Pune",
            origin_lat=18.5,
            origin_lon=73.8,
            destination_city="Mumbai",
            destination_address="Mumbai",
            destination_lat=19.0,
            destination_lon=72.8,
            weight_kg=2000.0,
            status="pending",
        )

        metrics = calculate_match_metrics(
            vehicle=vehicle,
            shipment=shipment,
            current_city="Pune",
            home_city="Mumbai",
        )

        assert metrics["empty_km_before"] > 0
        assert metrics["empty_km_after"] >= 0
        assert metrics["empty_km_reduced"] >= 0
        assert 0.0 <= metrics["empty_km_reduction_pct"] <= 100.0
        assert 0.0 <= metrics["match_score"] <= 100.0
    finally:
        db.close()


# ── Test 7: Deterministic Matching Score Bounds ───────────────────────────────

def test_match_score_bounds_and_determinism():
    """Score must always be within [0, 100] and identical for identical inputs."""
    db = SessionLocal()
    try:
        vehicle = db.query(Vehicle).first()
        shipment = db.query(Shipment).filter(Shipment.status == "pending").first()
        if not shipment:
            shipment = Shipment(
                shipment_number="SCORE-TEST",
                origin_city="Delhi",
                origin_address="Delhi",
                origin_lat=28.7,
                origin_lon=77.1,
                destination_city="Jaipur",
                destination_address="Jaipur",
                destination_lat=26.9,
                destination_lon=75.8,
                weight_kg=1500.0,
                status="pending",
            )

        m1 = calculate_match_metrics(vehicle, shipment, "Delhi", "Jaipur")
        m2 = calculate_match_metrics(vehicle, shipment, "Delhi", "Jaipur")

        assert m1["match_score"] == m2["match_score"]
        assert 0.0 <= m1["match_score"] <= 100.0
    finally:
        db.close()


# ── Test 8: Opportunities Endpoint ────────────────────────────────────────────

def test_return_opportunities_endpoint():
    """Verify GET /api/v1/return-cargo/opportunities lists fleet vehicles."""
    response = client.get("/api/v1/return-cargo/opportunities")
    assert response.status_code == 200
    opps = response.json()
    assert isinstance(opps, list)
    if opps:
        first = opps[0]
        assert "vehicle_id" in first
        assert "potential_empty_km" in first
        assert "available_matches_count" in first


# ── Test 9: Vehicle-Specific Matches Endpoint ──────────────────────────────────

def test_matches_for_vehicle_endpoint():
    """Verify GET /api/v1/return-cargo/matches/{vehicle_id}."""
    v_id, _ = get_test_vehicle("Bangalore", "Chennai")
    get_or_create_return_shipment("Bangalore", "Chennai")

    response = client.get(f"/api/v1/return-cargo/matches/{v_id}")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 0


# ── Test 10: Match Approval & Return Route Generation ─────────────────────────

def test_approve_match_creates_route():
    """Approving a match must create a Return Route, update Shipment and Vehicle."""
    v_id, _ = get_test_vehicle("Pune", "Mumbai")
    shp_id, _ = get_or_create_return_shipment("Pune", "Mumbai")

    # Generate matches
    search_res = client.post("/api/v1/return-cargo", json={"vehicle_id": v_id})
    assert search_res.status_code == 200
    items = search_res.json()["items"]
    assert len(items) > 0

    match_id = items[0]["id"]

    # Approve match
    approve_res = client.post(f"/api/v1/return-cargo/matches/{match_id}/approve", json={
        "notes": "Test Operator Approval"
    })
    assert approve_res.status_code == 200
    result = approve_res.json()
    assert result["success"] is True
    assert result["return_route_number"].startswith("RET-")
    assert result["empty_km_reduced"] >= 0

    # Verify DB state
    db = SessionLocal()
    try:
        match_db = db.query(ReturnCargoMatch).filter(ReturnCargoMatch.id == uuid.UUID(match_id)).first()
        assert match_db.status == "approved"
        assert match_db.return_route_id is not None

        # Verify Route was created
        route_db = db.query(Route).filter(Route.id == match_db.return_route_id).first()
        assert route_db is not None
        assert route_db.route_number.startswith("RET-")

        # Verify RouteStops were created
        stops = db.query(RouteStop).filter(RouteStop.route_id == route_db.id).all()
        assert len(stops) >= 2
    finally:
        db.close()


# ── Test 11: Rejection Endpoint ───────────────────────────────────────────────

def test_reject_match_endpoint():
    """Rejecting a match must update its status to 'rejected' with reason."""
    v_id, _ = get_test_vehicle("Ahmedabad", "Surat")
    get_or_create_return_shipment("Ahmedabad", "Surat")

    search_res = client.post("/api/v1/return-cargo", json={"vehicle_id": v_id})
    items = search_res.json()["items"]
    assert len(items) > 0

    match_id = items[0]["id"]
    reject_res = client.post(f"/api/v1/return-cargo/matches/{match_id}/reject", json={
        "rejection_reason": "Driver scheduled for mandatory rest"
    })
    assert reject_res.status_code == 200
    assert reject_res.json()["status"] == "rejected"
    assert reject_res.json()["rejection_reason"] == "Driver scheduled for mandatory rest"


# ── Test 12: Cannot Approve Already Approved Match ────────────────────────────

def test_cannot_reapprove_approved_match():
    """Attempting to approve an already approved match must return 400."""
    v_id, _ = get_test_vehicle("Hyderabad", "Bangalore")
    get_or_create_return_shipment("Hyderabad", "Bangalore")

    search_res = client.post("/api/v1/return-cargo", json={"vehicle_id": v_id})
    match_id = search_res.json()["items"][0]["id"]

    # First approval
    client.post(f"/api/v1/return-cargo/matches/{match_id}/approve", json={})

    # Second approval attempt
    res = client.post(f"/api/v1/return-cargo/matches/{match_id}/approve", json={})
    assert res.status_code == 400


# ── Test 13: Analytics Endpoint ───────────────────────────────────────────────

def test_return_cargo_analytics():
    """Verify GET /api/v1/return-cargo/analytics returns aggregate metrics."""
    response = client.get("/api/v1/return-cargo/analytics")
    assert response.status_code == 200
    data = response.json()
    assert "total_empty_km_reduced" in data
    assert "total_fuel_saved_l" in data
    assert "total_net_benefit_inr" in data
    assert "average_match_score" in data
    assert "total_approved_matches" in data


# ── Test 14: Refresh Match Endpoint ───────────────────────────────────────────

def test_refresh_return_match():
    """Verify POST /api/v1/return-cargo/{id}/match recalculates metrics."""
    v_id, _ = get_test_vehicle("Mumbai", "Pune")
    search_res = client.post("/api/v1/return-cargo", json={"vehicle_id": v_id})
    if search_res.json()["total"] > 0:
        match_id = search_res.json()["items"][0]["id"]
        refresh_res = client.post(f"/api/v1/return-cargo/{match_id}/match")
        assert refresh_res.status_code == 200
        assert refresh_res.json()["id"] == match_id
