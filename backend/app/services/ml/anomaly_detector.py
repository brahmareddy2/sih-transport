"""
AI/ML Anomaly Detection Service.
Uses IsolationForest to identify unusual fuel usage or trip duration logs.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

import numpy as np
from sqlalchemy.orm import Session

try:
    from sklearn.ensemble import IsolationForest
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from app.models.route import Route
from app.models.prediction import ModelPrediction
from app.services.optimization.distance_matrix import city_distance_km

logger = logging.getLogger(__name__)

# Cache for trained model (in-memory singleton)
_model_cache: dict = {
    "model": None,
    "version": "v1.0",
    "training_date": None,
    "features": ["fuel_efficiency_gap", "duration_ratio", "distance_ratio"],
}


def train_anomaly_model(db: Session) -> dict:
    """
    Fetch historical routes, prepare ratios, train IsolationForest,
    and cache the model.
    """
    if not SKLEARN_AVAILABLE:
        raise RuntimeError("scikit-learn not available.")

    routes = db.query(Route).all()
    if len(routes) < 20:
        # Avoid crash: use simulated routes or skip if too sparse
        logger.info("Not enough routes to fit IsolationForest. Model will run in heuristic backup mode.")
        return {"status": "insufficient_data"}

    X = []
    for r in routes:
        dist = float(r.total_distance_km or 100.0)
        actual_fuel = float(r.actual_fuel_l or 20.0)

        # 1. Fuel efficiency gap
        expected_eff = 5.0  # default
        if r.vehicle:
            expected_eff = float(r.vehicle.fuel_efficiency_kmpl)
        actual_eff = dist / max(actual_fuel, 1.0)
        fuel_gap = expected_eff - actual_eff

        # 2. Duration ratio
        est_dur = float(r.estimated_duration_min or 120.0)
        act_dur = float(r.actual_duration_min or est_dur)
        dur_ratio = act_dur / est_dur

        # 3. Distance ratio (detour ratio)
        straight_dist = city_distance_km(r.origin_city, r.destination_city)
        dist_ratio = dist / max(straight_dist, 1.0)

        X.append([fuel_gap, dur_ratio, dist_ratio])

    X_arr = np.array(X)

    # Fit Isolation Forest (contamination = 10% expected anomalies)
    model = IsolationForest(contamination=0.1, random_state=42)
    model.fit(X_arr)

    _model_cache["model"] = model
    _model_cache["training_date"] = datetime.now(timezone.utc)

    logger.info("Anomaly detection IsolationForest trained on %d trips.", len(routes))
    return {"status": "trained", "samples": len(routes)}


def detect_anomalies_for_route(db: Session, route_id: str) -> dict:
    """
    Check if a route execution represents an anomaly in duration, fuel, or detour.
    Returns anomaly flag, score, and explanation reasons.
    """
    import uuid as _uuid
    try:
        route_uuid = _uuid.UUID(str(route_id))
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid route ID format: '{route_id}'")

    route = db.query(Route).filter(Route.id == route_uuid).first()
    if not route:
        raise ValueError(f"Route with ID '{route_id}' not found.")

    dist = float(route.total_distance_km or 100.0)
    actual_fuel = float(route.actual_fuel_l or 20.0)

    # Compute features
    expected_eff = 5.0
    if route.vehicle:
        expected_eff = float(route.vehicle.fuel_efficiency_kmpl)
    actual_eff = dist / max(actual_fuel, 1.0)
    fuel_gap = expected_eff - actual_eff

    est_dur = float(route.estimated_duration_min or 120.0)
    act_dur = float(route.actual_duration_min or est_dur)
    dur_ratio = act_dur / est_dur

    straight_dist = city_distance_km(route.origin_city, route.destination_city)
    dist_ratio = dist / max(straight_dist, 1.0)

    model = _model_cache["model"]
    if model is None:
        try:
            train_anomaly_model(db)
            model = _model_cache["model"]
        except Exception:
            pass

    is_anomaly = False
    score = 0.0

    if model is not None:
        features = np.array([[fuel_gap, dur_ratio, dist_ratio]])
        pred = model.predict(features)[0]  # -1 = anomaly, 1 = normal
        is_anomaly = (pred == -1)
        score = float(model.score_samples(features)[0])
    else:
        # Heuristic fallback
        if fuel_gap > 2.2:  # High fuel usage gap
            is_anomaly = True
        if dur_ratio > 1.8:  # 80% slower than expected
            is_anomaly = True
        if dist_ratio > 1.6:  # massive detour
            is_anomaly = True
        score = -0.6 if is_anomaly else 0.1

    # Explain reasons
    reasons = []
    if fuel_gap > 1.5:
        reasons.append(f"Unusually high fuel consumption (gap of {fuel_gap:.1f} KMPL vs nominal)")
    if dur_ratio > 1.4:
        reasons.append(f"Significant trip duration delay ({dur_ratio:.1f}x estimated travel time)")
    if dist_ratio > 1.4:
        reasons.append(f"Excessive road detour route taken ({dist_ratio:.1f}x straight line distance)")

    if not reasons:
        reasons.append("Trip completed within standard parameters")

    explanation = reasons  # return as list for API consumers

    result = {
        "route_id": route_id,
        "is_anomaly": bool(is_anomaly),
        "anomaly_score": round(score, 3),
        "explanation": explanation,
        "features": {
            "fuel_gap_kmpl": round(fuel_gap, 2),
            "duration_ratio": round(dur_ratio, 2),
            "distance_ratio": round(dist_ratio, 2),
        }
    }

    # Store prediction log in DB
    pred_log = ModelPrediction(
        model_name="anomaly_detector",
        model_version=_model_cache["version"],
        training_date=_model_cache["training_date"] or datetime.now(timezone.utc),
        feature_info={
            "fuel_gap": fuel_gap,
            "dur_ratio": dur_ratio,
            "dist_ratio": dist_ratio,
        },
        evaluation_metrics={"contamination": 0.1},
        target_entity_type="trip",
        target_entity_id=str(route_id),
        prediction_value={**result, "explanation": " | ".join(explanation)},
        risk_level="HIGH" if is_anomaly else "LOW",
        explanation=" | ".join(explanation),
        prediction_timestamp=datetime.now(timezone.utc),
    )
    db.add(pred_log)
    db.commit()

    return result
