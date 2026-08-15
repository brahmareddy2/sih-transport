"""
Pydantic schemas for the Phase 4 Real-Time GPS Tracking & Telematics API.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class VehicleStateResponse(BaseModel):
    vehicle_id: UUID
    registration_number: str
    latitude: float
    longitude: float
    speed: float
    heading: int
    fuel_level: float
    fuel_pct: float
    engine_status: str
    vehicle_status: str
    timestamp: datetime
    current_trip_id: Optional[UUID] = None
    driver_name: Optional[str] = None
    remaining_km: Optional[float] = None
    eta_minutes: Optional[int] = None
    eta: Optional[str] = None
    risk_level: Optional[str] = None


class LocationHistoryResponse(BaseModel):
    vehicle_id: UUID
    trip_id: Optional[UUID] = None
    latitude: float
    longitude: float
    speed_kmh: float
    heading_deg: int
    fuel_level_l: float
    recorded_at: datetime


class SimulationControlRequest(BaseModel):
    vehicle_id: UUID
    action: str = Field(..., description="start | pause | resume | stop")
    route_id: Optional[UUID] = Field(None, description="Optional route/trip to simulate")
