"""
Driver model — linked to a User (role='driver') and optionally to a Vehicle.
Tracks Indian driving license types (LMV, HMV, HPMV) and work hours.
"""
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True
    )
    employee_id: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    license_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    license_type: Mapped[str | None] = mapped_column(
        String(10)
        # LMV | HMV | HPMV (Indian license categories)
    )
    license_expiry: Mapped[date | None] = mapped_column(Date())

    assigned_vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id")
    )

    status: Mapped[str] = mapped_column(
        String(20), default="available"
        # available | on_trip | off_duty | on_leave | unavailable
    )
    home_city: Mapped[str | None] = mapped_column(String(100))
    experience_years: Mapped[int | None] = mapped_column()
    total_trips: Mapped[int] = mapped_column(default=0)
    on_time_delivery_rate: Mapped[float | None] = mapped_column(
        Numeric(5, 2)  # percentage 0–100
    )

    # Hours driven today and this week (for fatigue / compliance monitoring)
    hours_driven_today: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    hours_driven_this_week: Mapped[float] = mapped_column(Numeric(5, 2), default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="driver_profile")
    assigned_vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="driver")
    routes: Mapped[list["Route"]] = relationship("Route", back_populates="driver")
    incidents: Mapped[list["Incident"]] = relationship("Incident", back_populates="driver")

    @property
    def full_name(self) -> str:
        """Convenience: return user's full name or employee_id as fallback."""
        if self.user and self.user.full_name:
            return self.user.full_name
        return self.employee_id

    def __repr__(self) -> str:
        return f"<Driver {self.employee_id} status={self.status}>"
