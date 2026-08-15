"""
Return Cargo and Empty-Kilometer Reduction models.
Phase 6: Models for matching vehicles on return legs with pending shipments
to minimize deadhead / empty kilometers.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Double, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ReturnCargoMatch(Base):
    __tablename__ = "return_cargo_matches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False, index=True
    )
    shipment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shipments.id"), nullable=False, index=True
    )
    route_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routes.id"), nullable=True
    )
    return_route_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routes.id"), nullable=True
    )

    # Locations
    origin_city: Mapped[str] = mapped_column(String(100), nullable=False)
    destination_city: Mapped[str] = mapped_column(String(100), nullable=False)
    vehicle_current_city: Mapped[str] = mapped_column(String(100), nullable=False)
    vehicle_home_city: Mapped[str] = mapped_column(String(100), nullable=False)

    # Distance & Empty-KM Metrics (km)
    empty_km_before: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0.0)
    empty_km_after: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0.0)
    empty_km_reduced: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0.0)
    empty_km_reduction_pct: Mapped[float] = mapped_column(Numeric(6, 2), default=0.0)
    loaded_distance_km: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)
    detour_distance_km: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)

    # Financial & Fuel Metrics (INR / Litres)
    additional_fuel_l: Mapped[float] = mapped_column(Numeric(8, 2), default=0.0)
    additional_fuel_cost_inr: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    additional_toll_cost_inr: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    total_additional_cost_inr: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    estimated_revenue_inr: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    net_benefit_inr: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)

    # Scoring & Details
    match_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0, index=True)
    compatibility_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Lifecycle status: pending | approved | rejected | completed
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Approval tracking
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    vehicle: Mapped["Vehicle"] = relationship("Vehicle", foreign_keys=[vehicle_id])
    shipment: Mapped["Shipment"] = relationship("Shipment", foreign_keys=[shipment_id])
    original_route: Mapped["Route"] = relationship("Route", foreign_keys=[route_id])
    return_route: Mapped["Route"] = relationship("Route", foreign_keys=[return_route_id])

    def __repr__(self) -> str:
        return (
            f"<ReturnCargoMatch vehicle={self.vehicle_id} shipment={self.shipment_id} "
            f"score={self.match_score} status={self.status}>"
        )
