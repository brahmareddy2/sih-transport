"""
Vehicle model — represents the Fleet Digital Twin entity.
Covers Indian vehicle types: mini_truck, tempo, medium_truck, large_truck, trailer.
"""
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Double, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Indian registration format: MH12AB1234
    registration_number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    # Indian commercial vehicle types
    vehicle_type: Mapped[str] = mapped_column(
        String(30), nullable=False
        # mini_truck | tempo | medium_truck | large_truck | trailer
    )
    make: Mapped[str | None] = mapped_column(String(50))   # Tata, Ashok Leyland, Mahindra, Volvo
    model_name: Mapped[str | None] = mapped_column(String(50))  # Ace, 407, 2518, FH
    year: Mapped[int | None] = mapped_column()

    # Cargo capacity
    capacity_weight_kg: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    capacity_volume_m3: Mapped[float | None] = mapped_column(Numeric(8, 2))

    # Fuel information
    fuel_type: Mapped[str] = mapped_column(
        String(15), nullable=False
        # diesel | petrol | cng | ev
    )
    fuel_efficiency_kmpl: Mapped[float] = mapped_column(
        Numeric(6, 2), nullable=False  # km per liter
    )
    fuel_tank_capacity_l: Mapped[float | None] = mapped_column(Numeric(8, 2))
    current_fuel_level_l: Mapped[float | None] = mapped_column(Numeric(8, 2))

    # Current location (updated by driver app / GPS)
    current_lat: Mapped[float | None] = mapped_column(Double())
    current_lon: Mapped[float | None] = mapped_column(Double())
    current_city: Mapped[str | None] = mapped_column(String(100))

    # Odometer
    odometer_km: Mapped[float] = mapped_column(Numeric(10, 2), default=0)

    # Operational status
    status: Mapped[str] = mapped_column(
        String(20), default="available"
        # available | in_transit | maintenance | breakdown | idle
    )

    # Maintenance tracking
    last_service_date: Mapped[date | None] = mapped_column(Date())
    next_service_due_km: Mapped[float | None] = mapped_column(Numeric(10, 2))
    insurance_expiry: Mapped[date | None] = mapped_column(Date())
    permit_expiry: Mapped[date | None] = mapped_column(Date())

    # Special capabilities
    is_refrigerated: Mapped[bool] = mapped_column(Boolean, default=False)
    can_carry_hazmat: Mapped[bool] = mapped_column(Boolean, default=False)

    home_depot_city: Mapped[str | None] = mapped_column(String(100))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    driver: Mapped["Driver"] = relationship("Driver", back_populates="assigned_vehicle", uselist=False)
    routes: Mapped[list["Route"]] = relationship("Route", back_populates="vehicle")
    incidents: Mapped[list["Incident"]] = relationship("Incident", back_populates="vehicle")
    location_history: Mapped[list["VehicleLocationHistory"]] = relationship(
        "VehicleLocationHistory", back_populates="vehicle"
    )
    maintenance_records: Mapped[list["MaintenanceRecord"]] = relationship(
        "MaintenanceRecord", back_populates="vehicle"
    )

    def __repr__(self) -> str:
        return f"<Vehicle {self.registration_number} ({self.vehicle_type}) status={self.status}>"
