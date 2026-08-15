"""
ModelPrediction model — stores machine learning prediction logs,
model versions, training date, and evaluation metrics.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ModelPrediction(Base):
    __tablename__ = "model_predictions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    model_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # e.g. "demand_forecasting" | "delay_prediction" | "vehicle_risk" | "anomaly_detector"

    model_version: Mapped[str] = mapped_column(String(20), nullable=False, default="v1.0")
    training_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Stores list of inputs or feature column keys used in training
    feature_info: Mapped[dict | None] = mapped_column(JSON)

    # Stores evaluation metrics like RMSE, F1-Score, Precision, Recall
    evaluation_metrics: Mapped[dict | None] = mapped_column(JSON)

    # Target entity details
    target_entity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # e.g., "shipment" | "vehicle" | "trip" | "system"
    target_entity_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Stores prediction outputs: probability, forecasted value, anomaly flag
    prediction_value: Mapped[dict] = mapped_column(JSON, nullable=False)

    risk_level: Mapped[str | None] = mapped_column(String(20))
    # e.g., LOW | MEDIUM | HIGH

    explanation: Mapped[str | None] = mapped_column(Text)
    # Explainable reasons: e.g., "High delay history on this segment"

    prediction_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    def __repr__(self) -> str:
        return f"<ModelPrediction model={self.model_name} version={self.model_version} target={self.target_entity_id}>"
