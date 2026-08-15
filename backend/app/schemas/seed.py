"""
Pydantic schemas for seed data management API.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SeedStatusSchema(BaseModel):
    """Current state of the seed data in the database."""
    seeded: bool
    vehicles_count: int
    drivers_count: int
    shipments_count: int
    trips_count: int
    incidents_count: int
    pending_shipments: int
    available_vehicles: int
    available_drivers: int
    seed_version: str = "SEED=42 v1.0"
    last_seeded_at: Optional[datetime] = None


class SeedGenerateRequest(BaseModel):
    """Request to generate or regenerate seed data."""
    overwrite: bool = False
    vehicles: int = 50
    drivers: int = 50
    shipments: int = 500
    trips: int = 300
    incidents: int = 80


class SeedGenerateResponse(BaseModel):
    message: str
    summary: dict
    duration_seconds: float
