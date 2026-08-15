"""
Pydantic schemas for the optimization API.
Request/response models for VRP solver endpoints.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Request Schemas ───────────────────────────────────────────

class ObjectiveWeightsSchema(BaseModel):
    """Configurable weights for multi-objective optimization."""
    cost_weight: float = Field(0.35, ge=0.0, le=1.0, description="Weight for cost minimization")
    distance_weight: float = Field(0.25, ge=0.0, le=1.0, description="Weight for distance minimization")
    delay_weight: float = Field(0.20, ge=0.0, le=1.0, description="Weight for delay penalty")
    empty_km_weight: float = Field(0.10, ge=0.0, le=1.0, description="Weight for empty km penalty")
    co2_weight: float = Field(0.10, ge=0.0, le=1.0, description="Weight for CO2 emissions")

    model_config = {"json_schema_extra": {
        "example": {
            "cost_weight": 0.35,
            "distance_weight": 0.25,
            "delay_weight": 0.20,
            "empty_km_weight": 0.10,
            "co2_weight": 0.10,
        }
    }}


class OptimizationRequest(BaseModel):
    """Request body to submit a new optimization job."""
    shipment_ids: list[str] = Field(
        ..., min_length=1, max_length=200,
        description="List of shipment IDs to optimize"
    )
    vehicle_ids: list[str] = Field(
        ..., min_length=1, max_length=50,
        description="List of vehicle IDs available for assignment"
    )
    weights: ObjectiveWeightsSchema = Field(
        default_factory=ObjectiveWeightsSchema,
        description="Objective function weights"
    )
    road_type: str = Field(
        "mixed",
        description="Road type: nh_only | mixed | sh | local | urban"
    )
    weight_profile: Optional[str] = Field(
        None,
        description="Pre-defined weight profile: balanced | cost_minimization | speed_priority | green_logistics | utilization_max"
    )
    time_limit_seconds: int = Field(
        30, ge=5, le=120,
        description="Solver time limit in seconds"
    )
    enable_consolidation: bool = Field(
        True,
        description="Allow shipment load consolidation"
    )


class ScenarioRequest(BaseModel):
    """Request to run a pre-built demo scenario."""
    scenario_number: int = Field(..., ge=1, le=5, description="Scenario number 1–5")
    weights: Optional[ObjectiveWeightsSchema] = None


# ── Response Schemas ──────────────────────────────────────────

class RouteStopSchema(BaseModel):
    stop_sequence: int
    stop_type: str          # pickup | delivery | depot
    city: str
    shipment_id: Optional[str]
    shipment_number: Optional[str]
    lat: float
    lon: float
    planned_arrival_min: int
    planned_departure_min: int
    distance_from_prev_km: float
    cargo_weight_kg: float
    cumulative_weight_kg: float


class CostBreakdownSchema(BaseModel):
    distance_km: float
    fuel_litres: float
    fuel_cost_inr: float
    toll_cost_inr: float
    driver_cost_inr: float
    vehicle_opex_inr: float
    empty_km: float
    empty_km_cost_inr: float
    co2_kg: float
    total_cost_inr: float
    cost_per_kg_inr: float
    cost_per_km_inr: float


class OptimizedRouteSchema(BaseModel):
    route_id: str
    vehicle_id: str
    vehicle_registration: str
    vehicle_type: str
    driver_id: Optional[str]
    stops: list[RouteStopSchema]
    shipment_ids: list[str]
    total_distance_km: float
    empty_distance_km: float
    estimated_duration_min: int
    total_weight_kg: float
    utilization_pct: float
    fuel_litres: float
    fuel_cost_inr: float
    toll_cost_inr: float
    driver_cost_inr: float
    vehicle_opex_inr: float
    total_cost_inr: float
    co2_kg: float
    cost_breakdown: CostBreakdownSchema


class OptimizationSummarySchema(BaseModel):
    """Aggregated fleet-level metrics for a solved optimization job."""
    total_routes: int
    total_shipments_served: int
    unserved_count: int
    total_distance_km: float
    total_empty_km: float
    empty_km_pct: float
    total_fuel_litres: float
    total_fuel_cost_inr: float
    total_toll_inr: float
    total_driver_cost_inr: float
    total_cost_inr: float
    total_co2_kg: float
    avg_utilization_pct: float
    cost_per_km_inr: float


class OptimizationResultSchema(BaseModel):
    """Full result for a completed optimization job."""
    job_id: str
    status: str
    algorithm: str
    solve_time_seconds: float
    routes: list[OptimizedRouteSchema]
    unserved_shipments: list[str]
    summary: OptimizationSummarySchema
    objective_score: dict
    explanation: list[str]
    created_at: datetime


class JobStatusSchema(BaseModel):
    """Status check response for an optimization job."""
    job_id: str
    status: str         # pending | running | solved | failed | timeout
    progress_pct: int
    message: str
    created_at: datetime


class ScenarioInfo(BaseModel):
    scenario_number: int
    title: str
    description: str
    shipment_count: int
    vehicle_count: int
    highlights: list[str]


class ConsolidationGroupSchema(BaseModel):
    group_id: int
    shipment_ids: list[str]
    total_weight_kg: float
    total_volume_m3: float
    shipment_count: int
    origin_city: Optional[str]
    destination_city: Optional[str]


class OptimizationExplanationSchema(BaseModel):
    job_id: str
    summary_text: str
    route_explanations: list[str]
    saving_highlights: list[str]
    constraint_notes: list[str]
    recommendations: list[str]
