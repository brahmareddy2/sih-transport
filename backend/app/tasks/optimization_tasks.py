"""
Optimization task implementations using OR-Tools VRP Solver.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.shipment import Shipment
from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.services.optimization.vrp_solver import VRPSolver
from app.services.optimization.objective import ObjectiveWeights
from app.api.optimization import (
    _orm_shipment_to_input,
    _orm_vehicle_to_input,
    _save_result_to_db,
    _result_to_schema,
    _job_store,
)

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.optimization_tasks.run_vrp_optimization")
def run_vrp_optimization(
    self,
    shipment_ids: list[str],
    vehicle_ids: list[str],
    options: dict = None,
):
    """
    Async VRP optimization task run by Celery workers.
    Solves VRP and persists results to the database.
    """
    options = options or {}
    logger.info(
        "Celery VRP optimization task started: %d shipments, %d vehicles",
        len(shipment_ids), len(vehicle_ids)
    )

    db = SessionLocal()
    try:
        # 1. Fetch from DB
        shipments_db = db.query(Shipment).filter(Shipment.id.in_(shipment_ids)).all()
        vehicles_db = db.query(Vehicle).filter(Vehicle.id.in_(vehicle_ids)).all()

        if not shipments_db or not vehicles_db:
            return {
                "status": "failed",
                "message": "No valid shipments or vehicles found in database.",
            }

        # 2. Map inputs
        shipment_inputs = [_orm_shipment_to_input(s) for s in shipments_db]
        vehicle_inputs = []
        for v in vehicles_db:
            driver = db.query(Driver).filter(Driver.assigned_vehicle_id == v.id).first()
            vehicle_inputs.append(_orm_vehicle_to_input(v, str(driver.id) if driver else None))

        # 3. Configure weights
        w_dict = options.get("weights", {})
        weights = ObjectiveWeights(
            cost_weight=w_dict.get("cost_weight", 0.35),
            distance_weight=w_dict.get("distance_weight", 0.25),
            delay_weight=w_dict.get("delay_weight", 0.20),
            empty_km_weight=w_dict.get("empty_km_weight", 0.10),
            co2_weight=w_dict.get("co2_weight", 0.10),
        )

        # 4. Solve VRP
        time_limit = options.get("time_limit_seconds", 30)
        road_type = options.get("road_type", "mixed")

        solver = VRPSolver(time_limit_seconds=time_limit)
        result = solver.solve(
            shipments=shipment_inputs,
            vehicles=vehicle_inputs,
            weights=weights,
            road_type=road_type,
        )

        # 5. Persist
        _save_result_to_db(result, db)

        # 6. Cache locally (for worker-level checks)
        result_schema = _result_to_schema(result)
        _job_store[result.job_id] = {
            "result": result,
            "schema": result_schema,
            "created_at": datetime.now(timezone.utc),
        }

        return {
            "status": "solved",
            "job_id": result.job_id,
            "routes_planned": len(result.routes),
            "shipments_served": result.total_shipments_served,
            "unserved_shipments": result.unserved_shipments,
            "total_cost_inr": result.total_cost_inr,
            "total_distance_km": result.total_distance_km,
        }

    except Exception as e:
        logger.error("Celery task failed with error: %s", e, exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
        }
    finally:
        db.close()

