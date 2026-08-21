"""
Shipment models:
  - Shipment: a single shipment request
  - ShipmentConsolidationGroup: a group of consolidated shipments
  - ShipmentGroupMember: many-to-many link table
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Double, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Shipment(Base):
    __tablename__ = "shipments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Human-readable number: SHP-2024-00001
    shipment_number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )

    # Origin
    origin_city: Mapped[str] = mapped_column(String(100), nullable=False)
    origin_address: Mapped[str] = mapped_column(Text, nullable=False)
    origin_lat: Mapped[float] = mapped_column(Double(), nullable=False)
    origin_lon: Mapped[float] = mapped_column(Double(), nullable=False)

    # Destination
    destination_city: Mapped[str] = mapped_column(String(100), nullable=False)
    destination_address: Mapped[str] = mapped_column(Text, nullable=False)
    destination_lat: Mapped[float] = mapped_column(Double(), nullable=False)
    destination_lon: Mapped[float] = mapped_column(Double(), nullable=False)

    # Cargo details
    weight_kg: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    volume_m3: Mapped[float | None] = mapped_column(Numeric(8, 2))
    goods_type: Mapped[str | None] = mapped_column(
        String(50)
        # FMCG | Pharmaceutical | Automotive | Electronics | Chemicals | Textiles | Perishables
    )
    is_hazardous: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_refrigeration: Mapped[bool] = mapped_column(Boolean, default=False)

    # Priority and time constraints
    priority: Mapped[str] = mapped_column(String(10), default="normal")
    # urgent | high | normal | low
    requested_pickup_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    time_window_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    time_window_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Value (INR)
    declared_value_inr: Mapped[float | None] = mapped_column(Numeric(12, 2))

    # Status lifecycle
    status: Mapped[str] = mapped_column(String(25), default="pending")
    # pending | consolidated | assigned | in_transit | delivered | cancelled | delayed

    assigned_route_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routes.id"), nullable=True
    )
    assigned_vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=True
    )
    assigned_driver_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id"), nullable=True
    )
    delay_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    customer: Mapped["User"] = relationship("User", foreign_keys=[customer_id])
    route: Mapped["Route"] = relationship(
        "Route", foreign_keys=[assigned_route_id], back_populates="shipments"
    )
    route_stops: Mapped[list["RouteStop"]] = relationship(
        "RouteStop", back_populates="shipment"
    )
    group_memberships: Mapped[list["ShipmentGroupMember"]] = relationship(
        "ShipmentGroupMember", back_populates="shipment"
    )

    def __repr__(self) -> str:
        return f"<Shipment {self.shipment_number} {self.origin_city}→{self.destination_city} status={self.status}>"


class ShipmentConsolidationGroup(Base):
    __tablename__ = "shipment_consolidation_groups"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    group_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    total_weight_kg: Mapped[float | None] = mapped_column(Numeric(10, 2))
    total_volume_m3: Mapped[float | None] = mapped_column(Numeric(8, 2))
    origin_city: Mapped[str | None] = mapped_column(String(100))
    destination_city: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    members: Mapped[list["ShipmentGroupMember"]] = relationship(
        "ShipmentGroupMember", back_populates="group"
    )


class ShipmentGroupMember(Base):
    __tablename__ = "shipment_group_members"

    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shipment_consolidation_groups.id"), primary_key=True
    )
    shipment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shipments.id"), primary_key=True
    )

    group: Mapped["ShipmentConsolidationGroup"] = relationship(
        "ShipmentConsolidationGroup", back_populates="members"
    )
    shipment: Mapped["Shipment"] = relationship(
        "Shipment", back_populates="group_memberships"
    )
