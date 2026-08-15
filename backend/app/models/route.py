"""
Route and RouteStop models.
Route = one vehicle trip covering multiple shipment stops.
RouteStop = one individual pickup or delivery point on a route.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Double, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Route(Base):
    __tablename__ = "routes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    route_number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id")
    )
    driver_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id")
    )
    origin_city: Mapped[str | None] = mapped_column(String(100))
    destination_city: Mapped[str | None] = mapped_column(String(100))

    # ── Distance & Time ──────────────────────────────────
    total_distance_km: Mapped[float | None] = mapped_column(Numeric(10, 2))
    estimated_duration_min: Mapped[int | None] = mapped_column(Integer())
    actual_duration_min: Mapped[int | None] = mapped_column(Integer())

    # ── Cost breakdown (INR) ─────────────────────────────
    estimated_fuel_l: Mapped[float | None] = mapped_column(Numeric(8, 2))
    actual_fuel_l: Mapped[float | None] = mapped_column(Numeric(8, 2))
    estimated_fuel_cost_inr: Mapped[float | None] = mapped_column(Numeric(12, 2))
    actual_fuel_cost_inr: Mapped[float | None] = mapped_column(Numeric(12, 2))
    estimated_toll_inr: Mapped[float | None] = mapped_column(Numeric(12, 2))
    actual_toll_inr: Mapped[float | None] = mapped_column(Numeric(12, 2))
    estimated_co2_kg: Mapped[float | None] = mapped_column(Numeric(8, 2))
    actual_co2_kg: Mapped[float | None] = mapped_column(Numeric(8, 2))
    driver_cost_inr: Mapped[float | None] = mapped_column(Numeric(12, 2))
    total_estimated_cost_inr: Mapped[float | None] = mapped_column(Numeric(12, 2))
    total_actual_cost_inr: Mapped[float | None] = mapped_column(Numeric(12, 2))

    # ── Optimization metadata ────────────────────────────
    optimization_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    road_type: Mapped[str] = mapped_column(String(20), default="mixed")
    # nh_only | mixed | local

    # ── Timing ───────────────────────────────────────────
    planned_start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    planned_end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ── Status lifecycle ─────────────────────────────────
    status: Mapped[str] = mapped_column(String(20), default="planned")
    # planned | in_progress | completed | cancelled | delayed

    # ── Route geometry (from ORS) ────────────────────────
    polyline: Mapped[str | None] = mapped_column(Text)          # Encoded polyline
    waypoints_json: Mapped[dict | None] = mapped_column(JSONB)  # Full waypoints
    optimization_meta: Mapped[dict | None] = mapped_column(JSONB)  # OR-Tools metadata

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="routes")
    driver: Mapped["Driver"] = relationship("Driver", back_populates="routes")
    stops: Mapped[list["RouteStop"]] = relationship(
        "RouteStop", back_populates="route", order_by="RouteStop.stop_sequence",
        cascade="all, delete-orphan"
    )
    shipments: Mapped[list["Shipment"]] = relationship(
        "Shipment", foreign_keys="Shipment.assigned_route_id", back_populates="route"
    )
    incidents: Mapped[list["Incident"]] = relationship("Incident", back_populates="route")

    def __repr__(self) -> str:
        return f"<Route {self.route_number} {self.origin_city}→{self.destination_city} status={self.status}>"


class RouteStop(Base):
    __tablename__ = "route_stops"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    route_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routes.id", ondelete="CASCADE"), nullable=False
    )
    shipment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shipments.id")
    )
    stop_sequence: Mapped[int] = mapped_column(Integer(), nullable=False)
    stop_type: Mapped[str | None] = mapped_column(String(15))
    # pickup | delivery | depot | fuel_stop

    city: Mapped[str | None] = mapped_column(String(100))
    address: Mapped[str | None] = mapped_column(Text)
    lat: Mapped[float | None] = mapped_column(Double())
    lon: Mapped[float | None] = mapped_column(Double())

    planned_arrival: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    planned_departure: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_arrival: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_departure: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    distance_from_prev_km: Mapped[float | None] = mapped_column(Numeric(8, 2))
    status: Mapped[str] = mapped_column(String(15), default="pending")
    # pending | arrived | completed | skipped

    # Relationships
    route: Mapped["Route"] = relationship("Route", back_populates="stops")
    shipment: Mapped["Shipment"] = relationship("Shipment", back_populates="route_stops")
