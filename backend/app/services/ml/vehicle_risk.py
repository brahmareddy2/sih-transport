"""
AI/ML Vehicle Health Risk and Recommended Inspections Predictor.
Estimates vehicle risk score based on age, odometer, and service logs.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.vehicle import Vehicle
from app.models.analytics import MaintenanceRecord
from app.models.prediction import ModelPrediction

logger = logging.getLogger(__name__)

# Configurable constants for Indian transport conditions
CRITICAL_ODOMETER_KM = 250000.0   # High wear and tear after 2.5L km
SERVICE_INTERVAL_LIMIT_KM = 30000.0


def predict_vehicle_risk(db: Session, vehicle_id: str) -> dict:
    """
    Evaluate vehicle risk index [0, 100] using operational telemetry and
    maintenance history. Stores predictions and recommends inspections.
    """
    import uuid as _uuid
    try:
        vehicle_uuid = _uuid.UUID(str(vehicle_id))
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid vehicle ID format: '{vehicle_id}'")

    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_uuid).first()
    if not vehicle:
        raise ValueError(f"Vehicle with ID '{vehicle_id}' not found.")

    # 1. Fetch maintenance records
    records = db.query(MaintenanceRecord).filter(
        MaintenanceRecord.vehicle_id == vehicle_uuid
    ).all()

    breakdowns = sum(1 for r in records if r.maintenance_type == "breakdown_repair")
    total_services = len(records)

    # 2. Compute telemetry inputs
    age_years = max(1, datetime.now(timezone.utc).year - (vehicle.year or 2018))
    odometer = float(vehicle.odometer_km or 0.0)

    # Calculate gap since last serviced odometer
    last_service_odo = 0.0
    if records:
        service_odos = [float(r.odometer_at_service or 0) for r in records if r.odometer_at_service]
        if service_odos:
            last_service_odo = max(service_odos)

    odo_since_service = max(0.0, odometer - last_service_odo)

    # 3. Risk scoring algorithm
    risk_score = 15.0  # base risk

    # Odometer risk (max 30 pts)
    risk_score += min(30.0, (odometer / CRITICAL_ODOMETER_KM) * 30.0)

    # Service delay risk (max 25 pts)
    if odo_since_service > SERVICE_INTERVAL_LIMIT_KM:
        risk_score += min(25.0, 10.0 + ((odo_since_service - SERVICE_INTERVAL_LIMIT_KM) / 10000.0) * 5.0)
    else:
        risk_score += (odo_since_service / SERVICE_INTERVAL_LIMIT_KM) * 10.0

    # Age risk (max 15 pts)
    risk_score += min(15.0, (age_years / 10.0) * 15.0)

    # Breakdown index (max 20 pts)
    if breakdowns > 0:
        risk_score += min(20.0, breakdowns * 7.5)

    risk_score = min(100.0, round(risk_score, 1))

    # Risk level classification
    if risk_score < 35.0:
        risk_level = "LOW"
    elif risk_score < 70.0:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    # Compile indicators and inspection recommendation flag
    indicators = []
    inspection_recommended = False

    if odo_since_service > SERVICE_INTERVAL_LIMIT_KM:
        indicators.append("Overdue scheduled service interval limit")
        inspection_recommended = True
    if breakdowns > 1:
        indicators.append(f"Frequent breakdown pattern ({breakdowns} repairs)")
        inspection_recommended = True
    if odometer > CRITICAL_ODOMETER_KM:
        indicators.append(f"High cumulative mileage wear ({odometer:,.0f} km)")

    if not indicators:
        indicators.append("All primary diagnostics within nominal limits")

    recommendation = "N/A"
    if inspection_recommended:
        if risk_level == "HIGH":
            recommendation = "CRITICAL: Urgent depot inspection required before next dispatch."
        else:
            recommendation = "WARNING: Plan inspection check-up during next scheduled maintenance halt."

    result = {
        "vehicle_id": vehicle_id,
        "registration_number": vehicle.registration_number,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "inspection_recommended": inspection_recommended,
        "recommended_action": recommendation,
        "risk_indicators": indicators,
    }

    # Store prediction logs in database
    explanation = f"Odometer: {odometer:,.0f} km | Age: {age_years} yrs | Breakdowns: {breakdowns} | Indicators: {', '.join(indicators)}"

    pred = ModelPrediction(
        model_name="vehicle_risk",
        model_version="v1.0",
        training_date=datetime.now(timezone.utc),
        feature_info={
            "odometer_km": odometer,
            "age_years": age_years,
            "odo_since_service": odo_since_service,
            "breakdowns": breakdowns,
        },
        evaluation_metrics={"explainable_model": True},
        target_entity_type="vehicle",
        target_entity_id=vehicle_id,
        prediction_value=result,
        risk_level=risk_level,
        explanation=explanation,
        prediction_timestamp=datetime.now(timezone.utc),
    )
    db.add(pred)
    db.commit()

    return result
