"""
FastAPI router for real-time tracking, WebSocket connections,
GPS simulation control, and location history queries — Phase 4.
"""
import logging
import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import (
    APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, status
)
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles, get_current_user as get_user_from_token
from app.core.security import decode_token
from app.models.user import User
from app.models.analytics import VehicleLocationHistory
from app.models.vehicle import Vehicle
from app.models.route import Route
from app.schemas.tracking import (
    VehicleStateResponse, LocationHistoryResponse, SimulationControlRequest
)
from app.services.tracking.gps_simulator import (
    SIMULATIONS, ACTIVE_CONNECTIONS, start_simulation, stop_simulation,
    pause_simulation, resume_simulation, get_vehicle_state, get_all_vehicle_states
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tracking", tags=["Fleet Tracking"])


# ── GET /vehicles ──────────────────────────────────────────────

@router.get("/vehicles", response_model=List[VehicleStateResponse], summary="List all vehicle locations & status")
def list_vehicle_states(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "fleet_operator", "driver")),
):
    """Retrieve the real-time telemetry state of all vehicles in the fleet (scoped for drivers)."""
    try:
        if current_user.role == "driver":
            from app.models.driver import Driver
            driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
            if not driver or not driver.assigned_vehicle_id:
                return []
            state = get_vehicle_state(driver.assigned_vehicle_id)
            return [state]
        return get_all_vehicle_states()
    except Exception as e:
        logger.error("Failed listing vehicle states: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── GET /vehicles/{vehicle_id} ─────────────────────────────────

@router.get("/vehicles/{vehicle_id}", response_model=VehicleStateResponse, summary="Get single vehicle tracking state")
def get_vehicle_tracking_state(
    vehicle_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "fleet_operator", "driver")),
):
    """Get the current position, speed, heading, and telemetry of a specific vehicle."""
    try:
        if current_user.role == "driver":
            from app.models.driver import Driver
            driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
            if not driver or driver.assigned_vehicle_id != vehicle_id:
                raise HTTPException(status_code=403, detail="Access denied. You can only track your assigned vehicle.")
        return get_vehicle_state(vehicle_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed fetching vehicle state: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── GET /vehicles/{vehicle_id}/history ─────────────────────────

@router.get("/vehicles/{vehicle_id}/history", response_model=List[LocationHistoryResponse], summary="Get vehicle location crumbs")
def get_vehicle_location_history(
    vehicle_id: uuid.UUID,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "fleet_operator", "driver")),
):
    """Get historical GPS breadcrumbs for a specific vehicle."""
    try:
        if current_user.role == "driver":
            from app.models.driver import Driver
            driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
            if not driver or driver.assigned_vehicle_id != vehicle_id:
                raise HTTPException(status_code=403, detail="Access denied. You can only query history for your assigned vehicle.")
        crumbs = db.query(VehicleLocationHistory).filter(
            VehicleLocationHistory.vehicle_id == vehicle_id
        ).order_by(VehicleLocationHistory.recorded_at.desc()).limit(limit).all()
        return crumbs
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed fetching location history: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── GET /trips/{trip_id}/location-history ──────────────────────

@router.get("/trips/{trip_id}/location-history", response_model=List[LocationHistoryResponse], summary="Get trip location crumbs")
def get_trip_location_history(
    trip_id: uuid.UUID,
    limit: int = Query(500, ge=1, le=2000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "fleet_operator")),
):
    """Get historical GPS breadcrumbs for a specific optimized trip/route."""
    try:
        crumbs = db.query(VehicleLocationHistory).filter(
            VehicleLocationHistory.trip_id == trip_id
        ).order_by(VehicleLocationHistory.recorded_at.desc()).limit(limit).all()
        return crumbs
    except Exception as e:
        logger.error("Failed fetching trip location history: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── Simulation Controls ───────────────────────────────────────

@router.post("/simulate/start", response_model=VehicleStateResponse, summary="Start GPS simulation")
def run_start_simulation(
    payload: SimulationControlRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "fleet_operator")),
):
    """Start simulated GPS movement for a vehicle along its route."""
    try:
        return start_simulation(payload.vehicle_id, payload.route_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to start simulation: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulate/pause", response_model=VehicleStateResponse, summary="Pause GPS simulation")
def run_pause_simulation(
    payload: SimulationControlRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "fleet_operator")),
):
    """Pause simulated GPS movement for a vehicle (setting status to STOPPED)."""
    try:
        return pause_simulation(payload.vehicle_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/simulate/resume", response_model=VehicleStateResponse, summary="Resume GPS simulation")
def run_resume_simulation(
    payload: SimulationControlRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "fleet_operator")),
):
    """Resume paused simulated GPS movement for a vehicle (setting status to IN_TRANSIT)."""
    try:
        return resume_simulation(payload.vehicle_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/simulate/stop", summary="Stop GPS simulation")
def run_stop_simulation(
    payload: SimulationControlRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "fleet_operator")),
):
    """Stop GPS simulation and mark route completed."""
    try:
        return stop_simulation(payload.vehicle_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── WebSocket Live Updates ─────────────────────────────────────

@router.websocket("/ws")
async def websocket_tracking(websocket: WebSocket, token: Optional[str] = Query(None)):
    """
    WebSocket endpoint for real-time fleet updates.
    Accepts JWT token as query parameter to authorize connection.
    """
    await websocket.accept()

    # Validate authentication
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token query parameter missing")
        return

    db = get_db()
    try:
        db_session = next(db)
        payload = decode_token(token)
        user_id = payload.get("sub")
        token_type = payload.get("type")
        if user_id is None or token_type != "access":
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            return

        user_uuid = uuid.UUID(user_id)
        user = db_session.query(User).filter(User.id == user_uuid, User.is_active == True).first()
        if not user or user.role not in ["admin", "operator", "fleet_manager", "driver"]:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Forbidden role access")
            return
            
    except Exception as e:
        logger.error("WebSocket auth failed: %s", e)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Auth validation failed")
        return
    finally:
        db.close()

    # Register active connection
    ACTIVE_CONNECTIONS.append({"socket": websocket, "role": user.role, "user_id": user.id})
    logger.info("WebSocket client connected. Active listeners: %d", len(ACTIVE_CONNECTIONS))

    try:
        # Keep client connection open, listen for control events or simple pings
        while True:
            data = await websocket.receive_text()
            # Simple ping-pong to keep connection alive
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected.")
    except Exception as e:
        logger.error("Error in websocket connection: %s", e)
    finally:
        for conn in list(ACTIVE_CONNECTIONS):
            if conn["socket"] == websocket:
                ACTIVE_CONNECTIONS.remove(conn)
