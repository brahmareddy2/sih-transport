import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class TripCost(Base):
    __tablename__ = "trip_costs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id = Column(UUID(as_uuid=True), ForeignKey("routes.id", ondelete="CASCADE"), nullable=False, unique=True)
    fuel_cost = Column(Numeric(12, 2), nullable=False, default=0.0)
    toll_cost = Column(Numeric(12, 2), nullable=False, default=0.0)
    driver_allowance = Column(Numeric(12, 2), nullable=False, default=0.0)
    other_overhead = Column(Numeric(12, 2), nullable=False, default=0.0)
    revenue = Column(Numeric(12, 2), nullable=False, default=0.0)
    
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    route = relationship("Route", back_populates="trip_cost")
