"""
Security utilities: password hashing and JWT token operations.
All cryptographic operations are centralized here.
Uses direct bcrypt library for hashing/verification (compatible with bcrypt 4.x/5.x).
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()

ALGORITHM = "HS256"


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using bcrypt (max 72 bytes)."""
    # Truncate to 72 bytes as per bcrypt specification
    password_bytes = plain_password.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a stored bcrypt hash."""
    password_bytes = plain_password.encode("utf-8")[:72]
    hashed_bytes = hashed_password.encode("utf-8")
    try:
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


# ── JWT Token Operations ──────────────────────────────────
def create_access_token(
    subject: str,
    role: str,
    extra_claims: Optional[dict] = None,
) -> str:
    """
    Create a short-lived JWT access token.

    Args:
        subject: User ID (UUID string)
        role: User role (admin, operator, etc.)
        extra_claims: Optional additional claims to embed

    Returns:
        Signed JWT string
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def create_refresh_token(subject: str) -> str:
    """
    Create a long-lived JWT refresh token.
    Contains minimal claims — only used to issue new access tokens.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    payload = {
        "sub": subject,
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    Raises:
        JWTError: If the token is invalid or expired.
    """
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
