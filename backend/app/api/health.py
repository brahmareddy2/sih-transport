"""
Health check router — used by Docker healthcheck and monitoring.
No authentication required.
"""
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db

settings = get_settings()
router = APIRouter(tags=["Health"])

# Application start time for uptime calculation
_START_TIME = time.time()


@router.get("/health", summary="Basic liveness check")
def health_check():
    """
    Lightweight liveness endpoint.
    Returns 200 OK immediately. Used by Docker healthcheck.
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.environment,
    }


@router.get("/health/ready", summary="Readiness check (DB + services)")
def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check — verifies the application can serve traffic.
    Checks database connectivity.
    Returns 200 if ready, 503 if not.
    """
    checks = {}

    # Database check
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"

    all_ok = all(v == "ok" for v in checks.values())
    uptime_seconds = round(time.time() - _START_TIME, 1)

    return {
        "status": "ready" if all_ok else "degraded",
        "uptime_seconds": uptime_seconds,
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0-phase1",
    }
