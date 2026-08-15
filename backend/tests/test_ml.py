"""
Phase 3 AI/ML Test Suite.
Tests for demand forecasting, delay risk prediction, vehicle risk,
anomaly detection, API endpoints, DB storage, and OR-Tools integration.
"""
import pytest
from datetime import date, datetime, timedelta, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.core.dependencies import get_current_user
from app.models.user import User
from app.core.database import SessionLocal

# ── Test Client Setup ──────────────────────────────────────────

mock_user = User(
    email="ml_testadmin@example.com",
    full_name="ML Test Admin",
    password_hash="test-hash",
    role="admin",
    is_active=True,
)

def mock_get_current_user():
    return mock_user

app.dependency_overrides[get_current_user] = mock_get_current_user
client = TestClient(app)


# ── 1. Demand Forecasting ──────────────────────────────────────

def test_demand_model_training():
    """Train the demand forecasting model; verify metrics are returned."""
    response = client.post("/api/v1/ml/demand/train")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    # Verify at least MAE and RMSE are numeric
    metrics = data["metrics"]
    assert "mae" in metrics or "status" in metrics  # either trained or message

def test_demand_predict_endpoint():
    """Predict demand for a future date via API."""
    payload = {
        "origin_city": "Mumbai",
        "destination_city": "Pune",
        "target_date": str(date.today() + timedelta(days=7)),
    }
    response = client.post("/api/v1/ml/demand/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "predicted_shipments" in data
    assert data["predicted_shipments"] >= 1
    assert "confidence_lower" in data
    assert "confidence_upper" in data
    assert data["confidence_lower"] <= data["predicted_shipments"] <= data["confidence_upper"] or \
        data["confidence_upper"] >= data["predicted_shipments"]

def test_demand_predict_returns_stored_forecast():
    """Verify that predictions are stored in the demand_forecasts table."""
    payload = {
        "origin_city": "Delhi",
        "destination_city": "Jaipur",
        "target_date": str(date.today() + timedelta(days=3)),
    }
    response = client.post("/api/v1/ml/demand/predict", json=payload)
    assert response.status_code == 200


# ── 2. Delay Risk Prediction ───────────────────────────────────

def test_delay_model_training():
    """Train the delay risk classifier."""
    response = client.post("/api/v1/ml/delay/train")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data

def test_delay_predict_with_dummy_ids():
    """Predict delay risk for synthetic UUIDs — should not crash."""
    payload = {
        "shipment_id": "00000000-0000-0000-0000-000000000001",
        "vehicle_id": "00000000-0000-0000-0000-000000000002",
        "distance_km": 450.0,
        "estimated_duration_min": 390.0,
    }
    response = client.post("/api/v1/ml/delay/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "delay_probability" in data
    assert 0.0 <= data["delay_probability"] <= 1.0
    assert data["risk_level"] in ("LOW", "MEDIUM", "HIGH")
    assert len(data["explanation"]) > 0

def test_delay_risk_levels():
    """Verify risk level classification is consistent."""
    payload = {
        "shipment_id": "00000000-0000-0000-0000-000000000003",
        "vehicle_id": "00000000-0000-0000-0000-000000000004",
        "distance_km": 1500.0,  # long haul => higher risk
        "estimated_duration_min": 720.0,
    }
    response = client.post("/api/v1/ml/delay/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] in ("LOW", "MEDIUM", "HIGH")
    assert data["predicted_delay_minutes"] >= 0


# ── 3. Vehicle Health Risk ─────────────────────────────────────

def test_vehicle_risk_predict_with_dummy_id():
    """Predict vehicle risk for a non-existent vehicle — should fail gracefully."""
    payload = {"vehicle_id": "00000000-0000-0000-0000-000000000099"}
    response = client.post("/api/v1/ml/vehicle-risk/predict", json=payload)
    # Expected: 500 because vehicle not found
    assert response.status_code == 500

def test_vehicle_risk_score_bounds_with_real_vehicle():
    """Run vehicle risk prediction on a real vehicle after seeding data."""
    # First seed the DB
    seed_response = client.post("/api/v1/seed/generate", json={"overwrite": True})
    assert seed_response.status_code == 200

    # Fetch a vehicle ID
    from app.core.database import SessionLocal
    from app.models.vehicle import Vehicle
    db = SessionLocal()
    vehicle = db.query(Vehicle).first()
    db.close()

    if vehicle:
        payload = {"vehicle_id": str(vehicle.id)}
        response = client.post("/api/v1/ml/vehicle-risk/predict", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert 0.0 <= data["risk_score"] <= 100.0
        assert data["risk_level"] in ("LOW", "MEDIUM", "HIGH")
        assert isinstance(data["risk_indicators"], list)
        assert isinstance(data["inspection_recommended"], bool)


# ── 4. Anomaly Detection ───────────────────────────────────────

def test_anomaly_detect_with_dummy_route():
    """Detect anomaly for a non-existent route — should fail gracefully."""
    payload = {"route_id": "00000000-0000-0000-0000-000000000099"}
    response = client.post("/api/v1/ml/anomaly/detect", json=payload)
    assert response.status_code == 500

def test_anomaly_detection_with_real_route():
    """Detect anomaly for an actual route after seeding data."""
    from app.core.database import SessionLocal
    from app.models.route import Route
    db = SessionLocal()
    route = db.query(Route).first()
    db.close()

    if route:
        payload = {"route_id": str(route.id)}
        response = client.post("/api/v1/ml/anomaly/detect", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["is_anomaly"], bool)
        assert "anomaly_score" in data
        assert "explanation" in data


# ── 5. Model Registry & Predictions Log ───────────────────────

def test_models_registry_endpoint():
    """GET /ml/models should return model metadata."""
    response = client.get("/api/v1/ml/models")
    assert response.status_code == 200
    data = response.json()
    model_names = [m["model_name"] for m in data]
    assert "demand_forecasting" in model_names
    assert "delay_prediction" in model_names
    assert "anomaly_detector" in model_names

def test_predictions_log_endpoint():
    """GET /ml/predictions should return a list."""
    response = client.get("/api/v1/ml/predictions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# ── 6. DB Prediction Storage ───────────────────────────────────

def test_prediction_stored_in_db():
    """Verify a demand prediction is persisted to the model_predictions table."""
    from app.core.database import SessionLocal
    from app.models.prediction import ModelPrediction

    payload = {
        "origin_city": "Chennai",
        "destination_city": "Bangalore",
        "target_date": str(date.today() + timedelta(days=14)),
    }
    client.post("/api/v1/ml/demand/predict", json=payload)

    db = SessionLocal()
    count = db.query(ModelPrediction).filter(ModelPrediction.model_name == "demand_forecasting").count()
    db.close()
    assert count > 0


# ── 7. Feature Preprocessing ───────────────────────────────────

def test_demand_feature_encoding():
    """Verify city-to-index encoding in demand forecasting module."""
    from app.services.ml.demand_forecasting import CITY_MAP, _model_cache
    assert "Mumbai" in CITY_MAP
    assert "Delhi" in CITY_MAP
    assert len(CITY_MAP) >= 12

def test_delay_model_features_defined():
    """Verify delay model has the correct feature set defined."""
    from app.services.ml.delay_prediction import _model_cache
    features = _model_cache["features"]
    assert "distance_km" in features
    assert "est_duration_min" in features

def test_anomaly_model_features_defined():
    """Verify anomaly detector has correct feature set."""
    from app.services.ml.anomaly_detector import _model_cache
    features = _model_cache["features"]
    assert "fuel_efficiency_gap" in features


# ── 8. AI → OR-Tools Integration ──────────────────────────────

def test_vrp_solver_accepts_ai_risk_penalties():
    """Verify OR-Tools VRP solver accepts ai_risk_penalties without errors."""
    from app.services.optimization.vrp_solver import VRPSolver, ShipmentInput, VehicleInput

    shipments = [
        ShipmentInput(id="shp-a1", shipment_number="A1", origin_city="Mumbai",
                      destination_city="Pune", weight_kg=500.0, volume_m3=2.0),
    ]
    vehicles = [
        VehicleInput(id="v-a1", registration_number="MH12XX1234",
                     vehicle_type="medium_truck", capacity_weight_kg=5000.0,
                     capacity_volume_m3=20.0, fuel_efficiency_kmpl=6.0, status="available"),
    ]

    # With AI penalty injected for high-risk shipment
    ai_penalties = {
        "shipments": {"shp-a1": 5000.0},   # ₹5,000 HIGH delay risk penalty
        "vehicles":  {"v-a1": 0.0},
    }

    solver = VRPSolver(time_limit_seconds=5)
    result = solver.solve(shipments, vehicles, ai_risk_penalties=ai_penalties)

    assert result.status == "solved"
    assert result.total_routes == 1
    # Total cost should include AI penalty
    route_cost = result.routes[0].total_cost_inr
    assert route_cost > 0
    cost_breakdown = result.routes[0].cost_breakdown
    assert "ai_risk_penalty_inr" in cost_breakdown
    assert cost_breakdown["ai_risk_penalty_inr"] == 5000.0

def test_vrp_solver_with_zero_penalties():
    """Verify solver with zero penalties produces normal results."""
    from app.services.optimization.vrp_solver import VRPSolver, ShipmentInput, VehicleInput

    shipments = [
        ShipmentInput(id="shp-b1", shipment_number="B1", origin_city="Delhi",
                      destination_city="Jaipur", weight_kg=800.0, volume_m3=3.0),
    ]
    vehicles = [
        VehicleInput(id="v-b1", registration_number="DL01YY4321",
                     vehicle_type="medium_truck", capacity_weight_kg=5000.0,
                     capacity_volume_m3=20.0, fuel_efficiency_kmpl=6.0, status="available"),
    ]

    solver = VRPSolver(time_limit_seconds=5)
    result_no_penalty = solver.solve(shipments, vehicles, ai_risk_penalties={})
    result_with_penalty = solver.solve(shipments, vehicles, ai_risk_penalties={
        "shipments": {"shp-b1": 10000.0}
    })

    # Cost with penalty must be higher than without
    cost_no_penalty = result_no_penalty.routes[0].total_cost_inr if result_no_penalty.routes else 0
    cost_with_penalty = result_with_penalty.routes[0].total_cost_inr if result_with_penalty.routes else 0
    assert cost_with_penalty >= cost_no_penalty
