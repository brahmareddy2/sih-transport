"""
Pydantic schemas for Phase 5 Incident Management & Recovery Planning API.
"""
from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


# ── Incident Schemas ──────────────────────────────────────────────────────────

class IncidentCreateRequest(BaseModel):
    incident_type: str = Field(..., description="breakdown|tyre_puncture|road_closure|traffic_jam|low_fuel|driver_unavailable|other")
    severity: Optional[str] = Field(None, description="low|medium|high|critical — auto-computed if omitted")
    vehicle_id: Optional[UUID] = None
    driver_id: Optional[UUID] = None
    route_id: Optional[UUID] = None
    description: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    city: Optional[str] = None
    source: Optional[str] = "manual"


class IncidentSimulateRequest(BaseModel):
    vehicle_id: UUID
    incident_type: str = Field(..., description="breakdown|tyre_puncture|road_closure|traffic_jam|low_fuel|driver_unavailable")
    route_id: Optional[UUID] = None
    description: Optional[str] = None


class IncidentResponse(BaseModel):
    id: UUID
    incident_type: str
    severity: str
    status: str
    vehicle_id: Optional[UUID]
    driver_id: Optional[UUID]
    route_id: Optional[UUID]
    description: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    city: Optional[str]
    source: Optional[str]
    reported_at: datetime
    detected_at: Optional[datetime]
    resolved_at: Optional[datetime]
    affected_shipment_ids: Optional[List[str]]
    # Computed / joined fields
    vehicle_registration: Optional[str] = None
    vehicle_type: Optional[str] = None
    driver_name: Optional[str] = None
    route_number: Optional[str] = None
    affected_shipment_count: Optional[int] = None
    recovery_plans_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class IncidentListResponse(BaseModel):
    total: int
    items: List[IncidentResponse]


# ── Recovery Plan Schemas ─────────────────────────────────────────────────────

class RecoveryPlanResponse(BaseModel):
    id: UUID
    incident_id: UUID
    plan_type: Optional[str]
    plan_description: Optional[str]
    action_type: Optional[str]
    recommended_action: str
    alternative_vehicle_id: Optional[UUID]
    alternative_driver_id: Optional[UUID]
    rerouted_route_id: Optional[UUID]
    estimated_delay_min: Optional[int]
    cost_impact_inr: Optional[float]
    additional_distance_km: Optional[float]
    recovery_score: Optional[float]
    is_approved: bool
    approved_at: Optional[datetime]
    created_at: datetime
    # Joined fields
    alternative_vehicle_registration: Optional[str] = None
    alternative_vehicle_type: Optional[str] = None
    alternative_driver_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RecoveryOptionsResponse(BaseModel):
    incident_id: UUID
    incident_type: str
    plans: List[RecoveryPlanResponse]
    recommended_plan_id: Optional[UUID] = None


class ApproveRecoveryRequest(BaseModel):
    notes: Optional[str] = None


class RecoveryExecutionResult(BaseModel):
    success: bool
    incident_id: UUID
    plan_id: UUID
    new_vehicle_id: Optional[UUID]
    new_vehicle_registration: Optional[str]
    new_driver_id: Optional[UUID]
    shipments_updated: int
    estimated_delay_min: int
    additional_cost_inr: float
    new_eta: Optional[str]
    incident_status: str
    message: str


class ResolveIncidentRequest(BaseModel):
    resolution_notes: Optional[str] = None
