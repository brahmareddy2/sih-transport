"""
ETA Calculator — Phase 4 Telematics Integration.
Computes deterministic remaining duration and integrates Phase 3 ML delay risk prediction.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import logging
from sqlalchemy.orm import Session
from app.services.ml.delay_prediction import predict_delay_risk

logger = logging.getLogger(__name__)

def calculate_eta(
    db: Session,
    vehicle_id: str,
    remaining_distance_km: float,
    current_speed_kmh: float,
    active_shipment_id: Optional[str] = None,
) -> dict:
    """
    Calculate remaining travel time and ETA.
    Integrates ML delay prediction to adjust the duration if a shipment_id is available.
    """
    speed = max(10.0, current_speed_kmh)  # prevent division by zero
    det_time_min = (remaining_distance_km / speed) * 60.0

    ml_delay_min = 0
    risk_level = "LOW"

    if active_shipment_id:
        try:
            # Call Phase 3 ML delay prediction
            pred = predict_delay_risk(
                db=db,
                shipment_id=active_shipment_id,
                vehicle_id=vehicle_id,
                distance_km=remaining_distance_km,
                estimated_duration_min=det_time_min,
            )
            ml_delay_min = pred.get("predicted_delay_minutes", 0)
            risk_level = pred.get("risk_level", "LOW")
        except Exception as e:
            logger.debug("Failed to calculate ML delay risk, falling back to deterministic: %s", e)

    total_duration_min = int(round(det_time_min + ml_delay_min))
    eta_time = datetime.now(timezone.utc) + timedelta(minutes=total_duration_min)

    return {
        "remaining_distance_km": round(remaining_distance_km, 1),
        "remaining_duration_min": total_duration_min,
        "deterministic_duration_min": int(round(det_time_min)),
        "ml_delay_minutes": ml_delay_min,
        "risk_level": risk_level,
        "eta": eta_time.isoformat(),
    }
