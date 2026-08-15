"""Models package — import all models here so Alembic can discover them."""

from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.models.shipment import Shipment, ShipmentConsolidationGroup, ShipmentGroupMember
from app.models.route import Route, RouteStop
from app.models.incident import Incident, RecoveryPlan
from app.models.analytics import (
    FuelStation,
    ServiceCenter,
    VehicleLocationHistory,
    MaintenanceRecord,
    DemandForecast,
    AnalyticsDaily,
)
from app.models.notification import Notification
from app.models.audit_log import AuditLog
from app.models.prediction import ModelPrediction
from app.models.return_cargo import ReturnCargoMatch

__all__ = [
    "User",
    "Vehicle",
    "Driver",
    "Shipment",
    "ShipmentConsolidationGroup",
    "ShipmentGroupMember",
    "Route",
    "RouteStop",
    "Incident",
    "RecoveryPlan",
    "FuelStation",
    "ServiceCenter",
    "VehicleLocationHistory",
    "MaintenanceRecord",
    "DemandForecast",
    "AnalyticsDaily",
    "Notification",
    "AuditLog",
    "ModelPrediction",
    "ReturnCargoMatch",
]
