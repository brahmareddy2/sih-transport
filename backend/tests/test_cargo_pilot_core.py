import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.user import User
from app.models.assistant_session import AssistantSession
from app.services.assistant.intent_engine import get_assistant_intent_engine

# We use the standard TestClient
client = TestClient(app)

def test_signup_role_rules():
    db = SessionLocal()
    # Clean database before testing if user exists
    db.query(User).filter(User.email.in_(["driver_test@cargo.com", "admin_test@cargo.com"])).delete()
    db.commit()

    # 1. Driver registration: should be active immediately
    response = client.post("/api/v1/auth/signup", json={
        "full_name": "Test Driver",
        "email": "driver_test@cargo.com",
        "password": "Password123!",
        "phone": "+919999988888",
        "preferred_language": "te",
        "organization_name": "Cargo Test Ltd",
        "role": "driver"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "driver"
    assert data["is_active"] is True
    # In db is_approved must be True
    user_db = db.query(User).filter(User.email == "driver_test@cargo.com").first()
    assert user_db is not None
    assert user_db.is_active is True
    assert user_db.is_approved is True

    # 2. Admin registration: should be inactive and unapproved by default
    response = client.post("/api/v1/auth/signup", json={
        "full_name": "Test Admin",
        "email": "admin_test@cargo.com",
        "password": "Password123!",
        "phone": "+919999977777",
        "preferred_language": "en",
        "organization_name": "Cargo Test Ltd",
        "role": "admin"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "admin"
    assert data["is_active"] is False

    admin_db = db.query(User).filter(User.email == "admin_test@cargo.com").first()
    assert admin_db is not None
    assert admin_db.is_active is False
    assert admin_db.is_approved is False
    db.close()


def test_admin_approval_workflow():
    db = SessionLocal()
    # Ensure admin_test exists and is inactive/unapproved
    admin_db = db.query(User).filter(User.email == "admin_test@cargo.com").first()
    if not admin_db:
        # Create it inactive
        import uuid
        from app.core.security import hash_password
        admin_db = User(
            id=uuid.uuid4(),
            email="admin_test@cargo.com",
            password_hash=hash_password("Password123!"),
            role="admin",
            full_name="Test Admin",
            is_active=False,
            is_approved=False
        )
        db.add(admin_db)
        db.commit()

    # 1. Attempting login as unapproved admin should return 403 Forbidden
    login_res = client.post("/api/v1/auth/login", json={
        "email": "admin_test@cargo.com",
        "password": "Password123!"
    })
    assert login_res.status_code == 403
    assert "pending approval" in login_res.json()["detail"]

    # 2. Fetch pending approvals (requires active admin role)
    # We temporarily mock get_current_user to bypass check for list retrieval
    from app.core.dependencies import get_current_user
    old_override = app.dependency_overrides.get(get_current_user)
    active_admin = User(role="admin", is_active=True, is_approved=True, email="super@cargo.com")
    app.dependency_overrides[get_current_user] = lambda: active_admin

    pending_res = client.get("/api/v1/admin/pending-users")
    assert pending_res.status_code == 200
    pending_list = pending_res.json()
    assert any(u["email"] == "admin_test@cargo.com" for u in pending_list)

    # 3. Approve the user
    target_user_id = str(admin_db.id)
    approve_res = client.post(f"/api/v1/admin/approve-user/{target_user_id}")
    assert approve_res.status_code == 200
    assert approve_res.json()["success"] is True

    # Clean overrides
    if old_override is not None:
        app.dependency_overrides[get_current_user] = old_override
    else:
        app.dependency_overrides.pop(get_current_user, None)

    # 4. Now, login should succeed!
    login_res2 = client.post("/api/v1/auth/login", json={
        "email": "admin_test@cargo.com",
        "password": "Password123!"
    })
    assert login_res2.status_code == 200
    assert "access_token" in login_res2.json()

    # Clean up
    db.query(User).filter(User.email == "admin_test@cargo.com").delete()
    db.commit()
    db.close()


def test_multiturn_assistant_session():
    db = SessionLocal()
    # Create or fetch a test driver user
    driver = db.query(User).filter(User.role == "driver", User.is_active == True).first()
    if not driver:
        import uuid
        from app.core.security import hash_password
        driver = User(
            id=uuid.uuid4(),
            email="driver_flow@cargo.com",
            password_hash=hash_password("Password123!"),
            role="driver",
            full_name="Driver Flow",
            is_active=True,
            is_approved=True
        )
        db.add(driver)
        db.commit()

    engine = get_assistant_intent_engine()
    user_id = str(driver.id)

    # Clear assistant session for this user first
    db.query(AssistantSession).filter(AssistantSession.user_id == driver.id).delete()
    db.commit()

    # Turn 1: Specify origin and destination cities
    res = engine.process_query(
        query="Delhi to Hyderabad",
        user_role="driver",
        user_id=user_id,
        db=db
    )
    assert res["intent"] == "TRIP_PLANNING"
    # It should store origin/destination and ask for vehicle
    assert "vehicle" in res["message"] or "వాహనం" in res["message"]

    # Turn 2: Specify the vehicle ID (TRUCK-025)
    res2 = engine.process_query(
        query="TRUCK-025",
        user_role="driver",
        user_id=user_id,
        db=db
    )
    assert res2["intent"] == "TRIP_PLANNING"
    # It should retain origin/destination, store vehicle, and ask for fuel level
    assert "diesel" in res2["message"] or "డీజిల్" in res2["message"]

    # Turn 3: Specify fuel available (120 L) -> should complete plan and return card details
    res3 = engine.process_query(
        query="120 litres",
        user_role="driver",
        user_id=user_id,
        db=db
    )
    assert res3["intent"] == "TRIP_PLANNING"
    assert "distance_km" in res3["data"]
    # Final trip card summary must contain calculated details
    assert res3["data"]["fuel_required_l"] > 0

    # Cleanup
    db.query(AssistantSession).filter(AssistantSession.user_id == driver.id).delete()
    db.query(User).filter(User.email == "driver_flow@cargo.com").delete()
    db.commit()
    db.close()
