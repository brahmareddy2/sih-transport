"""
Authentication router.
Endpoints: login, refresh, logout, /me, change-password
"""
import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserProfile,
    SignupRequest,
)
from app.schemas.common import MessageResponse

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=UserProfile, summary="User registration")
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    """
    Register a new user account.
    Public registration is restricted to 'driver', 'fleet_operator', and 'customer' (Enterprise Customer).
    Creates both the User and their specific profile atomically inside a database transaction.
    """
    existing_user = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    import uuid
    role_requested = payload.role.lower()
    if role_requested not in ["admin", "fleet_operator", "driver", "customer"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Public registration is only allowed for Admin, Driver, Fleet Operator, or Enterprise Customer roles.",
        )

    is_active = True
    is_approved = True
    if role_requested == "admin":
        is_active = False
        is_approved = False

    new_user = User(
        id=uuid.uuid4(),
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        phone=payload.phone,
        role=role_requested,
        preferred_language=payload.preferred_language or "en",
        organization_name=payload.organization_name,
        is_active=is_active,
        is_approved=is_approved,
    )
    db.add(new_user)

    try:
        if role_requested == "driver":
            license_num = payload.license_number
            if not license_num:
                import random
                license_num = f"DL-{random.randint(100000, 999999)}"
            
            # Verify license_number is unique
            from app.models.driver import Driver
            existing_driver = db.query(Driver).filter(Driver.license_number == license_num).first()
            if existing_driver and payload.license_number:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Driver license number is already registered",
                )

            employee_id = f"EMP-{uuid.uuid4().hex[:8].upper()}"
            from datetime import datetime
            expiry_date = None
            if payload.license_expiry:
                try:
                    expiry_date = datetime.strptime(payload.license_expiry, "%Y-%m-%d").date()
                except ValueError:
                    pass

            profile = Driver(
                id=uuid.uuid4(),
                user_id=new_user.id,
                employee_id=employee_id,
                license_number=license_num,
                license_type=payload.license_type or "LMV",
                license_expiry=expiry_date,
                assigned_vehicle_id=payload.assigned_vehicle_id,
                status="available",
            )
            db.add(profile)

        elif role_requested == "fleet_operator":
            from app.models.fleet_operator import FleetOperatorProfile
            profile = FleetOperatorProfile(
                id=uuid.uuid4(),
                user_id=new_user.id,
                managed_fleet_size=payload.managed_fleet_size or 0,
                region=payload.region or "National",
            )
            db.add(profile)

        elif role_requested == "customer":
            company_name_val = payload.company_name or payload.organization_name
            if not company_name_val:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Company name or organization name is required for Enterprise Customer registration",
                )
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
        logger.error("Transaction failed during signup: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed due to database error: {str(e)}",
        )

    db.refresh(new_user)
    logger.info("New user registered: id=%s email=%s role=%s active=%s", new_user.id, new_user.email, new_user.role, new_user.is_active)
    return new_user


@router.post("/login", response_model=TokenResponse, summary="User login")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    Authenticate user with email + password.
    Returns JWT access token (15 min) and refresh token (7 days).
    """
    # Query user by email (regardless of active status first)
    user = db.query(User).filter(User.email == payload.email.lower()).first()

    if not user:
        logger.warning("Login failed: email=%s not found", payload.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    if not verify_password(payload.password, user.password_hash):
        logger.warning("Failed login attempt for email=%s ip=%s", payload.email, request.client.host)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active or not getattr(user, "is_approved", True):
        logger.warning("Inactive/Unapproved user login attempt: email=%s", payload.email)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is pending approval by an administrator.",
        )

    access_token = create_access_token(subject=str(user.id), role=user.role)
    refresh_token = create_refresh_token(subject=str(user.id))

    logger.info("User logged in: id=%s role=%s", user.id, user.role)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserProfile.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse, summary="Refresh access token")
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    """Issue a new access token using a valid refresh token."""
    from jose import JWTError

    try:
        token_data = decode_token(payload.refresh_token)
        if token_data.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = token_data.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return TokenResponse(
        access_token=create_access_token(subject=str(user.id), role=user.role),
        refresh_token=create_refresh_token(subject=str(user.id)),
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserProfile.model_validate(user),
    )


@router.post("/logout", response_model=MessageResponse, summary="Logout")
def logout(current_user: Annotated[User, Depends(get_current_user)]):
    """
    Logout endpoint. In a stateless JWT system, the client deletes the token.
    Future: add a token blacklist in Redis for immediate invalidation.
    """
    logger.info("User logged out: id=%s", current_user.id)
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserProfile, summary="Get current user profile")
def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    """Return the profile of the currently authenticated user."""
    return UserProfile.model_validate(current_user)


@router.put("/change-password", response_model=MessageResponse, summary="Change password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Allow a user to change their own password."""
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    current_user.password_hash = hash_password(payload.new_password)
    current_user.updated_at = datetime.now(timezone.utc)
    db.commit()
    logger.info("Password changed for user id=%s", current_user.id)
    return MessageResponse(message="Password changed successfully")
