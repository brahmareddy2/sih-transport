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
from app.models.route import Route
from app.models.vehicle import Vehicle

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
    current_user: User = Depends(require_roles("admin", "fleet_operator", "operator", "fleet_manager")),
    db: Session = Depends(get_db),
):
    drivers = db.query(Driver).filter(Driver.status == "available").all()
    return {"items": [_driver_to_dict(d) for d in drivers], "total": len(drivers)}


@router.get("/active-trip", summary="Get logged-in driver's active trip details")
def get_active_trip(
    current_user: User = Depends(require_roles("driver")),
    db: Session = Depends(get_db),
):
    """
    Retrieve the active in-transit trip details for the currently logged-in driver,
    including the active route, vehicle telemetry, and estimated expenses.
    """
    driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver profile not found")

    # Find active or in-progress route
    route = db.query(Route).filter(
        Route.driver_id == driver.id,
        Route.status.in_(["in_progress", "planned"])
    ).first()

    # Fallback to last route if no active route is found
    if not route:
        route = db.query(Route).filter(Route.driver_id == driver.id).order_by(Route.created_at.desc()).first()

    vehicle = driver.assigned_vehicle

    origin = route.origin_city if route else "Delhi"
    destination = route.destination_city if route else "Hyderabad"
    distance = float(route.total_distance_km) if (route and route.total_distance_km) else 1580.0
    duration_hrs = round((route.estimated_duration_min / 60.0), 1) if (route and route.estimated_duration_min) else 26.5
    
    fuel_available = float(vehicle.current_fuel_level_l) if (vehicle and vehicle.current_fuel_level_l is not None) else 180.0
    fuel_efficiency = float(vehicle.fuel_efficiency_kmpl) if (vehicle and vehicle.fuel_efficiency_kmpl) else 4.0
    fuel_required = round(distance / fuel_efficiency) if fuel_efficiency > 0 else 395
    
    toll_cost = float(route.estimated_toll_inr) if (route and route.estimated_toll_inr) else 2850.0
    fuel_cost = float(route.estimated_fuel_cost_inr) if (route and route.estimated_fuel_cost_inr) else 36735.0
    total_cost = toll_cost + fuel_cost

    # Look up city coords for origin & destination
    from app.services.optimization.distance_matrix import INDIAN_CITIES
    origin_info = INDIAN_CITIES.get(origin, {"lat": 28.7041, "lon": 77.1025})
    dest_info = INDIAN_CITIES.get(destination, {"lat": 17.3850, "lon": 78.4867})
    origin_coords = [origin_info.get("lat"), origin_info.get("lon")]
    destination_coords = [dest_info.get("lat"), dest_info.get("lon")]

    from app.models.route import RouteStop
    path_coords = []
    if route:
        stops = db.query(RouteStop).filter(RouteStop.route_id == route.id).order_by(RouteStop.stop_sequence).all()
        for s in stops:
            if s.lat is not None and s.lon is not None:
                path_coords.append([s.lat, s.lon])
                
    if not path_coords:
        path_coords = [origin_coords, destination_coords]

    return {
        "has_trip": (route is not None),
        "trip_id": str(route.id) if route else None,
        "route_number": route.route_number if route else "TRIP-DEMO-77",
        "origin": origin,
        "destination": destination,
        "distance_km": distance,
        "duration_hours": duration_hrs,
        "eta": "Tomorrow 06:30 AM",
        "fuel_available_l": fuel_available,
        "fuel_required_l": fuel_required,
        "refuel_city": "Nagpur" if origin == "Delhi" else "Nagpur",
        "toll_cost_inr": toll_cost,
        "fuel_cost_inr": fuel_cost,
        "total_cost_inr": total_cost,
        "status": route.status.upper() if route else "IN_PROGRESS",
        "origin_coords": origin_coords,
        "destination_coords": destination_coords,
        "path_coords": path_coords,
        "vehicle_id": str(vehicle.id) if vehicle else None,
        "registration_number": vehicle.registration_number if vehicle else None,
        "current_lat": vehicle.current_lat if (vehicle and vehicle.current_lat is not None) else origin_coords[0],
        "current_lon": vehicle.current_lon if (vehicle and vehicle.current_lon is not None) else origin_coords[1],
    }


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
