"""
In-process GPS and Telematics Simulation Engine.
Manages vehicle movement interpolation, fuel depletion, status changes,
database persistence of breadcrumbs, and WebSocket broadcast triggers.
"""
import asyncio
import logging
import math
import random
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.vehicle import Vehicle
from app.models.route import Route, RouteStop
from app.models.analytics import VehicleLocationHistory
from app.models.notification import Notification
from app.models.user import User
from app.services.tracking.eta_calculator import calculate_eta
from app.services.optimization.distance_matrix import INDIAN_CITIES

logger = logging.getLogger(__name__)

# Active simulations: vehicle_id (str) -> dict of tracking state
SIMULATIONS: Dict[str, dict] = {}

# Active WebSocket connections
ACTIVE_CONNECTIONS: List = []

# Helper calculation functions
def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    dLon = math.radians(lon2 - lon1)
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)
    y = math.sin(dLon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dLon)
    brng = math.atan2(y, x)
    return int((math.degrees(brng) + 360) % 360)

def calculate_remaining_distance(lat: float, lon: float, path: list, stop_index: int) -> float:
    if stop_index >= len(path) - 1:
        return 0.0
    next_lat, next_lon = path[stop_index + 1][0], path[stop_index + 1][1]
    dist = haversine_distance(lat, lon, next_lat, next_lon)
    for i in range(stop_index + 1, len(path) - 1):
        dist += haversine_distance(path[i][0], path[i][1], path[i+1][0], path[i+1][1])
    return dist

# Control functions
def start_simulation(vehicle_id: uuid.UUID, route_id: Optional[uuid.UUID], db: Session) -> dict:
    v_str = str(vehicle_id)
    
    # 1. Fetch vehicle
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise ValueError(f"Vehicle with ID '{vehicle_id}' not found.")
        
    # 2. Get active/specified route
    route = None
    if route_id:
        route = db.query(Route).filter(Route.id == route_id).first()
    else:
        # Fallback to vehicle's first in-progress or planned route
        route = db.query(Route).filter(
            Route.vehicle_id == vehicle_id,
            Route.status.in_(["in_progress", "planned"])
        ).first()

    if not route:
        # Create a dummy route for simulation fallback
        logger.info("No active route found for vehicle %s, using simulation fallback", vehicle.registration_number)
        route_num = f"SIM-{vehicle.registration_number}-{random.randint(100, 999)}"
        route = Route(
            route_number=route_num,
            vehicle_id=vehicle_id,
            driver_id=vehicle.driver.id if vehicle.driver else None,
            origin_city=vehicle.current_city or "Mumbai",
            destination_city="Pune",
            total_distance_km=150.0,
            estimated_duration_min=180,
            status="in_progress"
        )
        db.add(route)
        db.commit()
        db.refresh(route)
        
        # Add stops
        origin_coords = INDIAN_CITIES.get(route.origin_city, {"lat": 19.0760, "lon": 72.8777})
        dest_coords = INDIAN_CITIES.get(route.destination_city, {"lat": 18.5204, "lon": 73.8567})
        stop1 = RouteStop(route_id=route.id, stop_sequence=0, stop_type="pickup", city=route.origin_city, lat=origin_coords["lat"], lon=origin_coords["lon"])
        stop2 = RouteStop(route_id=route.id, stop_sequence=1, stop_type="delivery", city=route.destination_city, lat=dest_coords["lat"], lon=dest_coords["lon"])
        db.add(stop1)
        db.add(stop2)
        db.commit()

    # 3. Retrieve path stops
    stops = db.query(RouteStop).filter(RouteStop.route_id == route.id).order_by(RouteStop.stop_sequence).all()
    path_points = []
    for s in stops:
        if s.lat is not None and s.lon is not None:
            path_points.append((s.lat, s.lon, s.city or "Unknown", s.stop_type, s.shipment_id))
            
    if not path_points:
        origin_coords = INDIAN_CITIES.get(route.origin_city, {"lat": 19.0760, "lon": 72.8777})
        dest_coords = INDIAN_CITIES.get(route.destination_city, {"lat": 28.7041, "lon": 77.1025})
        path_points = [
            (origin_coords["lat"], origin_coords["lon"], route.origin_city or "Mumbai", "pickup", None),
            (dest_coords["lat"], dest_coords["lon"], route.destination_city or "Delhi", "delivery", None)
        ]

    # Ensure path has at least 2 points
    if len(path_points) < 2:
        lat, lon = path_points[0][0], path_points[0][1]
        path_points.append((lat + 0.1, lon + 0.1, "Sub-depot Hub", "delivery", None))

    # Calculate remaining distance
    rem_km = calculate_remaining_distance(path_points[0][0], path_points[0][1], path_points, 0)

    # Initialize state
    state = {
        "vehicle_id": str(vehicle_id),
        "registration_number": vehicle.registration_number,
        "driver_name": vehicle.driver.full_name if (vehicle.driver and hasattr(vehicle.driver, 'full_name')) else "Unknown Driver",
        "current_trip_id": str(route.id),
        "trip_id": str(route.id),
        "path": path_points,
        "stop_index": 0,
        "progress_pct": 0.0,
        "latitude": path_points[0][0],
        "longitude": path_points[0][1],
        "speed": 0.0,
        "heading": 0,
        "fuel_level": float(vehicle.current_fuel_level_l or vehicle.fuel_tank_capacity_l or 200.0),
        "fuel_capacity": float(vehicle.fuel_tank_capacity_l or 200.0),
        "fuel_efficiency": float(vehicle.fuel_efficiency_kmpl or 5.0),
        "engine_status": "running",
        "vehicle_status": "IN_TRANSIT",
        "is_paused": False,
        "tick_count": 0,
        "remaining_km": round(rem_km, 1),
        "eta_minutes": int(round((rem_km / 55.0) * 60.0)),
        "eta": datetime.now(timezone.utc).isoformat(),
        "risk_level": "LOW",
        "timestamp": datetime.now(timezone.utc)
    }

    SIMULATIONS[v_str] = state
    
    # Update route & vehicle status in DB immediately
    try:
        route.status = "in_progress"
        vehicle.status = "in_transit"
        vehicle.current_lat = state["latitude"]
        vehicle.current_lon = state["longitude"]
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Failed to update status on simulation start: %s", e)

    logger.info("Started GPS simulation for vehicle %s", vehicle.registration_number)
    return get_vehicle_state(vehicle_id)

def stop_simulation(vehicle_id: uuid.UUID) -> dict:
    v_str = str(vehicle_id)
    if v_str in SIMULATIONS:
        state = SIMULATIONS.pop(v_str)
        db = SessionLocal()
        try:
            _complete_trip_in_db(db, v_str, state["trip_id"])
        finally:
            db.close()
    return {"vehicle_id": vehicle_id, "status": "OFFLINE"}

def pause_simulation(vehicle_id: uuid.UUID) -> dict:
    v_str = str(vehicle_id)
    if v_str in SIMULATIONS:
        SIMULATIONS[v_str]["is_paused"] = True
        SIMULATIONS[v_str]["engine_status"] = "idle"
        SIMULATIONS[v_str]["vehicle_status"] = "STOPPED"
        SIMULATIONS[v_str]["speed"] = 0.0
    return get_vehicle_state(vehicle_id)

def resume_simulation(vehicle_id: uuid.UUID) -> dict:
    v_str = str(vehicle_id)
    if v_str in SIMULATIONS:
        SIMULATIONS[v_str]["is_paused"] = False
        SIMULATIONS[v_str]["engine_status"] = "running"
        SIMULATIONS[v_str]["vehicle_status"] = "IN_TRANSIT"
    return get_vehicle_state(vehicle_id)

def get_vehicle_state(vehicle_id: uuid.UUID) -> dict:
    v_str = str(vehicle_id)
    if v_str in SIMULATIONS:
        s = SIMULATIONS[v_str]
        return {
            "vehicle_id": uuid.UUID(s["vehicle_id"]),
            "registration_number": s["registration_number"],
            "latitude": s["latitude"],
            "longitude": s["longitude"],
            "speed": s["speed"],
            "heading": s["heading"],
            "fuel_level": s["fuel_level"],
            "fuel_pct": s["fuel_pct"] if "fuel_pct" in s else round((s["fuel_level"] / s["fuel_capacity"])*100.0, 1),
            "engine_status": s["engine_status"],
            "vehicle_status": s["vehicle_status"],
            "timestamp": datetime.now(timezone.utc),
            "current_trip_id": uuid.UUID(s["current_trip_id"]) if s["current_trip_id"] else None,
            "driver_name": s["driver_name"],
            "remaining_km": s["remaining_km"],
            "eta_minutes": s["eta_minutes"],
            "eta": s["eta"],
            "risk_level": s["risk_level"]
        }
    
    # Fallback to reading vehicle from DB
    db = SessionLocal()
    try:
        vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if vehicle:
            return {
                "vehicle_id": vehicle.id,
                "registration_number": vehicle.registration_number,
                "latitude": vehicle.current_lat or 19.0760,
                "longitude": vehicle.current_lon or 72.8777,
                "speed": 0.0,
                "heading": 0,
                "fuel_level": float(vehicle.current_fuel_level_l or 0.0),
                "fuel_pct": round((float(vehicle.current_fuel_level_l or 0.0)/float(vehicle.fuel_tank_capacity_l or 200.0))*100, 1) if vehicle.fuel_tank_capacity_l else 0.0,
                "engine_status": "off",
                "vehicle_status": "OFFLINE" if vehicle.status == "breakdown" else vehicle.status.upper(),
                "timestamp": datetime.now(timezone.utc),
                "current_trip_id": None,
                "driver_name": vehicle.driver.full_name if vehicle.driver else "No Driver Assigned",
                "remaining_km": 0.0,
                "eta_minutes": 0,
                "eta": None,
                "risk_level": "LOW"
            }
    finally:
        db.close()
    raise ValueError(f"Vehicle {vehicle_id} not found.")

def get_all_vehicle_states() -> List[dict]:
    # Merges memory simulation list with remaining DB vehicles
    states = []
    db = SessionLocal()
    try:
        vehicles = db.query(Vehicle).all()
        for v in vehicles:
            if str(v.id) in SIMULATIONS:
                states.append(get_vehicle_state(v.id))
            else:
                # Idle/offline DB states
                states.append({
                    "vehicle_id": v.id,
                    "registration_number": v.registration_number,
                    "latitude": v.current_lat or 19.0760,
                    "longitude": v.current_lon or 72.8777,
                    "speed": 0.0,
                    "heading": 0,
                    "fuel_level": float(v.current_fuel_level_l or 0.0),
                    "fuel_pct": round((float(v.current_fuel_level_l or 0.0)/float(v.fuel_tank_capacity_l or 200.0))*100, 1) if v.fuel_tank_capacity_l else 0.0,
                    "engine_status": "off",
                    "vehicle_status": "OFFLINE" if v.status == "breakdown" else v.status.upper(),
                    "timestamp": datetime.now(timezone.utc),
                    "current_trip_id": None,
                    "driver_name": v.driver.full_name if v.driver else "No Driver Assigned",
                    "remaining_km": 0.0,
                    "eta_minutes": 0,
                    "eta": None,
                    "risk_level": "LOW"
                })
    finally:
        db.close()
    return states

# Simulation Tick Thread Methods
def _complete_trip_in_db(db: Session, vehicle_id: str, trip_id: Optional[str]):
    try:
        v_uuid = uuid.UUID(vehicle_id)
        vehicle = db.query(Vehicle).filter(Vehicle.id == v_uuid).first()
        if vehicle:
            vehicle.status = "available"
        if trip_id:
            t_uuid = uuid.UUID(trip_id)
            route = db.query(Route).filter(Route.id == t_uuid).first()
            if route:
                route.status = "completed"
                route.actual_end_time = datetime.now(timezone.utc)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Failed to complete trip in DB: %s", e)

def _trigger_low_fuel_alert(db: Session, vehicle_id: str, registration_number: str, current_fuel: float):
    try:
        v_uuid = uuid.UUID(vehicle_id)
        recent = db.query(Notification).filter(
            Notification.notification_type == "low_fuel_alert",
            Notification.message.like(f"%{registration_number}%")
        ).order_by(Notification.created_at.desc()).first()
        
        if recent and (datetime.now(timezone.utc) - recent.created_at.replace(tzinfo=timezone.utc)).total_seconds() < 600:
            return  # Suppress repeat alerts
            
        recipient = db.query(User).filter(User.role.in_(["operator", "admin"])).first()
        if recipient:
            alert = Notification(
                user_id=recipient.id,
                notification_type="low_fuel_alert",
                title=f"⚠️ Low Fuel Alert: {registration_number}",
                message=f"Vehicle {registration_number} is running low on fuel ({current_fuel:.1f} L remaining). Recommended to stop at nearest IOCL/BPCL station.",
                is_read=False,
                created_at=datetime.now(timezone.utc)
            )
            db.add(alert)
            db.commit()
            logger.warning("Generated low-fuel alert for %s", registration_number)
    except Exception as e:
        db.rollback()
        logger.error("Failed to generate low-fuel alert: %s", e)

def _write_history_and_update_vehicle_in_db(db: Session, vehicle_id: str, state: dict):
    try:
        v_uuid = uuid.UUID(vehicle_id)
        t_uuid = uuid.UUID(state["trip_id"]) if state["trip_id"] else None
        
        vehicle = db.query(Vehicle).filter(Vehicle.id == v_uuid).first()
        if vehicle:
            vehicle.current_lat = state["latitude"]
            vehicle.current_lon = state["longitude"]
            vehicle.current_fuel_level_l = state["fuel_level"]
            vehicle.status = "in_transit" if state["vehicle_status"] == "IN_TRANSIT" else state["vehicle_status"].lower()
            
        history = VehicleLocationHistory(
            vehicle_id=v_uuid,
            trip_id=t_uuid,
            lat=state["latitude"],
            lon=state["longitude"],
            speed_kmh=state["speed"],
            heading_deg=state["heading"],
            fuel_level_l=state["fuel_level"],
            recorded_at=datetime.now(timezone.utc)
        )
        db.add(history)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Failed periodic DB telemetry update: %s", e)

# Simulation loop ticking
async def broadcast_fleet_update():
    if not ACTIVE_CONNECTIONS:
        return
    import json
    payload = {
        "type": "fleet_update",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "vehicles": [
            {
                "vehicle_id": str(s["vehicle_id"]),
                "registration_number": s["registration_number"],
                "latitude": s["latitude"],
                "longitude": s["longitude"],
                "speed": s["speed"],
                "heading": s["heading"],
                "fuel_level": s["fuel_level"],
                "fuel_pct": s["fuel_pct"] if "fuel_pct" in s else round((s["fuel_level"] / s["fuel_capacity"])*100.0, 1),
                "engine_status": s["engine_status"],
                "vehicle_status": s["vehicle_status"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "current_trip_id": s["current_trip_id"],
                "driver_name": s["driver_name"],
                "remaining_km": s["remaining_km"],
                "eta_minutes": s["eta_minutes"],
                "eta": s["eta"],
                "risk_level": s["risk_level"]
            }
            for s in get_all_vehicle_states()
        ]
    }
    dead = []
    for ws in ACTIVE_CONNECTIONS:
        try:
            await ws.send_text(json.dumps(payload))
        except Exception:
            dead.append(ws)
    for ws in dead:
        if ws in ACTIVE_CONNECTIONS:
            ACTIVE_CONNECTIONS.remove(ws)

async def tick_simulations():
    if not SIMULATIONS:
        return
    db = SessionLocal()
    try:
        updated = False
        for vehicle_id, state in list(SIMULATIONS.items()):
            if state["is_paused"]:
                continue
                
            # Simulate real-time movement speed (55 to 75 km/h)
            speed = round(random.uniform(55.0, 75.0), 1)
            state["speed"] = speed

            path = state["path"]
            stop_idx = state["stop_index"]

            lat_start, lon_start = path[stop_idx][0], path[stop_idx][1]
            lat_end, lon_end = path[stop_idx + 1][0], path[stop_idx + 1][1]

            leg_dist = haversine_distance(lat_start, lon_start, lat_end, lon_end)
            if leg_dist < 0.01:
                state["progress_pct"] = 1.0
            else:
                # Distance traveled in 3 seconds leg progress
                dist_km = (speed / 3600.0) * 3
                state["progress_pct"] += dist_km / leg_dist

            # Leg completion logic
            if state["progress_pct"] >= 1.0:
                state["progress_pct"] = 0.0
                state["stop_index"] += 1
                
                if state["stop_index"] >= len(path) - 1:
                    state["latitude"] = path[-1][0]
                    state["longitude"] = path[-1][1]
                    state["speed"] = 0.0
                    state["vehicle_status"] = "STOPPED"
                    state["engine_status"] = "off"
                    state["remaining_km"] = 0.0
                    state["eta_minutes"] = 0
                    
                    _complete_trip_in_db(db, vehicle_id, state["trip_id"])
                    SIMULATIONS.pop(vehicle_id, None)
                    updated = True
                    continue
                else:
                    stop_idx = state["stop_index"]
                    lat_start, lon_start = path[stop_idx][0], path[stop_idx][1]
                    lat_end, lon_end = path[stop_idx + 1][0], path[stop_idx + 1][1]
                    leg_dist = haversine_distance(lat_start, lon_start, lat_end, lon_end)

            p = state["progress_pct"]
            curr_lat = lat_start + p * (lat_end - lat_start)
            curr_lon = lon_start + p * (lon_end - lon_start)
            state["latitude"] = round(curr_lat, 6)
            state["longitude"] = round(curr_lon, 6)
            state["heading"] = calculate_bearing(lat_start, lon_start, lat_end, lon_end)

            # Realistic fuel decrease based on nominal fuel efficiency
            dist_in_tick = (speed / 3600.0) * 3
            fuel_consumed = dist_in_tick / state["fuel_efficiency"]
            state["fuel_level"] = max(0.0, round(state["fuel_level"] - fuel_consumed, 2))
            
            # Fuel percentage remaining
            fuel_pct = round((state["fuel_level"] / state["fuel_capacity"]) * 100.0, 1) if state["fuel_capacity"] > 0 else 0
            state["fuel_pct"] = fuel_pct

            # Status trigger on low fuel
            if fuel_pct < 15.0:
                state["vehicle_status"] = "LOW_FUEL"
                _trigger_low_fuel_alert(db, vehicle_id, state["registration_number"], state["fuel_level"])
            else:
                state["vehicle_status"] = "IN_TRANSIT"

            # Compute remaining distance and call ETA calculation
            rem_km = calculate_remaining_distance(state["latitude"], state["longitude"], path, state["stop_index"])
            state["remaining_km"] = round(rem_km, 1)

            active_ship_id = None
            for i in range(state["stop_index"], len(path)):
                if path[i][4]:
                    active_ship_id = path[i][4]
                    break

            eta_res = calculate_eta(db, vehicle_id, rem_km, speed, active_ship_id)
            state["eta_minutes"] = eta_res["remaining_duration_min"]
            state["eta"] = eta_res["eta"]
            state["risk_level"] = eta_res["risk_level"]

            state["tick_count"] += 1
            if state["tick_count"] % 5 == 0:
                _write_history_and_update_vehicle_in_db(db, vehicle_id, state)

            updated = True

        if updated:
            await broadcast_fleet_update()
    except Exception as e:
        logger.error("Failed simulation tick execution: %s", e)
    finally:
        db.close()

async def run_simulation_loop():
    logger.info("GPS Simulation loop background task initialized")
    while True:
        try:
            await asyncio.sleep(3)
            await tick_simulations()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("Unhandled simulation loop error: %s", e, exc_info=True)
