"""
Incident and RecoveryPlan models.
Incidents are disruptions reported by drivers or detected by the system.
RecoveryPlans are generated recommendations to handle incidents.
Phase 5: Added affected_shipment_ids, detected_at to Incident;
         Added plan_type, plan_description, alternative_driver_id,
         additional_distance_km, recovery_score to RecoveryPlan.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Double, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    route_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routes.id")
    )
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id")
    )
    driver_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id")
    )

    incident_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # breakdown | tyre_puncture | accident | traffic_jam |
    # road_closure | low_fuel | driver_unavailable | weather_disruption | delay | other

    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    # low | medium | high | critical

    description: Mapped[str | None] = mapped_column(Text)

    lat: Mapped[float | None] = mapped_column(Double())
    lon: Mapped[float | None] = mapped_column(Double())
    city: Mapped[str | None] = mapped_column(String(100))

    source: Mapped[str | None] = mapped_column(String(20))
    # driver | system | weather_api | manual

    reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    detected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    status: Mapped[str] = mapped_column(String(20), default="open")
    # open | acknowledged | in_recovery | resolved | closed

    # Phase 5: list of affected shipment UUID strings (stored as JSON array)
    affected_shipment_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    route: Mapped["Route"] = relationship("Route", back_populates="incidents")
    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="incidents")
    driver: Mapped["Driver"] = relationship("Driver", back_populates="incidents")
    recovery_plans: Mapped[list["RecoveryPlan"]] = relationship(
        "RecoveryPlan", back_populates="incident"
    )

    def __repr__(self) -> str:
        return f"<Incident {self.incident_type} severity={self.severity} status={self.status}>"


class RecoveryPlan(Base):
    __tablename__ = "recovery_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False
    )
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False)
    action_type: Mapped[str | None] = mapped_column(String(30))
    # reassign_vehicle | reroute | delay_shipment | transfer_cargo | find_fuel | find_workshop | cancel

    # Phase 5: richer plan metadata
    plan_type: Mapped[str | None] = mapped_column(String(30))
    # replace_vehicle | replace_vehicle_and_driver | reroute | fuel_stop | delay_only
    plan_description: Mapped[str | None] = mapped_column(Text)

    alternative_vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id")
    )
    alternative_driver_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id")
    )
    rerouted_route_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routes.id")
    )
    estimated_delay_min: Mapped[int | None] = mapped_column(Integer())
    cost_impact_inr: Mapped[float | None] = mapped_column(Numeric(12, 2))
    additional_distance_km: Mapped[float | None] = mapped_column(Numeric(10, 2))
    recovery_score: Mapped[float | None] = mapped_column(Numeric(5, 2))

    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    incident: Mapped["Incident"] = relationship("Incident", back_populates="recovery_plans")
    alternative_vehicle: Mapped["Vehicle"] = relationship(
        "Vehicle", foreign_keys=[alternative_vehicle_id]
    )
    alternative_driver: Mapped["Driver"] = relationship(
        "Driver", foreign_keys=[alternative_driver_id]
    )
