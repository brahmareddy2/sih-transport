"""
Phase 1 verification script:
Tests database creation, admin user bootstrap, password hashing, and JWT login API.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.models.user import User
from app.models import *  # import all models
from app.main import app

from sqlalchemy.pool import StaticPool

def run_verification():
    print("=" * 60)
    print("  Phase 1 Local Verification Script")
    print("=" * 60)

    # 1. Create in-memory SQLite DB with StaticPool so all threads share the memory DB
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Ignore PostgreSQL JSONB compile issue for SQLite by substituting JSON
    from sqlalchemy.dialects.postgresql import JSONB
    from sqlalchemy import JSON
    for table in Base.metadata.tables.values():
        for col in table.columns:
            if isinstance(col.type, JSONB):
                col.type = JSON()

    Base.metadata.create_all(engine)
    print(f"[OK] Created all {len(Base.metadata.tables)} tables in DB schema")

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Override get_db dependency in FastAPI
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # 2. Seed Admin user
    db = TestingSessionLocal()
    admin = User(
        email="admin@logistics.in",
        password_hash=hash_password("Admin@123!"),
        full_name="System Administrator",
        role="admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    print("[OK] Admin user created: admin@logistics.in / Admin@123!")
    db.close()

    # 3. Test Auth Endpoint via TestClient
    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@logistics.in", "password": "Admin@123!"},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    print("[OK] Login successful!")
    print("  Access Token :", data["access_token"][:30] + "...")
    print("  Refresh Token:", data["refresh_token"][:30] + "...")
    print("  User Role    :", data["user"]["role"])
    print("  Expires In   :", data["expires_in"], "seconds")

    # 4. Test Protected Endpoint (/api/v1/auth/me)
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200, f"Auth me failed: {me_res.text}"
    print("[OK] GET /api/v1/auth/me succeeded:", me_res.json()["email"])

    print("=" * 60)
    print("  ALL PHASE 1 VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_verification()
