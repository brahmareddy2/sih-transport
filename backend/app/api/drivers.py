"""
Drivers router — Phase 1: CRUD foundation.
"""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.driver import Driver
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/drivers", tags=["Drivers"])


@router.get("", summary="List drivers")
def list_drivers(
    status_filter: Optional[str] = Query(None, alias="status"),
    city: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_roles("admin", "operator", "fleet_manager")),
    db: Session = Depends(get_db),
):
    query = db.query(Driver)
    if status_filter:
        query = query.filter(Driver.status == status_filter)
    if city:
        query = query.filter(Driver.home_city.ilike(f"%{city}%"))

    total = query.count()
    drivers = query.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [_driver_to_dict(d) for d in drivers],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/available", summary="List available drivers")
def list_available_drivers(
    current_user: User = Depends(require_roles("admin", "operator", "fleet_manager")),
    db: Session = Depends(get_db),
):
    drivers = db.query(Driver).filter(Driver.status == "available").all()
    return {"items": [_driver_to_dict(d) for d in drivers], "total": len(drivers)}


@router.get("/{driver_id}", summary="Get driver detail")
def get_driver(
    driver_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return _driver_to_dict(driver)


@router.patch("/{driver_id}/status", summary="Update driver availability")
def update_driver_status(
    driver_id: UUID,
    payload: dict,
    current_user: User = Depends(require_roles("admin", "fleet_manager", "driver")),
    db: Session = Depends(get_db),
):
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    allowed = ["available", "on_trip", "off_duty", "on_leave", "unavailable"]
    new_status = payload.get("status")
    if new_status not in allowed:
        raise HTTPException(status_code=400, detail=f"Invalid status. Allowed: {allowed}")

    driver.status = new_status
    db.commit()
    return {"message": f"Driver status updated to {new_status}"}


def _driver_to_dict(d: Driver) -> dict:
    return {
        "id": str(d.id),
        "employee_id": d.employee_id,
        "license_number": d.license_number,
        "license_type": d.license_type,
        "license_expiry": d.license_expiry.isoformat() if d.license_expiry else None,
        "assigned_vehicle_id": str(d.assigned_vehicle_id) if d.assigned_vehicle_id else None,
        "status": d.status,
        "home_city": d.home_city,
        "experience_years": d.experience_years,
        "total_trips": d.total_trips,
        "on_time_delivery_rate": float(d.on_time_delivery_rate) if d.on_time_delivery_rate else None,
        "hours_driven_today": float(d.hours_driven_today),
        "hours_driven_this_week": float(d.hours_driven_this_week),
        "created_at": d.created_at.isoformat(),
    }
