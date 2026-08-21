"""
Auth-related Pydantic schemas.
These define the exact shape of request bodies and responses for auth endpoints.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: "UserProfile"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserProfile(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    phone: str | None = None
    is_active: bool
    preferred_language: str | None = "en"
    organization_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SignupRequest(BaseModel):
    full_name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=6)
    phone: str | None = None
    preferred_language: str | None = "en"
    organization_name: str | None = None
    role: str = "driver"

    # Driver Profile fields
    license_number: str | None = None
    license_type: str | None = None
    license_expiry: str | None = None
    assigned_vehicle_id: UUID | None = None

    # Fleet Manager Profile fields
    managed_fleet_size: int | None = None
    region: str | None = None

    # Enterprise Customer Profile fields
    company_name: str | None = None
    gst_number: str | None = None
    billing_address: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
