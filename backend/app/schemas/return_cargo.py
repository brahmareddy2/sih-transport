"""
Pydantic v2 schemas for Phase 6: Return Cargo Matching and Empty-Kilometer Reduction.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


# ── Search & Request Schemas ──────────────────────────────────────────────────

class ReturnCargoSearchRequest(BaseModel):
    vehicle_id: Optional[UUID] = Field(None, description="Specific vehicle ID to search matches for")
    current_city: Optional[str] = Field(None, description="Current city/location of vehicle")
    destination_city: Optional[str] = Field(None, description="Home depot / target return city")
    max_detour_km: Optional[float] = Field(200.0, ge=0.0, description="Max acceptable detour in km")
    min_score: Optional[float] = Field(0.0, ge=0.0, le=100.0, description="Minimum matching score threshold")


class ApproveMatchRequest(BaseModel):
    notes: Optional[str] = Field(None, description="Operator approval notes")


class RejectMatchRequest(BaseModel):
    rejection_reason: str = Field(..., min_length=2, description="Reason for rejection")


# ── Detailed Match Response ───────────────────────────────────────────────────

class ReturnCargoMatchResponse(BaseModel):
    id: UUID
    vehicle_id: UUID
    shipment_id: UUID
    route_id: Optional[UUID] = None
    return_route_id: Optional[UUID] = None

    # Locations
    origin_city: str
    destination_city: str
    vehicle_current_city: str
    vehicle_home_city: str

    # Distance & Empty-KM Metrics
    empty_km_before: float
    empty_km_after: float
    empty_km_reduced: float
    empty_km_reduction_pct: float
    loaded_distance_km: float
    detour_distance_km: float

    # Financial & Fuel Metrics
    additional_fuel_l: float
    additional_fuel_cost_inr: float
    additional_toll_cost_inr: float
    total_additional_cost_inr: float
    estimated_revenue_inr: float
    net_benefit_inr: float

    # Scoring & Details
    match_score: float
    compatibility_details: Optional[Dict[str, Any]] = None

    # Lifecycle & Status
    status: str
    rejection_reason: Optional[str] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Joined / Enriched Fields
    vehicle_registration: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_capacity_weight_kg: Optional[float] = None
    shipment_number: Optional[str] = None
    shipment_weight_kg: Optional[float] = None
    shipment_goods_type: Optional[str] = None
    shipment_priority: Optional[str] = None
    is_refrigerated: Optional[bool] = None
    is_hazardous: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class ReturnCargoListResponse(BaseModel):
    total: int
    items: List[ReturnCargoMatchResponse]


# ── Vehicle Opportunity Model ─────────────────────────────────────────────────

class VehicleReturnOpportunity(BaseModel):
    vehicle_id: UUID
    registration_number: str
    vehicle_type: str
    current_city: str
    home_depot_city: str
    status: str
    capacity_weight_kg: float
    fuel_efficiency_kmpl: float
    is_refrigerated: bool
    can_carry_hazmat: bool
    potential_empty_km: float
    available_matches_count: int
    best_match_score: Optional[float] = None


# ── Execution Result ──────────────────────────────────────────────────────────

class ReturnRouteExecutionResult(BaseModel):
    success: bool
    match_id: UUID
    vehicle_id: UUID
    shipment_id: UUID
    return_route_id: UUID
    return_route_number: str
    total_distance_km: float
    empty_km_reduced: float
    empty_km_reduction_pct: float
    estimated_fuel_saved_l: float
    estimated_cost_saved_inr: float
    new_eta: Optional[str] = None
    message: str


# ── Analytics Response ────────────────────────────────────────────────────────

class ReturnCargoAnalyticsResponse(BaseModel):
    total_potential_empty_km: float
    total_empty_km_reduced: float
    overall_reduction_pct: float
    total_fuel_saved_l: float
    total_fuel_saved_inr: float
    total_net_benefit_inr: float
    total_matches_generated: int
    total_approved_matches: int
    total_rejected_matches: int
    average_match_score: float
    top_saving_routes: List[Dict[str, Any]] = []
