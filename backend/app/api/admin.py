"""
Phase 7 — Admin and System Statistics API Router.

Provides real-time platform diagnostic status, resource counts, and uptime.
"""
import logging
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.route import Route
from app.models.shipment import Shipment
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.analytics import SystemStatsResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin & System"])

_START_TIME = time.time()


@router.get(
    "/system-stats",
    response_model=SystemStatsResponse,
    summary="Platform System Diagnostics & Statistics",
)
def get_system_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "operator")),
):
    """Return health of core components, database connection, and tracked entity counts."""
    db_connected = False
    try:
        db.execute(text("SELECT 1"))
        db_connected = True
    except Exception as e:
        logger.warning("DB ping check failed: %s", e)

    veh_count = db.query(Vehicle).count()
    shp_count = db.query(Shipment).count()
    routes_count = db.query(Route).count()

    uptime = round(time.time() - _START_TIME, 1)

    return {
        "status": "healthy" if db_connected else "degraded",
        "version": "1.0.0-phase7",
        "database_connected": db_connected,
        "total_vehicles_active": veh_count,
        "total_shipments_tracked": shp_count,
        "total_routes_active": routes_count,
        "active_websockets_count": 1,
        "uptime_seconds": uptime,
        "environment": get_settings().environment,
        "timestamp": datetime.now(timezone.utc),
    }
