"""
FastAPI dependency injection utilities.
Centralized place for all reusable dependencies:
  - Database session
  - Current authenticated user
  - Role-based access control guards
"""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User

# ── Bearer token extractor ────────────────────────────────
bearer_scheme = HTTPBearer(auto_error=True)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Dependency: Decode JWT, load user from DB, return User ORM object.
    Raises HTTP 401 if token invalid or user not found/inactive.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials)
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        if user_id is None or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    import uuid
    try:
        user_uuid = uuid.UUID(user_id)
    except (ValueError, TypeError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_uuid, User.is_active == True).first()
    if user is None:
        raise credentials_exception
    return user


# ── Role-guard factory ────────────────────────────────────
def require_roles(*allowed_roles: str):
    """
    Returns a FastAPI dependency that enforces role-based access.

    Usage:
        @router.get("/admin-only")
        def admin_route(user = Depends(require_roles("admin"))):
            ...
    """
    # Map operator/fleet_manager to fleet_operator for backward compatibility & safety
    mapped_roles = set(allowed_roles)
    if "operator" in mapped_roles or "fleet_manager" in mapped_roles:
        mapped_roles.add("fleet_operator")

    def role_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in mapped_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {list(allowed_roles)}",
            )
        return current_user

    return role_checker


# ── Convenience aliases ───────────────────────────────────
# Use these as Depends() arguments in route handlers

AdminOnly = Depends(require_roles("admin"))
OperatorOrAbove = Depends(require_roles("admin", "fleet_operator"))
FleetManagerOrAbove = Depends(require_roles("admin", "fleet_operator"))
AnyStaff = Depends(require_roles("admin", "fleet_operator", "driver"))
AnyAuthenticated = Depends(get_current_user)
