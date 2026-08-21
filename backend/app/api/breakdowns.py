import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.models.shipment import Shipment
from app.models.route import Route, RouteStop
from app.models.notification import Notification
from app.models.breakdown import VehicleBreakdown
from app.services.tracking.gps_simulator import SIMULATIONS, get_vehicle_state
from app.services.optimization.distance_matrix import haversine_km

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/breakdowns", tags=["Vehicle Breakdowns"])


# ── Schemas ───────────────────────────────────────────────────

class BreakdownCreateSchema(BaseModel):
    vehicle_id: uuid.UUID
    trip_id: Optional[uuid.UUID] = None
    severity: str  # minor, major
    description: str


class BreakdownTransferSchema(BaseModel):
    target_vehicle_id: uuid.UUID


class BreakdownResolveSchema(BaseModel):
    resolution_notes: Optional[str] = None


class BreakdownResponseSchema(BaseModel):
    id: uuid.UUID
    vehicle_id: uuid.UUID
    trip_id: Optional[uuid.UUID]
    driver_id: uuid.UUID
    severity: str
    description: Optional[str]
    reported_at: datetime
    resolved_at: Optional[datetime]
    status: str

    class Config:
        from_attributes = True


# ── Endpoints ─────────────────────────────────────────────────

@router.post("", response_model=BreakdownResponseSchema, status_code=status.HTTP_201_CREATED)
def report_breakdown(
    payload: BreakdownCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reports a vehicle breakdown.
    Changes vehicle status, halts active simulations, generates notifications,
    and runs alternate vehicle routing search for major breakdowns.
    """
    # 1. Fetch vehicle
    vehicle = db.query(Vehicle).filter(Vehicle.id == payload.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # 2. Halt simulation if active
    v_str = str(vehicle.id)
    broken_lat = vehicle.current_lat or 19.0760
    broken_lon = vehicle.current_lon or 72.8777
    
    if v_str in SIMULATIONS:
        SIMULATIONS[v_str]["vehicle_status"] = "BREAKDOWN"
        SIMULATIONS[v_str]["engine_status"] = "stopped"
        SIMULATIONS[v_str]["speed"] = 0.0
        broken_lat = SIMULATIONS[v_str]["latitude"]
        broken_lon = SIMULATIONS[v_str]["longitude"]

    # 3. Update vehicle status in DB
    vehicle.status = "breakdown"
    vehicle.current_lat = broken_lat
    vehicle.current_lon = broken_lon

    # 4. Create breakdown record
    breakdown = VehicleBreakdown(
        vehicle_id=payload.vehicle_id,
        trip_id=payload.trip_id,
        driver_id=current_user.id,
        severity=payload.severity.lower(),
        description=payload.description,
        status="reported",
        reported_at=datetime.now(timezone.utc)
    )
    db.add(breakdown)
    db.commit()
    db.refresh(breakdown)

    # 5. Notify the Fleet Operator
    op_user_id = vehicle.operator_id
    if not op_user_id:
        # Fallback: Alert all fleet operator profiles/users
        first_op = db.query(User).filter(User.role == "fleet_operator").first()
        op_user_id = first_op.id if first_op else current_user.id

    op_notification = Notification(
        user_id=op_user_id,
        notification_type="incident_alert",
        title=f"🚨 Breakdown Reported: {vehicle.registration_number}",
        message=f"Vehicle #{vehicle.registration_number} breakdown reported (severity: {payload.severity.upper()}). Description: {payload.description}",
        is_read=False,
        created_at=datetime.now(timezone.utc)
    )
    db.add(op_notification)
    db.commit()

    # 6. Major Breakdown Severity Logic
    if payload.severity.lower() == "major":
        # Find active shipments on this route
        active_shipments = []
        if payload.trip_id:
            active_shipments = db.query(Shipment).filter(
                Shipment.assigned_route_id == payload.trip_id,
                Shipment.status.in_(["assigned", "in_transit"])
            ).all()

        for shipment in active_shipments:
            shipment.status = "delayed"
            shipment.delay_reason = "vehicle breakdown"
        db.commit()

        # Trigger alternate-vehicle matching logic
        # Find in-transit vehicles managed by SAME operator
        candidates = db.query(Vehicle).filter(
            Vehicle.operator_id == vehicle.operator_id,
            Vehicle.id != vehicle.id,
            Vehicle.status == "in_transit"
        ).all()

        matched_vehicle = None
        for cand in candidates:
            # A. Check remaining capacity
            # Sum of active shipments on candidate
            cand_active_shipments = db.query(Shipment).filter(
                Shipment.assigned_vehicle_id == cand.id,
                Shipment.status.in_(["assigned", "in_transit", "delayed"])
            ).all()
            cand_load = sum(float(shp.weight_kg) for shp in cand_active_shipments)
            cand.current_load_kg = cand_load # ensure load is accurate
            db.commit()

            # For each shipment from broken vehicle, verify if candidate has space
            fits_all = True
            for shipment in active_shipments:
                if float(cand.capacity_weight_kg) - float(cand.current_load_kg) < float(shipment.weight_kg):
                    fits_all = False
                    break
            
            if not fits_all:
                continue

            # B. Check route proximity (upcoming route segment passes near broken location)
            # Find active route for candidate
            cand_route = db.query(Route).filter(
                Route.vehicle_id == cand.id,
                Route.status == "in_progress"
            ).first()

            if not cand_route:
                continue

            cand_stops = db.query(RouteStop).filter(RouteStop.route_id == cand_route.id).all()
            near = False
            for stop in cand_stops:
                if stop.lat is not None and stop.lon is not None:
                    dist = haversine_km(broken_lat, broken_lon, stop.lat, stop.lon)
                    if dist <= 50.0:  # Proximity threshold: 50km
                        near = True
                        break
            
            if near:
                matched_vehicle = cand
                break

        # 7. Generate alerts based on search results
        for shipment in active_shipments:
            if matched_vehicle:
                # Notify matched alternate vehicle available
                match_notification = Notification(
                    user_id=op_user_id,
                    notification_type="route_update",
                    title=f"💡 Alternate Match Found for Order #{shipment.shipment_number}",
                    message=f"Vehicle #{matched_vehicle.registration_number} has space and is near Vehicle #{vehicle.registration_number}'s route — transfer available.",
                    data_json={"breakdown_id": str(breakdown.id), "recommended_vehicle_id": str(matched_vehicle.id)},
                    is_read=False,
                    created_at=datetime.now(timezone.utc)
                )
                db.add(match_notification)
            else:
                # Notify manual intervention needed
                manual_notification = Notification(
                    user_id=op_user_id,
                    notification_type="incident_alert",
                    title=f"⚠️ Manual Action Required: Order #{shipment.shipment_number}",
                    message=f"No alternate vehicle available for Order #{shipment.shipment_number} — manual intervention required.",
                    is_read=False,
                    created_at=datetime.now(timezone.utc)
                )
                db.add(manual_notification)
        db.commit()

    return breakdown


@router.post("/{breakdown_id}/transfer")
def transfer_cargo(
    breakdown_id: uuid.UUID,
    payload: BreakdownTransferSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "fleet_operator"))
):
    """
    Manually confirms the transfer of products from broken vehicle to target vehicle.
    Updates cargo records, notifies the new driver with handoff details.
    """
    # 1. Fetch breakdown
    breakdown = db.query(VehicleBreakdown).filter(VehicleBreakdown.id == breakdown_id).first()
    if not breakdown:
        raise HTTPException(status_code=404, detail="Breakdown record not found")
    if breakdown.status == "product_transferred":
        raise HTTPException(status_code=400, detail="Cargo already transferred")

    # 2. Fetch vehicles
    broken_vehicle = db.query(Vehicle).filter(Vehicle.id == breakdown.vehicle_id).first()
    target_vehicle = db.query(Vehicle).filter(Vehicle.id == payload.target_vehicle_id).first()

    if not broken_vehicle or not target_vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # 3. Find target vehicle's active trip & driver
    target_route = db.query(Route).filter(
        Route.vehicle_id == target_vehicle.id,
        Route.status == "in_progress"
    ).first()
    
    if not target_route:
        raise HTTPException(status_code=400, detail="Target vehicle must have an active trip")

    target_driver = db.query(Driver).filter(Driver.assigned_vehicle_id == target_vehicle.id).first()
    target_driver_user_id = target_driver.user_id if target_driver else None
    if not target_driver_user_id:
        raise HTTPException(status_code=400, detail="Target vehicle must have a driver assigned")

    # 4. Fetch active shipments on broken route
    active_shipments = []
    if breakdown.trip_id:
        active_shipments = db.query(Shipment).filter(
            Shipment.assigned_route_id == breakdown.trip_id,
            Shipment.status.in_(["assigned", "in_transit", "delayed"])
        ).all()

    if not active_shipments:
        raise HTTPException(status_code=400, detail="No active shipments found to transfer")

    # 5. Process transfers
    total_transferred_weight = 0.0
    for shipment in active_shipments:
        shipment.assigned_vehicle_id = target_vehicle.id
        shipment.assigned_driver_id = target_driver.id
        shipment.assigned_route_id = target_route.id
        shipment.status = "in_transit"
        shipment.delay_reason = None
        total_transferred_weight += float(shipment.weight_kg)

        # Append RouteStop to target route
        max_stop = db.query(RouteStop).filter(RouteStop.route_id == target_route.id).order_by(RouteStop.stop_sequence.desc()).first()
        next_seq = (max_stop.stop_sequence + 1) if max_stop else 0
        
        delivery_stop = RouteStop(
            route_id=target_route.id,
            shipment_id=shipment.id,
            stop_sequence=next_seq,
            stop_type="delivery",
            city=shipment.destination_city,
            address=shipment.destination_address,
            lat=shipment.destination_lat,
            lon=shipment.destination_lon,
            status="pending"
        )
        db.add(delivery_stop)

        # 6. Notify target driver with full handoff details
        driver_message = (
            f"🔄 Handoff pickup/transfer location: {broken_vehicle.current_city or 'breakdown spot'}. "
            f"Product: {shipment.goods_type} ({shipment.weight_kg} kg). "
            f"Destination: {shipment.destination_city} - {shipment.destination_address}."
        )
        driver_alert = Notification(
            user_id=target_driver_user_id,
            notification_type="route_update",
            title=f"📦 New Consignment Handoff Details",
            message=driver_message,
            is_read=False,
            created_at=datetime.now(timezone.utc)
        )
        db.add(driver_alert)

    # 7. Update loads
    broken_vehicle.current_load_kg = 0.0
    
    cand_active = db.query(Shipment).filter(
        Shipment.assigned_vehicle_id == target_vehicle.id,
        Shipment.status.in_(["assigned", "in_transit"])
    ).all()
    target_vehicle.current_load_kg = sum(float(shp.weight_kg) for shp in cand_active) + total_transferred_weight

    # 8. Update breakdown record
    breakdown.status = "product_transferred"
    db.commit()

    # 9. Sync tracking simulator context
    t_str = str(target_vehicle.id)
    b_str = str(broken_vehicle.id)
    if b_str in SIMULATIONS:
        SIMULATIONS.pop(b_str)  # Remove broken vehicle simulator
    if t_str in SIMULATIONS:
        # Append delivery stops to simulator path
        path = SIMULATIONS[t_str]["path"]
        for shipment in active_shipments:
            path.append((shipment.destination_lat, shipment.destination_lon, shipment.destination_city, "delivery", shipment.id))
        SIMULATIONS[t_str]["path"] = path

    return {"message": "Cargo successfully transferred", "transferred_weight": total_transferred_weight}


@router.post("/{breakdown_id}/resolve")
def resolve_breakdown(
    breakdown_id: uuid.UUID,
    payload: Optional[BreakdownResolveSchema] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Marks a vehicle breakdown resolved. Resets status back to available.
    """
    breakdown = db.query(VehicleBreakdown).filter(VehicleBreakdown.id == breakdown_id).first()
    if not breakdown:
        raise HTTPException(status_code=404, detail="Breakdown record not found")

    breakdown.status = "resolved"
    breakdown.resolved_at = datetime.now(timezone.utc)

    # Reset vehicle status
    vehicle = db.query(Vehicle).filter(Vehicle.id == breakdown.vehicle_id).first()
    if vehicle:
        vehicle.status = "available"

    # Reset simulation state
    v_str = str(breakdown.vehicle_id)
    if v_str in SIMULATIONS:
        SIMULATIONS[v_str]["vehicle_status"] = "IN_TRANSIT"
        SIMULATIONS[v_str]["engine_status"] = "running"

    db.commit()
    return {"message": "Breakdown successfully resolved", "breakdown_id": breakdown_id}


@router.get("", response_model=List[BreakdownResponseSchema])
def list_breakdowns(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List breakdowns, scoped to Fleet Operator.
    """
    query = db.query(VehicleBreakdown)
    if current_user.role in ("fleet_operator", "operator", "fleet_manager"):
        # Scope: only breakdowns of vehicles managed by this operator
        query = query.join(Vehicle).filter(Vehicle.operator_id == current_user.id)
    return query.all()
