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
)
from app.schemas.common import MessageResponse

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse, summary="User login")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    Authenticate user with email + password.
    Returns JWT access token (15 min) and refresh token (7 days).
    """
    user = db.query(User).filter(
        User.email == payload.email,
        User.is_active == True,
    ).first()

    if not user or not verify_password(payload.password, user.password_hash):
        logger.warning("Failed login attempt for email=%s ip=%s", payload.email, request.client.host)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
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
