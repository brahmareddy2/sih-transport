"""
AI/ML Demand Forecasting Engine.
Trains a RandomForestRegressor to predict inter-city shipment counts.
"""
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import numpy as np
from sqlalchemy.orm import Session

# Try imports
try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import root_mean_squared_error, mean_absolute_error
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from app.models.shipment import Shipment
from app.models.prediction import ModelPrediction
from app.models.analytics import DemandForecast
from app.services.optimization.distance_matrix import CITY_NAMES

logger = logging.getLogger(__name__)

# Cache for trained model (in-memory singleton)
_model_cache: dict = {
    "model": None,
    "version": "v1.0",
    "training_date": None,
    "metrics": {},
    "features": ["weekday", "month", "origin_idx", "dest_idx"],
}

# Categorical mapping for cities
CITY_MAP = {city: idx for idx, city in enumerate(CITY_NAMES)}


def train_demand_model(db: Session) -> dict:
    """
    Fetch historical shipment data, prepare features, train RandomForestRegressor,
    evaluate on test set, and store metrics in the database.
    """
    if not SKLEARN_AVAILABLE:
        raise RuntimeError("scikit-learn not available. Install dependencies first.")

    # 1. Fetch completed shipments
    shipments = db.query(Shipment).filter(Shipment.status == "delivered").all()
    if len(shipments) < 30:
        # Generate synthetic history for training if database has sparse records
        logger.info("Insufficient delivered shipments (%d) for ML training. Simulating history...", len(shipments))
        shipments = _simulate_shipment_history(db)

    # 2. Group by date and origin-destination to create sample rows
    # Target: total shipment count on a given day for a city pair
    data_points: dict[tuple[date, str, str], list[float]] = {}
    for s in shipments:
        # Handle date conversion
        ship_date = s.requested_pickup_time.date() if isinstance(s.requested_pickup_time, datetime) else s.requested_pickup_time
        if not ship_date:
            continue
        key = (ship_date, s.origin_city, s.destination_city)
        if key not in data_points:
            data_points[key] = []
        data_points[key].append(float(s.weight_kg))

    # Compile dataset array
    X = []
    y_count = []
    y_weight = []

    for (s_date, origin, dest), weights in data_points.items():
        o_idx = CITY_MAP.get(origin, 0)
        d_idx = CITY_MAP.get(dest, 0)
        weekday = s_date.weekday()
        month = s_date.month

        X.append([weekday, month, o_idx, d_idx])
        y_count.append(len(weights))
        y_weight.append(sum(weights))

    X_arr = np.array(X)
    y_count_arr = np.array(y_count)
    y_weight_arr = np.array(y_weight)

    if len(X_arr) < 10:
        raise ValueError(f"Not enough data points ({len(X_arr)}) to train demand model.")

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X_arr, y_count_arr, test_size=0.2, random_state=42)

    # Train model
    model = RandomForestRegressor(n_estimators=50, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    rmse = root_mean_squared_error(y_test, predictions)
    r2 = float(model.score(X_test, y_test))

    # Calculate MAPE safely (avoid division by zero)
    non_zero = y_test > 0
    if np.any(non_zero):
        mape = float(np.mean(np.abs((y_test[non_zero] - predictions[non_zero]) / y_test[non_zero])) * 100)
    else:
        mape = 0.0

    metrics = {
        "mae": round(float(mae), 3),
        "rmse": round(float(rmse), 3),
        "mape_pct": round(mape, 2),
        "r2": round(r2, 3),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
    }

    # Cache locally
    _model_cache["model"] = model
    _model_cache["training_date"] = datetime.now(timezone.utc)
    _model_cache["metrics"] = metrics

    # Log/persist model performance metadata in ModelPrediction DB
    pred_log = ModelPrediction(
        model_name="demand_forecasting",
        model_version=_model_cache["version"],
        training_date=_model_cache["training_date"],
        feature_info={"features": _model_cache["features"]},
        evaluation_metrics=metrics,
        target_entity_type="system",
        target_entity_id="global_demand",
        prediction_value={"status": "trained"},
        prediction_timestamp=datetime.now(timezone.utc),
    )
    db.add(pred_log)
    db.commit()

    logger.info("Demand forecasting model trained. RMSE: %.3f, MAE: %.3f", rmse, mae)
    return metrics


def predict_demand(db: Session, origin: str, destination: str, target_date: date) -> dict:
    """
    Predict shipment count and weight for a future date and city pair.
    Uses trained model, falls back to historical averages if model not trained.
    """
    o_idx = CITY_MAP.get(origin, 0)
    d_idx = CITY_MAP.get(destination, 0)
    weekday = target_date.weekday()
    month = target_date.month

    # Check cache
    model = _model_cache["model"]
    if model is None:
        # Try to train or fallback to baseline
        try:
            train_demand_model(db)
            model = _model_cache["model"]
        except Exception as e:
            logger.warning("Could not auto-train demand model (%s) — using historical baseline", e)

    predicted_count = 0.0
    if model is not None:
        features = np.array([[weekday, month, o_idx, d_idx]])
        predicted_count = float(model.predict(features)[0])
    else:
        # Baseline fallback: rolling average shipments per city pair on that weekday
        historical = db.query(Shipment).filter(
            Shipment.origin_city == origin,
            Shipment.destination_city == destination,
        ).all()
        if historical:
            counts = [1 for s in historical if s.requested_pickup_time.weekday() == weekday]
            predicted_count = sum(counts) / max(len(counts), 1)
        else:
            predicted_count = 1.2  # default fallback

    # Add realistic bounds (confidence intervals)
    rmse = _model_cache["metrics"].get("rmse", 0.8)
    confidence_lower = max(0, int(predicted_count - 1.96 * rmse))
    confidence_upper = int(predicted_count + 1.96 * rmse) + 1

    # Predicted weight (estimated average weight per shipment is ~1800 kg)
    predicted_weight = round(predicted_count * 1800.0, 1)

    horizon_days = (target_date - date.today()).days if isinstance(target_date, date) else 7
    result = {
        "predicted_shipments": max(1, int(round(predicted_count))),
        "predicted_weight_kg": predicted_weight,
        "confidence_lower": confidence_lower,
        "confidence_upper": confidence_upper,
        "model_version": _model_cache["version"],
        "origin_city": origin,
        "destination_city": destination,
        "target_date": str(target_date),
        "prediction_horizon_days": max(1, horizon_days),
        "model_mae": _model_cache["metrics"].get("mae"),
    }

    # Save output to demand_forecasts table
    forecast = DemandForecast(
        origin_city=origin,
        destination_city=destination,
        forecast_date=target_date,
        predicted_shipments=result["predicted_shipments"],
        predicted_weight_kg=result["predicted_weight_kg"],
        confidence_lower=result["confidence_lower"],
        confidence_upper=result["confidence_upper"],
        model_version=result["model_version"],
    )
    db.add(forecast)
    db.commit()

    return result


def _simulate_shipment_history(db: Session) -> list[Shipment]:
    """Helper to generate internal simulated deliveries for training."""
    from app.services.seed_data.generator import generate_shipments
    sim_shipments = generate_shipments(200)
    db_shipments = []
    for s in sim_shipments:
        ship = Shipment(
            shipment_number=s["shipment_number"] + "-SIM",
            origin_city=s["origin_city"],
            origin_address=s["origin_address"],
            origin_lat=s["origin_lat"],
            origin_lon=s["origin_lon"],
            destination_city=s["destination_city"],
            destination_address=s["destination_address"],
            destination_lat=s["destination_lat"],
            destination_lon=s["destination_lon"],
            weight_kg=s["weight_kg"],
            volume_m3=s["volume_m3"],
            goods_type=s["goods_type"],
            is_hazardous=s["is_hazardous"],
            requires_refrigeration=s["requires_refrigeration"],
            priority=s["priority"],
            requested_pickup_time=s["requested_pickup_time"] - timedelta(days=30),
            status="delivered",
        )
        db.add(ship)
        db_shipments.append(ship)
    db.commit()
    return db_shipments
