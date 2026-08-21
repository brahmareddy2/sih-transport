"""
Seed data management API.
Endpoints to generate and inspect the synthetic demo dataset.
"""
import logging
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.models.shipment import Shipment
from app.models.route import Route
from app.models.incident import Incident
from app.schemas.seed import SeedStatusSchema, SeedGenerateRequest, SeedGenerateResponse
from app.services.seed_data.generator import run_full_seed

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/seed", tags=["Seed Data"])


@router.get("/status", response_model=SeedStatusSchema, summary="Check seed data status")
def get_seed_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return current counts of seeded data in the database."""
    vehicles_count = db.query(Vehicle).count()
    drivers_count = db.query(Driver).count()
    shipments_count = db.query(Shipment).count()
    trips_count = db.query(Route).count()
    incidents_count = db.query(Incident).count()
    pending_shipments = db.query(Shipment).filter(Shipment.status == "pending").count()
    available_vehicles = db.query(Vehicle).filter(Vehicle.status == "available").count()
    available_drivers = db.query(Driver).filter(Driver.status == "available").count()

    return SeedStatusSchema(
        seeded=vehicles_count > 0,
        vehicles_count=vehicles_count,
        drivers_count=drivers_count,
        shipments_count=shipments_count,
        trips_count=trips_count,
        incidents_count=incidents_count,
        pending_shipments=pending_shipments,
        available_vehicles=available_vehicles,
        available_drivers=available_drivers,
    )


@router.post("/generate", response_model=SeedGenerateResponse, summary="Generate synthetic data")
def generate_seed_data(
    payload: SeedGenerateRequest = SeedGenerateRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "operator")),
):
    """
    Generate or regenerate synthetic demo data.
    Requires admin or operator role.

    If `overwrite=False` and data already exists, returns an error.
    If `overwrite=True`, clears existing data first.
    """
    t0 = time.time()

    # Check if data exists
    existing_count = db.query(Vehicle).count()
    if existing_count > 0 and not payload.overwrite:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Seed data already exists ({existing_count} vehicles). Use overwrite=true to regenerate.",
        )

    if payload.overwrite:
        logger.info("Clearing existing seed data before regeneration")
        try:
            # Delete in dependency order (including dependent tracking/analytics/recovery tables)
            from app.models.incident import RecoveryPlan
            from app.models.return_cargo import ReturnCargoMatch
            from app.models.route import RouteStop
            from app.models.shipment import ShipmentGroupMember, ShipmentConsolidationGroup
            from app.models.analytics import VehicleLocationHistory, MaintenanceRecord, DemandForecast
            from app.models.notification import Notification

            db.query(RecoveryPlan).delete()
            db.query(Incident).delete()
            db.query(ReturnCargoMatch).delete()
            db.query(ShipmentGroupMember).delete()
            db.query(ShipmentConsolidationGroup).delete()
            from app.models.breakdown import VehicleBreakdown
            db.query(VehicleBreakdown).delete()
            db.query(RouteStop).delete()
            db.query(Notification).delete()
            db.query(VehicleLocationHistory).delete()
            db.query(MaintenanceRecord).delete()
            db.query(DemandForecast).delete()
            db.query(Shipment).delete()
            db.query(Route).delete()
            db.query(Driver).filter(Driver.employee_id.like("DRV-%")).delete(synchronize_session=False)
            db.query(Vehicle).delete()
            db.commit()
            logger.info("Existing seed data cleared")
        except Exception as e:
            db.rollback()
            logger.error("Failed to clear seed data: %s", e)
            raise HTTPException(status_code=500, detail=f"Failed to clear existing data: {e}")

    # Generate synthetic data
    logger.info("Generating synthetic data with SEED=42")
    data = run_full_seed()

    # Insert vehicles
    logger.info("Inserting %d vehicles...", len(data["vehicles"]))
    try:
        demo_operators = db.query(User).filter(User.email.in_(["operator@logistics.in", "fleet@logistics.in"])).all()
        op_ids = [op.id for op in op_operators] if 'op_operators' in locals() else [op.id for op in demo_operators]
        
        for idx, v in enumerate(data["vehicles"]):
            op_id = op_ids[idx % len(op_ids)] if op_ids else None
            vehicle = Vehicle(
                registration_number=v["registration_number"],
                vehicle_type=v["vehicle_type"],
                make=v["make"],
                model_name=v["model_name"],
                year=v["year"],
                capacity_weight_kg=v["capacity_weight_kg"],
                capacity_volume_m3=v["capacity_volume_m3"],
                fuel_type=v["fuel_type"],
                fuel_efficiency_kmpl=v["fuel_efficiency_kmpl"],
                fuel_tank_capacity_l=v["fuel_tank_capacity_l"],
                current_fuel_level_l=v["current_fuel_level_l"],
                current_lat=v["current_lat"],
                current_lon=v["current_lon"],
                current_city=v["current_city"],
                odometer_km=v["odometer_km"],
                status=v["status"],
                last_service_date=v["last_service_date"],
                next_service_due_km=v["next_service_due_km"],
                insurance_expiry=v["insurance_expiry"],
                permit_expiry=v["permit_expiry"],
                is_refrigerated=v["is_refrigerated"],
                can_carry_hazmat=v["can_carry_hazmat"],
                home_depot_city=v["home_depot_city"],
                operator_id=op_id,
                current_load_kg=0.0,
            )
            db.add(vehicle)
        db.commit()
        logger.info("Vehicles committed")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to insert vehicles: {e}")

    # Insert drivers (without vehicle assignment for now)
    logger.info("Inserting %d drivers...", len(data["drivers"]))
    try:
        for d in data["drivers"]:
            driver = Driver(
                employee_id=d["employee_id"],
                license_number=d["license_number"],
                license_type=d["license_type"],
                license_expiry=d["license_expiry"],
                status=d["status"],
                home_city=d["home_city"],
                experience_years=d["experience_years"],
                total_trips=d["total_trips"],
                on_time_delivery_rate=d["on_time_delivery_rate"],
                hours_driven_today=d["hours_driven_today"],
                hours_driven_this_week=d["hours_driven_this_week"],
            )
            db.add(driver)
        db.commit()
        logger.info("Drivers committed")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to insert drivers: {e}")

    # Insert shipments
    logger.info("Inserting %d shipments...", len(data["shipments"]))
    try:
        for s in data["shipments"]:
            shipment = Shipment(
                shipment_number=s["shipment_number"],
                origin_city=s["origin_city"],
                origin_address=s["origin_address"],
                origin_lat=s["origin_lat"],
                origin_lon=s["origin_lon"],
                destination_city=s["destination_city"],
                destination_address=s["destination_address"],
                destination_lat=s["destination_lat"],
                destination_lon=s["destination_lon"],
                weight_kg=s["weight_kg"],
                volume_m3=s["volume_m3"],
                goods_type=s["goods_type"],
                is_hazardous=s["is_hazardous"],
                requires_refrigeration=s["requires_refrigeration"],
                priority=s["priority"],
                requested_pickup_time=s["requested_pickup_time"],
                time_window_start=s["time_window_start"],
                time_window_end=s["time_window_end"],
                declared_value_inr=s["declared_value_inr"],
                status=s["status"],
            )
            db.add(shipment)
        db.commit()
        logger.info("Shipments committed")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to insert shipments: {e}")

    # Insert historical trips (routes) — simplified, without route stops
    logger.info("Inserting %d historical trips...", len(data["trips"]))
    try:
        # Build vehicle/driver lookup by position index
        db_vehicles = db.query(Vehicle).all()
        db_drivers = db.query(Driver).all()
        import random
        random.seed(42)

        for t in data["trips"]:
            vehicle = random.choice(db_vehicles) if db_vehicles else None
            driver = random.choice(db_drivers) if db_drivers else None

            route = Route(
                route_number=t["route_number"],
                vehicle_id=vehicle.id if vehicle else None,
                driver_id=driver.id if driver else None,
                origin_city=t["origin_city"],
                destination_city=t["destination_city"],
                total_distance_km=t["total_distance_km"],
                estimated_duration_min=t["estimated_duration_min"],
                actual_duration_min=t["actual_duration_min"],
                estimated_fuel_l=t["estimated_fuel_l"],
                actual_fuel_l=t["actual_fuel_l"],
                estimated_fuel_cost_inr=t["estimated_fuel_cost_inr"],
                actual_fuel_cost_inr=t["actual_fuel_cost_inr"],
                estimated_toll_inr=t["estimated_toll_inr"],
                actual_toll_inr=t["actual_toll_inr"],
                estimated_co2_kg=t["estimated_co2_kg"],
                actual_co2_kg=t["actual_co2_kg"],
                planned_start_time=t["planned_start_time"],
                actual_start_time=t["actual_start_time"],
                planned_end_time=t["planned_end_time"],
                actual_end_time=t["actual_end_time"],
                status=t["status"],
                road_type=t["road_type"],
            )
            db.add(route)
        db.commit()
        logger.info("Trips committed")

        # Link shipments to routes and create RouteStops
        db_routes = db.query(Route).all()
        db_shipments = db.query(Shipment).all()
        from app.models.route import RouteStop
        import random
        random.seed(42)
        
        # Shuffle shipments
        random.shuffle(db_shipments)
        shipment_idx = 0
        
        for route in db_routes:
            # Assign 1-2 shipments to each route
            num_consignments = random.randint(1, 2)
            route_load = 0.0
            
            for _ in range(num_consignments):
                if shipment_idx >= len(db_shipments):
                    break
                shp = db_shipments[shipment_idx]
                shipment_idx += 1
                
                # Link shipment
                shp.assigned_route_id = route.id
                shp.assigned_vehicle_id = route.vehicle_id
                shp.assigned_driver_id = route.driver_id
                
                # Align status
                if route.status == "in_progress":
                    shp.status = "in_transit"
                    route_load += float(shp.weight_kg)
                elif route.status == "completed":
                    shp.status = "delivered"
                
                # Create RouteStops
                pickup_stop = RouteStop(
                    route_id=route.id,
                    shipment_id=shp.id,
                    stop_sequence=0,
                    stop_type="pickup",
                    city=shp.origin_city,
                    address=shp.origin_address,
                    lat=shp.origin_lat,
                    lon=shp.origin_lon,
                    status="completed" if route.status == "completed" else "arrived"
                )
                delivery_stop = RouteStop(
                    route_id=route.id,
                    shipment_id=shp.id,
                    stop_sequence=1,
                    stop_type="delivery",
                    city=shp.destination_city,
                    address=shp.destination_address,
                    lat=shp.destination_lat,
                    lon=shp.destination_lon,
                    status="completed" if route.status == "completed" else "pending"
                )
                db.add(pickup_stop)
                db.add(delivery_stop)
            
            # Update vehicle load
            if route.status == "in_progress" and route.vehicle_id:
                veh = db.query(Vehicle).filter(Vehicle.id == route.vehicle_id).first()
                if veh:
                    veh.current_load_kg = route_load
                    veh.status = "in_transit"
                    
        db.commit()
        logger.info("Shipment-Route linkages and RouteStops committed")
    except Exception as e:
        db.rollback()
        logger.warning("Failed to insert trips (non-fatal): %s", e)

    duration = round(time.time() - t0, 2)
    summary = data["summary"]

    # Recount from DB
    summary["vehicles_count"] = db.query(Vehicle).count()
    summary["drivers_count"] = db.query(Driver).count()
    summary["shipments_count"] = db.query(Shipment).count()

    logger.info("Seed data generation completed in %.1fs", duration)

    return SeedGenerateResponse(
        message=f"Synthetic data generated successfully in {duration}s",
        summary=summary,
        duration_seconds=duration,
    )
