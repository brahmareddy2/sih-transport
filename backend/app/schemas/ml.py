"""
Pydantic schemas for the AI/ML Prediction and Risk Intelligence API.
"""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Demand Forecasting ────────────────────────────────────────

class DemandPredictRequest(BaseModel):
    origin_city: str = Field(..., description="Origin city name")
    destination_city: str = Field(..., description="Destination city name")
    target_date: date = Field(..., description="Target date for forecasting")


class DemandPredictResponse(BaseModel):
    predicted_shipments: int
    predicted_weight_kg: float
    confidence_lower: int
    confidence_upper: int
    model_version: str
    origin_city: Optional[str] = None
    destination_city: Optional[str] = None
    target_date: Optional[str] = None
    prediction_horizon_days: Optional[int] = None
    model_mae: Optional[float] = None


# ── Delay Risk Prediction ─────────────────────────────────────

class DelayPredictRequest(BaseModel):
    shipment_id: str = Field(..., description="Shipment UUID")
    vehicle_id: str = Field(..., description="Vehicle UUID")
    distance_km: float = Field(..., description="Route distance in km")
    estimated_duration_min: float = Field(..., description="Estimated travel time in minutes")


class DelayPredictResponse(BaseModel):
    shipment_id: str
    vehicle_id: str
    delay_probability: float
    predicted_delay_minutes: int
    risk_level: str
    explanation: list[str]


# ── Vehicle Risk Prediction ───────────────────────────────────

class VehicleRiskRequest(BaseModel):
    vehicle_id: str = Field(..., description="Vehicle UUID")


class VehicleRiskResponse(BaseModel):
    vehicle_id: str
    registration_number: str
    risk_score: float
    risk_level: str
    inspection_recommended: bool
    recommended_action: str
    risk_indicators: list[str]


# ── Anomaly Detection ─────────────────────────────────────────

class AnomalyDetectRequest(BaseModel):
    route_id: str = Field(..., description="Route/Trip UUID")


class AnomalyDetectResponse(BaseModel):
    route_id: str
    is_anomaly: bool
    anomaly_score: float
    explanation: list[str]
    features: dict


# ── Model Registry & Log List ────────────────────────────────

class ModelRegistryResponse(BaseModel):
    model_name: str
    model_version: str
    training_date: Optional[datetime]
    evaluation_metrics: dict
    features: list[str]


class PredictionLogResponse(BaseModel):
    id: UUID
    model_name: str
    model_version: str
    target_entity_type: str
    target_entity_id: str
    risk_level: Optional[str]
    explanation: Optional[str]
    prediction_timestamp: datetime
    prediction_value: dict
