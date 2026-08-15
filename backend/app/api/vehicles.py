"""
Vehicles router — Phase 1: CRUD foundation.
Full optimization integration added in Phase 2.
"""
import logging
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.models.vehicle import Vehicle

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


@router.get("", summary="List vehicles")
def list_vehicles(
    status_filter: Optional[str] = Query(None, alias="status"),
    city: Optional[str] = None,
    vehicle_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_roles("admin", "operator", "fleet_manager")),
    db: Session = Depends(get_db),
):
    query = db.query(Vehicle)
    if status_filter:
        query = query.filter(Vehicle.status == status_filter)
    if city:
        query = query.filter(Vehicle.current_city.ilike(f"%{city}%"))
    if vehicle_type:
        query = query.filter(Vehicle.vehicle_type == vehicle_type)

    total = query.count()
    vehicles = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": [_vehicle_to_dict(v) for v in vehicles],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/available", summary="List available vehicles")
def list_available_vehicles(
    current_user: User = Depends(require_roles("admin", "operator", "fleet_manager")),
    db: Session = Depends(get_db),
):
    vehicles = db.query(Vehicle).filter(Vehicle.status == "available").all()
    return {"items": [_vehicle_to_dict(v) for v in vehicles], "total": len(vehicles)}


@router.get("/{vehicle_id}", summary="Get vehicle detail")
def get_vehicle(
    vehicle_id: UUID,
    current_user: User = Depends(require_roles("admin", "operator", "fleet_manager")),
    db: Session = Depends(get_db),
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return _vehicle_to_dict(vehicle)


@router.patch("/{vehicle_id}/status", summary="Update vehicle status")
def update_vehicle_status(
    vehicle_id: UUID,
    payload: dict,
    current_user: User = Depends(require_roles("admin", "fleet_manager", "driver")),
    db: Session = Depends(get_db),
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    allowed = ["available", "in_transit", "maintenance", "breakdown", "idle"]
    new_status = payload.get("status")
    if new_status not in allowed:
        raise HTTPException(status_code=400, detail=f"Invalid status. Allowed: {allowed}")

    vehicle.status = new_status
    db.commit()
    return {"message": f"Vehicle status updated to {new_status}", "vehicle_id": str(vehicle_id)}


@router.patch("/{vehicle_id}/location", summary="Update vehicle GPS location")
def update_vehicle_location(
    vehicle_id: UUID,
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    vehicle.current_lat = payload.get("lat", vehicle.current_lat)
    vehicle.current_lon = payload.get("lon", vehicle.current_lon)
    vehicle.current_city = payload.get("city", vehicle.current_city)
    db.commit()
    return {"message": "Location updated"}


def _vehicle_to_dict(v: Vehicle) -> dict:
    return {
        "id": str(v.id),
        "registration_number": v.registration_number,
        "vehicle_type": v.vehicle_type,
        "make": v.make,
        "model_name": v.model_name,
        "year": v.year,
        "capacity_weight_kg": float(v.capacity_weight_kg),
        "capacity_volume_m3": float(v.capacity_volume_m3) if v.capacity_volume_m3 else None,
        "fuel_type": v.fuel_type,
        "fuel_efficiency_kmpl": float(v.fuel_efficiency_kmpl),
        "current_fuel_level_l": float(v.current_fuel_level_l) if v.current_fuel_level_l else None,
        "current_lat": v.current_lat,
        "current_lon": v.current_lon,
        "current_city": v.current_city,
        "status": v.status,
        "is_refrigerated": v.is_refrigerated,
        "can_carry_hazmat": v.can_carry_hazmat,
        "home_depot_city": v.home_depot_city,
        "odometer_km": float(v.odometer_km),
        "created_at": v.created_at.isoformat(),
    }
