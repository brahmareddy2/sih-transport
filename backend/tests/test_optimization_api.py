"""
Integration tests for the optimization and seed data APIs.
"""
from fastapi.testclient import TestClient
from app.main import app
from app.core.dependencies import get_current_user
from app.models.user import User

# Create a mock user to bypass JWT authorization checks
mock_user = User(
    email="testadmin@example.com",
    full_name="Test Admin",
    password_hash="test-hash",
    role="admin",
    is_active=True,
)

def mock_get_current_user():
    return mock_user

# Apply override
app.dependency_overrides[get_current_user] = mock_get_current_user
client = TestClient(app)


def test_seed_status_endpoint():
    response = client.get("/api/v1/seed/status")
    assert response.status_code == 200
    data = response.json()
    assert "seeded" in data
    assert "vehicles_count" in data


def test_scenarios_list_endpoint():
    response = client.get("/api/v1/optimization/scenarios")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    assert data[0]["scenario_number"] == 1


def test_preview_consolidation_endpoint():
    response = client.get("/api/v1/optimization/consolidate")
    assert response.status_code == 200
    # Returns an array (empty or populated depending on seed state)
    data = response.json()
    assert isinstance(data, list)


def test_generate_seed_and_run_scenario():
    # 1. Generate seed data (with overwrite to ensure clean slate)
    gen_response = client.post("/api/v1/seed/generate", json={"overwrite": True})
    assert gen_response.status_code == 200
    gen_data = gen_response.json()
    assert gen_data["summary"]["vehicles_count"] == 50

    # 2. Run Scenario 1 (which depends on seed data existing)
    sc_response = client.post("/api/v1/optimization/scenario/1")
    assert sc_response.status_code == 200
    sc_data = sc_response.json()
    assert sc_data["status"] == "solved"
    assert sc_data["summary"]["total_routes"] > 0

    # 3. Retrieve explanation
    job_id = sc_data["job_id"]
    exp_response = client.get(f"/api/v1/optimization/explain/{job_id}")
    assert exp_response.status_code == 200
    exp_data = exp_response.json()
    assert "summary_text" in exp_data
    assert len(exp_data["recommendations"]) > 0
