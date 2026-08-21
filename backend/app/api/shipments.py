"""
Shipments router — Phase 1: CRUD foundation.
Consolidation and optimization hooks added in Phase 2.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.shipment import Shipment
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/shipments", tags=["Shipments"])


def _generate_shipment_number(db: Session) -> str:
    """Generate sequential shipment number: SHP-YYYY-NNNNN"""
    year = datetime.now(timezone.utc).year
    count = db.query(Shipment).count() + 1
    return f"SHP-{year}-{count:05d}"


@router.get("", summary="List shipments")
def list_shipments(
    status_filter: Optional[str] = Query(None, alias="status"),
    origin_city: Optional[str] = None,
    destination_city: Optional[str] = None,
    priority: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Shipment)

    # Customers can only see their own shipments
    if current_user.role == "customer":
        query = query.filter(Shipment.customer_id == current_user.id)

    if status_filter:
        query = query.filter(Shipment.status == status_filter)
    if origin_city:
        query = query.filter(Shipment.origin_city.ilike(f"%{origin_city}%"))
    if destination_city:
        query = query.filter(Shipment.destination_city.ilike(f"%{destination_city}%"))
    if priority:
        query = query.filter(Shipment.priority == priority)

    query = query.order_by(Shipment.created_at.desc())
    total = query.count()
    shipments = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": [_shipment_to_dict(s) for s in shipments],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.post("", status_code=201, summary="Create new shipment")
def create_shipment(
    payload: dict,
    current_user: User = Depends(require_roles("admin", "fleet_operator", "customer")),
    db: Session = Depends(get_db),
):
    required = ["origin_city", "origin_address", "origin_lat", "origin_lon",
                "destination_city", "destination_address", "destination_lat",
                "destination_lon", "weight_kg"]
    for field in required:
        if field not in payload:
            raise HTTPException(status_code=422, detail=f"Missing required field: {field}")

    shipment = Shipment(
        id=uuid4(),
        shipment_number=_generate_shipment_number(db),
        customer_id=current_user.id if current_user.role == "customer" else payload.get("customer_id"),
        origin_city=payload["origin_city"],
        origin_address=payload["origin_address"],
        origin_lat=payload["origin_lat"],
        origin_lon=payload["origin_lon"],
        destination_city=payload["destination_city"],
        destination_address=payload["destination_address"],
        destination_lat=payload["destination_lat"],
        destination_lon=payload["destination_lon"],
        weight_kg=payload["weight_kg"],
        volume_m3=payload.get("volume_m3"),
        goods_type=payload.get("goods_type"),
        is_hazardous=payload.get("is_hazardous", False),
        requires_refrigeration=payload.get("requires_refrigeration", False),
        priority=payload.get("priority", "normal"),
        declared_value_inr=payload.get("declared_value_inr"),
        status="pending",
    )
    db.add(shipment)
    db.commit()
    db.refresh(shipment)
    logger.info("Shipment created: %s by user %s", shipment.shipment_number, current_user.id)

    # Trigger notifications to Fleet Operators with at least one empty vehicle
    try:
        from app.models.notification import Notification
        from app.models.vehicle import Vehicle
        operators = db.query(User).filter(User.role == "fleet_operator").all()
        for op in operators:
            # Check if operator has an empty vehicle (status available or idle)
            empty_vehicle = db.query(Vehicle).filter(
                Vehicle.operator_id == op.id,
                Vehicle.status.in_(["available", "idle"])
            ).first()
            
            if empty_vehicle:
                notif = Notification(
                    user_id=op.id,
                    notification_type="incident_alert",
                    title=f"📦 New Order Booked: {shipment.shipment_number}",
                    message=f"A new shipment order {shipment.shipment_number} ({shipment.goods_type or 'General Cargo'}, {shipment.weight_kg}kg) has been booked from {shipment.origin_city} to {shipment.destination_city}. You have idle vehicle {empty_vehicle.registration_number} available for assignment.",
                    is_read=False,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(notif)
        db.commit()
    except Exception as notif_err:
        logger.error("Failed sending operator notifications: %s", notif_err)

    return _shipment_to_dict(shipment)


@router.get("/pending", summary="List unassigned pending shipments")
def list_pending_shipments(
    current_user: User = Depends(require_roles("admin", "fleet_operator", "operator")),
    db: Session = Depends(get_db),
):
    shipments = db.query(Shipment).filter(Shipment.status == "pending").order_by(
        Shipment.priority, Shipment.created_at
    ).all()
    return {"items": [_shipment_to_dict(s) for s in shipments], "total": len(shipments)}


@router.get("/{shipment_id}", summary="Get shipment detail")
def get_shipment(
    shipment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    # Customers can only view their own
    if current_user.role == "customer" and shipment.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return _shipment_to_dict(shipment)


@router.delete("/{shipment_id}", summary="Cancel a shipment")
def cancel_shipment(
    shipment_id: UUID,
    current_user: User = Depends(require_roles("admin", "fleet_operator", "operator")),
    db: Session = Depends(get_db),
):
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    if shipment.status in ("in_transit", "delivered"):
        raise HTTPException(status_code=400, detail=f"Cannot cancel shipment in status: {shipment.status}")
    shipment.status = "cancelled"
    shipment.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": f"Shipment {shipment.shipment_number} cancelled"}


def _shipment_to_dict(s: Shipment) -> dict:
    return {
        "id": str(s.id),
        "shipment_number": s.shipment_number,
        "customer_id": str(s.customer_id) if s.customer_id else None,
        "origin_city": s.origin_city,
        "origin_address": s.origin_address,
        "origin_lat": s.origin_lat,
        "origin_lon": s.origin_lon,
        "destination_city": s.destination_city,
        "destination_address": s.destination_address,
        "destination_lat": s.destination_lat,
        "destination_lon": s.destination_lon,
        "weight_kg": float(s.weight_kg),
        "volume_m3": float(s.volume_m3) if s.volume_m3 else None,
        "goods_type": s.goods_type,
        "is_hazardous": s.is_hazardous,
        "requires_refrigeration": s.requires_refrigeration,
        "priority": s.priority,
        "declared_value_inr": float(s.declared_value_inr) if s.declared_value_inr else None,
        "status": s.status,
        "assigned_route_id": str(s.assigned_route_id) if s.assigned_route_id else None,
        "created_at": s.created_at.isoformat(),
        "updated_at": s.updated_at.isoformat(),
    }


from pydantic import BaseModel
class AssignShipmentPayload(BaseModel):
    vehicle_id: UUID
    driver_id: UUID


@router.post("/{shipment_id}/assign", summary="Manually assign empty vehicle and driver to a shipment (confirm order)")
def assign_shipment_to_vehicle(
    shipment_id: UUID,
    payload: AssignShipmentPayload,
    current_user: User = Depends(require_roles("admin", "fleet_operator")),
    db: Session = Depends(get_db)
):
    from app.models.vehicle import Vehicle
    from app.models.driver import Driver
    from app.models.route import Route, RouteStop
    
    # 1. Fetch shipment
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
        
    if shipment.status != "pending":
        raise HTTPException(status_code=400, detail=f"Shipment is already {shipment.status}")

    # 2. Fetch vehicle & driver
    vehicle = db.query(Vehicle).filter(Vehicle.id == payload.vehicle_id).first()
    driver = db.query(Driver).filter(Driver.id == payload.driver_id).first()
    
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    # Enforce vehicle is empty (load == 0 or status == available)
    active_routes = db.query(Route).filter(
        Route.vehicle_id == vehicle.id,
        Route.status.in_(["planned", "in_progress"])
    ).all()
    if len(active_routes) > 0 or float(vehicle.current_load_kg) > 0 or vehicle.status not in ["available", "idle"]:
        raise HTTPException(status_code=400, detail="Vehicle is not empty or is already assigned to a trip")

    # 3. Create a Route (trip)
    import uuid
    route_id = uuid.uuid4()
    route_number = f"RT-{datetime.now(timezone.utc).year}-{db.query(Route).count() + 1:05d}"
    
    route = Route(
        id=route_id,
        route_number=route_number,
        vehicle_id=vehicle.id,
        driver_id=driver.id,
        origin_city=shipment.origin_city,
        destination_city=shipment.destination_city,
        planned_start_time=datetime.now(timezone.utc),
        status="in_progress",
    )
    db.add(route)

    # 4. Create stops
    pickup_stop = RouteStop(
        route_id=route_id,
        shipment_id=shipment.id,
        stop_sequence=0,
        stop_type="pickup",
        city=shipment.origin_city,
        address=shipment.origin_address,
        lat=shipment.origin_lat,
        lon=shipment.origin_lon,
        status="completed",
        actual_arrival=datetime.now(timezone.utc),
        actual_departure=datetime.now(timezone.utc),
    )
    delivery_stop = RouteStop(
        route_id=route_id,
        shipment_id=shipment.id,
        stop_sequence=1,
        stop_type="delivery",
        city=shipment.destination_city,
        address=shipment.destination_address,
        lat=shipment.destination_lat,
        lon=shipment.destination_lon,
        status="pending",
    )
    db.add(pickup_stop)
    db.add(delivery_stop)

    # 5. Update vehicle & shipment state
    vehicle.status = "in_transit"
    vehicle.current_load_kg = shipment.weight_kg
    
    shipment.assigned_vehicle_id = vehicle.id
    shipment.assigned_driver_id = driver.id
    shipment.assigned_route_id = route_id
    shipment.status = "in_transit"
    
    # 6. Notify driver
    from app.models.notification import Notification
    driver_notif = Notification(
        user_id=driver.user_id,
        notification_type="route_update",
        title=f"📋 New Trip Assigned: {route_number}",
        message=f"You have been assigned to trip {route_number} transporting {shipment.goods_type or 'General Cargo'} ({shipment.weight_kg}kg) from {shipment.origin_city} to {shipment.destination_city}.",
        is_read=False,
        created_at=datetime.now(timezone.utc),
    )
    db.add(driver_notif)

    db.commit()
    return {"message": "Shipment assigned successfully", "route_id": str(route_id), "route_number": route_number}
