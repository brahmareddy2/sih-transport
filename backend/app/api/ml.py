"""
AI/ML Prediction and Risk Intelligence API Router — Phase 3.
Provides endpoints to train, predict, and analyze fleet/route logs.
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.models.prediction import ModelPrediction
from app.schemas.ml import (
    DemandPredictRequest,
    DemandPredictResponse,
    DelayPredictRequest,
    DelayPredictResponse,
    VehicleRiskRequest,
    VehicleRiskResponse,
    AnomalyDetectRequest,
    AnomalyDetectResponse,
    ModelRegistryResponse,
    PredictionLogResponse,
)
from app.services.ml.demand_forecasting import (
    train_demand_model,
    predict_demand,
    _model_cache as demand_cache,
)
from app.services.ml.delay_prediction import (
    train_delay_model,
    predict_delay_risk,
    _model_cache as delay_cache,
)
from app.services.ml.vehicle_risk import predict_vehicle_risk
from app.services.ml.anomaly_detector import (
    train_anomaly_model,
    detect_anomalies_for_route,
    _model_cache as anomaly_cache,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ml", tags=["AI/ML Predictions"])


# ── Demand Forecasting ────────────────────────────────────────

@router.post("/demand/train", summary="Train demand forecasting model")
def run_train_demand(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "operator")),
):
    """Train the daily shipment demand forecasting regressor."""
    try:
        metrics = train_demand_model(db)
        return {"message": "Demand forecasting model trained.", "metrics": metrics}
    except Exception as e:
        logger.error("Failed to train demand model: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/demand/predict", response_model=DemandPredictResponse, summary="Predict shipment demand")
def run_predict_demand(
    payload: DemandPredictRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Predict shipment count and weight for a future date and city pair."""
    try:
        return predict_demand(db, payload.origin_city, payload.destination_city, payload.target_date)
    except Exception as e:
        logger.error("Demand prediction failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── Delay Risk Prediction ─────────────────────────────────────

@router.post("/delay/train", summary="Train delay prediction classifier")
def run_train_delay(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "operator")),
):
    """Train the shipment delivery delay risk classifier."""
    try:
        metrics = train_delay_model(db)
        return {"message": "Delay risk prediction model trained.", "metrics": metrics}
    except Exception as e:
        logger.error("Failed to train delay model: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/delay/predict", response_model=DelayPredictResponse, summary="Predict route delay risk")
def run_predict_delay(
    payload: DelayPredictRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Predict shipment delay probability and risk category (LOW / MEDIUM / HIGH)."""
    try:
        return predict_delay_risk(
            db, payload.shipment_id, payload.vehicle_id, payload.distance_km, payload.estimated_duration_min
        )
    except Exception as e:
        logger.error("Delay prediction failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── Vehicle Health Risk ───────────────────────────────────────

@router.post("/vehicle-risk/train", summary="Train/Refresh vehicle risk model")
def run_train_vehicle_risk(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "operator")),
):
    """Initializes vehicle breakdown risk telemetry logs. Vehicle risk evaluates dynamically."""
    return {"message": "Vehicle breakdown risk model refreshed."}


@router.post("/vehicle-risk/predict", response_model=VehicleRiskResponse, summary="Predict vehicle risk score")
def run_predict_vehicle_risk(
    payload: VehicleRiskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Evaluate vehicle risk index [0, 100], risk category, and inspection warnings."""
    try:
        return predict_vehicle_risk(db, payload.vehicle_id)
    except Exception as e:
        logger.error("Vehicle risk evaluation failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── Anomaly Detection ─────────────────────────────────────────

@router.post("/anomaly/detect", response_model=AnomalyDetectResponse, summary="Detect trip anomalies")
def run_detect_anomaly(
    payload: AnomalyDetectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Detect fuel theft, detour, or delay anomalies for a route using IsolationForest."""
    try:
        return detect_anomalies_for_route(db, payload.route_id)
    except Exception as e:
        logger.error("Anomaly detection failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── Models & Predictions Info ────────────────────────────────

@router.get("/models", response_model=list[ModelRegistryResponse], summary="List trained models")
def list_models(
    current_user: User = Depends(get_current_user),
):
    """Retrieve training metadata, versioning, and feature configurations for ML models."""
    return [
        ModelRegistryResponse(
            model_name="demand_forecasting",
            model_version=demand_cache["version"],
            training_date=demand_cache["training_date"],
            evaluation_metrics=demand_cache["metrics"],
            features=demand_cache["features"],
        ),
        ModelRegistryResponse(
            model_name="delay_prediction",
            model_version=delay_cache["version"],
            training_date=delay_cache["training_date"],
            evaluation_metrics=delay_cache["metrics"],
            features=delay_cache["features"],
        ),
        ModelRegistryResponse(
            model_name="anomaly_detector",
            model_version=anomaly_cache["version"],
            training_date=anomaly_cache["training_date"],
            evaluation_metrics={"contamination": 0.1},
            features=anomaly_cache["features"],
        ),
    ]


@router.get("/predictions", response_model=list[PredictionLogResponse], summary="List predictions log")
def list_predictions(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List historical predictions logs stored in the database."""
    logs = db.query(ModelPrediction).order_by(
        ModelPrediction.prediction_timestamp.desc()
    ).limit(limit).all()
    return logs
