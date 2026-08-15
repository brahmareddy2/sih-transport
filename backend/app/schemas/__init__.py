"""Schemas package init."""
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    UserProfile,
)
from app.schemas.common import (
    PaginatedResponse,
    MessageResponse,
    ErrorResponse,
)

__all__ = [
    "LoginRequest",
    "TokenResponse",
    "RefreshRequest",
    "UserProfile",
    "PaginatedResponse",
    "MessageResponse",
    "ErrorResponse",
]
