"""
Pydantic v2 schemas for Phase 7: Integrated Analytics, What-If Simulation, and Notifications.
"""
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


# ── Live Dashboard Overview ───────────────────────────────────────────────────

class DashboardOverviewResponse(BaseModel):
    # Fleet status
    total_vehicles: int
    available_vehicles: int
    in_transit_vehicles: int
    maintenance_vehicles: int
    breakdown_vehicles: int

    # Shipment status
    total_shipments: int
    pending_shipments: int
    in_transit_shipments: int
    delivered_shipments: int
    delayed_shipments: int

    # Incident & Recovery metrics
    active_incidents: int
    resolved_incidents: int
    total_recovery_plans: int
    approved_recovery_plans: int

    # Distance & Deadhead metrics
    total_distance_km: float
    total_empty_km: float
    empty_km_reduced: float
    empty_km_reduction_pct: float

    # Fuel & Financials
    total_fuel_l: float
    total_fuel_cost_inr: float
    estimated_fuel_saved_l: float
    estimated_fuel_savings_inr: float
    total_logistics_cost_inr: float
    total_co2_kg: float

    # Performance
    avg_vehicle_utilization_pct: float
    on_time_delivery_pct: float
    total_return_matches_approved: int

    timestamp: datetime


# ── What-If Simulation Schemas ────────────────────────────────────────────────

class WhatIfSimulateRequest(BaseModel):
    scenario_type: str = Field(
        ...,
        description=(
            "Scenario type: heavy_traffic | breakdown | tyre_puncture | "
            "road_closure | low_fuel | driver_unavailable | urgent_shipment | "
            "additional_shipment | vehicle_unavailable"
        ),
    )
    vehicle_id: Optional[UUID] = None
    route_id: Optional[UUID] = None
    extra_delay_min: Optional[int] = Field(None, ge=0)
    detour_km: Optional[float] = Field(None, ge=0)
    additional_weight_kg: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None


class WhatIfMetric(BaseModel):
    metric_name: str
    before: float
    after: float
    delta: float
    delta_pct: float
    unit: str
    is_favorable: bool


class WhatIfScenarioResult(BaseModel):
    scenario_type: str
    scenario_title: str
    description: str
    target_vehicle_registration: Optional[str] = None
    target_route_number: Optional[str] = None
    metrics: Dict[str, WhatIfMetric]
    recommended_action: str
    action_steps: List[str]
    optimization_plan: Dict[str, Any]


# ── Actual vs Predicted Intelligence ──────────────────────────────────────────

class ActualVsPredictedResponse(BaseModel):
    eta_comparisons: List[Dict[str, Any]]
    demand_comparisons: List[Dict[str, Any]]
    delay_risk_accuracy: Dict[str, Any]
    anomaly_detection_summary: Dict[str, Any]


# ── Notifications Schemas ─────────────────────────────────────────────────────

class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    notification_type: str
    title: str
    message: str
    data_json: Optional[Dict[str, Any]] = None
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    total: int
    unread_count: int
    items: List[NotificationResponse]


# ── System Stats Schema ───────────────────────────────────────────────────────

class SystemStatsResponse(BaseModel):
    status: str
    version: str
    database_connected: bool
    total_vehicles_active: int
    total_shipments_tracked: int
    total_routes_active: int
    active_websockets_count: int
    uptime_seconds: float
    environment: str
    timestamp: datetime
