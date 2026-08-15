"""
Stub routers for domains not yet implemented in Phase 1.
Each router returns a clear "not yet implemented" response so the
frontend can be built progressively without 404 errors.
"""
from fastapi import APIRouter

# ── Routes / Optimization ─────────────────────────────────
routes_router = APIRouter(prefix="/routes", tags=["Routes & Optimization"])

@routes_router.get("", summary="[Phase 2] List routes")
def list_routes():
    return {"message": "Routes API — implemented in Phase 2", "items": [], "total": 0}

@routes_router.post("/optimize", summary="[Phase 2] Trigger VRP optimization")
def optimize_routes():
    return {"message": "Route optimization — implemented in Phase 2"}


# ── Incidents ─────────────────────────────────────────────
incidents_router = APIRouter(prefix="/incidents", tags=["Incidents"])

@incidents_router.get("", summary="[Phase 4] List incidents")
def list_incidents():
    return {"message": "Incidents API — implemented in Phase 4", "items": [], "total": 0}


# ── Analytics ─────────────────────────────────────────────
analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])

@analytics_router.get("/dashboard", summary="[Phase 6] KPI dashboard")
def analytics_dashboard():
    return {"message": "Analytics API — implemented in Phase 6"}


# ── Notifications ─────────────────────────────────────────
notifications_router = APIRouter(prefix="/notifications", tags=["Notifications"])

@notifications_router.get("", summary="[Phase 4] List notifications")
def list_notifications():
    return {"message": "Notifications API — implemented in Phase 4", "items": [], "total": 0}


# ── Admin ─────────────────────────────────────────────────
admin_router = APIRouter(prefix="/admin", tags=["Admin"])

@admin_router.get("/system-stats", summary="[Phase 7] System statistics")
def system_stats():
    return {"message": "Admin API — implemented in Phase 7"}
