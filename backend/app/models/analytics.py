"""
Analytics and supporting reference models:
  - FuelStation: IOCL/BPCL/HPCL fuel stations on Indian highways
  - ServiceCenter: workshops and tyre shops
  - VehicleLocationHistory: GPS breadcrumbs
  - MaintenanceRecord: service and repair history
  - DemandForecast: ML-predicted shipment demand
  - AnalyticsDaily: pre-aggregated daily KPIs
"""
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Double, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class FuelStation(Base):
    __tablename__ = "fuel_stations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    # e.g. "Indian Oil — NH48 Pune Bypass"
    operator: Mapped[str | None] = mapped_column(String(50))
    # IOCL | BPCL | HPCL | Reliance | Essar

    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(50))
    lat: Mapped[float] = mapped_column(Double(), nullable=False)
    lon: Mapped[float] = mapped_column(Double(), nullable=False)
    address: Mapped[str | None] = mapped_column(Text)

    # Stored as a plain comma-separated string for SQLite compatibility
    # In PostgreSQL we use ARRAY but fallback to string for portability
    fuel_types_available: Mapped[str | None] = mapped_column(String(100), default="diesel")
    # e.g. "diesel,petrol,cng"

    is_24h: Mapped[bool] = mapped_column(Boolean, default=False)
    has_truck_parking: Mapped[bool] = mapped_column(Boolean, default=False)
    rating: Mapped[float | None] = mapped_column(Numeric(3, 1))


class ServiceCenter(Base):
    __tablename__ = "service_centers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    service_type: Mapped[str | None] = mapped_column(String(20))
    # workshop | tyre_shop | full_service

    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(50))
    lat: Mapped[float] = mapped_column(Double(), nullable=False)
    lon: Mapped[float] = mapped_column(Double(), nullable=False)
    address: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(String(15))
    is_24h: Mapped[bool] = mapped_column(Boolean, default=False)
    specializations: Mapped[str | None] = mapped_column(String(200))
    # comma-separated: "tyre,engine,electrical"
    rating: Mapped[float | None] = mapped_column(Numeric(3, 1))


class VehicleLocationHistory(Base):
    __tablename__ = "vehicle_locations_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), __import__('sqlalchemy').ForeignKey("vehicles.id"), nullable=False, index=True
    )
    lat: Mapped[float] = mapped_column(Double(), nullable=False)
    lon: Mapped[float] = mapped_column(Double(), nullable=False)
    speed_kmh: Mapped[float | None] = mapped_column(Numeric(5, 1))
    heading_deg: Mapped[int | None] = mapped_column(Integer())
    fuel_level_l: Mapped[float | None] = mapped_column(Numeric(8, 2))
    trip_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="location_history")


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), __import__('sqlalchemy').ForeignKey("vehicles.id"), nullable=False
    )
    maintenance_type: Mapped[str | None] = mapped_column(String(30))
    # scheduled_service | tyre_replacement | engine_repair | brake_service | oil_change | breakdown_repair | other
    description: Mapped[str | None] = mapped_column(Text)
    workshop_name: Mapped[str | None] = mapped_column(String(200))
    city: Mapped[str | None] = mapped_column(String(100))
    cost_inr: Mapped[float | None] = mapped_column(Numeric(12, 2))
    odometer_at_service: Mapped[float | None] = mapped_column(Numeric(10, 2))
    serviced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_service_due_km: Mapped[float | None] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="maintenance_records")


class DemandForecast(Base):
    __tablename__ = "demand_forecasts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    origin_city: Mapped[str | None] = mapped_column(String(100))
    destination_city: Mapped[str | None] = mapped_column(String(100))
    forecast_date: Mapped[date] = mapped_column(Date(), nullable=False)
    predicted_shipments: Mapped[int | None] = mapped_column(Integer())
    predicted_weight_kg: Mapped[float | None] = mapped_column(Numeric(10, 2))
    confidence_lower: Mapped[int | None] = mapped_column(Integer())
    confidence_upper: Mapped[int | None] = mapped_column(Integer())
    model_version: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class AnalyticsDaily(Base):
    __tablename__ = "analytics_daily"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    date: Mapped[date] = mapped_column(Date(), unique=True, nullable=False, index=True)

    total_routes: Mapped[int] = mapped_column(Integer(), default=0)
    total_shipments_delivered: Mapped[int] = mapped_column(Integer(), default=0)
    total_distance_km: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    total_empty_km: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    total_fuel_l: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    total_fuel_cost_inr: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    total_toll_cost_inr: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    total_co2_kg: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    on_time_deliveries: Mapped[int] = mapped_column(Integer(), default=0)
    delayed_deliveries: Mapped[int] = mapped_column(Integer(), default=0)
    total_incidents: Mapped[int] = mapped_column(Integer(), default=0)
    avg_vehicle_utilization_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    total_revenue_inr: Mapped[float] = mapped_column(Numeric(14, 2), default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
