"""
Phase 7 — Admin and System Statistics API Router.

Provides real-time platform diagnostic status, resource counts, and uptime.
"""
import logging
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.route import Route
from app.models.shipment import Shipment
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.analytics import SystemStatsResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin & System"])

_START_TIME = time.time()


@router.get(
    "/system-stats",
    response_model=SystemStatsResponse,
    summary="Platform System Diagnostics & Statistics",
)
def get_system_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "operator")),
):
    """Return health of core components, database connection, and tracked entity counts."""
    db_connected = False
    try:
        db.execute(text("SELECT 1"))
        db_connected = True
    except Exception as e:
        logger.warning("DB ping check failed: %s", e)

    veh_count = db.query(Vehicle).count()
    shp_count = db.query(Shipment).count()
    routes_count = db.query(Route).count()

    uptime = round(time.time() - _START_TIME, 1)

    return {
        "status": "healthy" if db_connected else "degraded",
        "version": "1.0.0-phase7",
        "database_connected": db_connected,
        "total_vehicles_active": veh_count,
        "total_shipments_tracked": shp_count,
        "total_routes_active": routes_count,
        "active_websockets_count": 1,
        "uptime_seconds": uptime,
        "environment": get_settings().environment,
        "timestamp": datetime.now(timezone.utc),
    }


from typing import List
from app.schemas.auth import UserProfile
from fastapi import HTTPException

@router.get(
    "/pending-users",
    response_model=List[UserProfile],
    summary="Get users pending approval",
)
def get_pending_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Retrieve list of inactive or unapproved users (e.g. pending admin accounts)."""
    try:
        pending = db.query(User).filter((User.is_active == False) | (User.is_approved == False)).all()
    except Exception:
        pending = db.query(User).filter(User.is_active == False).all()
    return pending


@router.post(
    "/approve-user/{user_id}",
    summary="Approve pending user account",
)
def approve_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Approve and activate user account."""
    import uuid
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = True
    if hasattr(user, "is_approved"):
        user.is_approved = True
    db.commit()
    logger.info("Admin %s approved user %s", current_user.email, user.email)
    return {"message": f"User {user.email} approved successfully", "success": True}


from app.schemas.auth import SignupRequest
from app.core.security import hash_password

@router.post(
    "/create-internal-user",
    response_model=UserProfile,
    summary="Create internal user (Admin/Operator) by an existing Admin",
)
def create_internal_user(
    payload: SignupRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """
    Register an internal user (Admin or Operator) directly.
    Only existing Admins are authorized to call this.
    """
    existing_user = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email is already registered",
        )

    import uuid
    role_requested = payload.role.lower()
    if role_requested not in ["admin", "operator", "fleet_manager", "driver", "customer"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid role requested",
        )

    new_user = User(
        id=uuid.uuid4(),
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        phone=payload.phone,
        role=role_requested,
        preferred_language=payload.preferred_language or "en",
        organization_name=payload.organization_name,
        is_active=True,
        is_approved=True,
    )
    db.add(new_user)

    try:
        if role_requested == "driver":
            if not payload.license_number:
                raise HTTPException(status_code=400, detail="License number is required for driver")
            from app.models.driver import Driver
            profile = Driver(
                id=uuid.uuid4(),
                user_id=new_user.id,
                employee_id=f"EMP-{uuid.uuid4().hex[:8].upper()}",
                license_number=payload.license_number,
                license_type=payload.license_type or "LMV",
                status="available",
            )
            db.add(profile)
        elif role_requested == "fleet_manager":
            from app.models.fleet_manager import FleetManagerProfile
            profile = FleetManagerProfile(
                id=uuid.uuid4(),
                user_id=new_user.id,
                managed_fleet_size=payload.managed_fleet_size or 0,
                region=payload.region or "National",
            )
            db.add(profile)
        elif role_requested == "customer":
            company_name_val = payload.company_name or payload.organization_name or "Internal Organization"
            from app.models.enterprise_customer import EnterpriseCustomerProfile
            profile = EnterpriseCustomerProfile(
                id=uuid.uuid4(),
                user_id=new_user.id,
                company_name=company_name_val,
                gst_number=payload.gst_number,
                billing_address=payload.billing_address,
            )
            db.add(profile)

        db.commit()
    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create user/profile: {str(e)}"
        )

    db.refresh(new_user)
    return new_user

