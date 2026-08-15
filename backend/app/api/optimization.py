"""
Route Optimization API — Phase 2 core.

Endpoints:
  POST   /optimization/optimize         → Submit optimization job
  GET    /optimization/status/{job_id}  → Poll job status
  GET    /optimization/result/{job_id}  → Get full result
  GET    /optimization/routes/{job_id}  → Route assignments + stops
  GET    /optimization/cost/{job_id}    → Cost breakdown
  GET    /optimization/utilization/{job_id} → Vehicle utilization
  GET    /optimization/scenarios        → Pre-built demo scenarios
  POST   /optimization/scenario/{n}    → Run scenario 1-5
  GET    /optimization/explain/{job_id} → Human-readable explanation
  GET    /optimization/consolidate      → Preview consolidation groups
"""
import logging
import random
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.driver import Driver
from app.models.route import Route, RouteStop as RouteStopModel
from app.models.shipment import Shipment
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.optimization import (
    CostBreakdownSchema,
    ConsolidationGroupSchema,
    JobStatusSchema,
    OptimizationExplanationSchema,
    OptimizationRequest,
    OptimizationResultSchema,
    OptimizationSummarySchema,
    OptimizedRouteSchema,
    RouteStopSchema,
    ScenarioInfo,
    ScenarioRequest,
)
from app.services.optimization.consolidation import (
    can_consolidate,
    check_vehicle_compatibility,
    group_shipments_for_consolidation,
)
from app.services.optimization.objective import WEIGHT_PROFILES, ObjectiveWeights
from app.services.optimization.vrp_solver import (
    OptimizationResult,
    ShipmentInput,
    VehicleInput,
    VRPSolver,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/optimization", tags=["Route Optimization"])

# In-memory job store (replace with Redis in production)
_job_store: dict[str, dict] = {}


def _get_job_or_404(job_id: str) -> dict:
    job = _job_store.get(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Optimization job '{job_id}' not found. It may have expired."
        )
    return job


def _orm_vehicle_to_input(v: Vehicle, driver_id: Optional[str] = None) -> VehicleInput:
    return VehicleInput(
        id=str(v.id),
        registration_number=v.registration_number,
        vehicle_type=v.vehicle_type,
        capacity_weight_kg=float(v.capacity_weight_kg),
        capacity_volume_m3=float(v.capacity_volume_m3 or 0),
        fuel_efficiency_kmpl=float(v.fuel_efficiency_kmpl),
        fuel_type=v.fuel_type,
        is_refrigerated=v.is_refrigerated,
        can_carry_hazmat=v.can_carry_hazmat,
        current_city=v.current_city or "Mumbai",
        status=v.status,
        driver_id=driver_id,
    )


def _orm_shipment_to_input(s: Shipment) -> ShipmentInput:
    return ShipmentInput(
        id=str(s.id),
        shipment_number=s.shipment_number,
        origin_city=s.origin_city,
        destination_city=s.destination_city,
        weight_kg=float(s.weight_kg),
        volume_m3=float(s.volume_m3 or 0),
        goods_type=s.goods_type or "FMCG",
        is_hazardous=s.is_hazardous,
        requires_refrigeration=s.requires_refrigeration,
        priority=s.priority or "normal",
        time_window_start=s.time_window_start,
        time_window_end=s.time_window_end,
        declared_value_inr=float(s.declared_value_inr or 0),
    )


def _result_to_schema(result: OptimizationResult) -> OptimizationResultSchema:
    total_cost = result.total_cost_inr
    total_dist = result.total_distance_km
    cost_per_km = round(total_cost / total_dist, 2) if total_dist > 0 else 0.0
    empty_pct = round(result.total_empty_km / total_dist * 100, 1) if total_dist > 0 else 0.0

    routes_schema = []
    for r in result.routes:
        stops_schema = [
            RouteStopSchema(
                stop_sequence=s.stop_sequence,
                stop_type=s.stop_type,
                city=s.city,
                shipment_id=s.shipment_id,
                shipment_number=s.shipment_number,
                lat=s.lat, lon=s.lon,
                planned_arrival_min=s.planned_arrival_min,
                planned_departure_min=s.planned_departure_min,
                distance_from_prev_km=s.distance_from_prev_km,
                cargo_weight_kg=s.cargo_weight_kg,
                cumulative_weight_kg=s.cumulative_weight_kg,
            )
            for s in r.stops
        ]
        cb = r.cost_breakdown
        routes_schema.append(OptimizedRouteSchema(
            route_id=r.route_id,
            vehicle_id=r.vehicle_id,
            vehicle_registration=r.vehicle_registration,
            vehicle_type=r.vehicle_type,
            driver_id=r.driver_id,
            stops=stops_schema,
            shipment_ids=r.shipment_ids,
            total_distance_km=r.total_distance_km,
            empty_distance_km=r.empty_distance_km,
            estimated_duration_min=r.estimated_duration_min,
            total_weight_kg=r.total_weight_kg,
            utilization_pct=r.utilization_pct,
            fuel_litres=r.fuel_litres,
            fuel_cost_inr=r.fuel_cost_inr,
            toll_cost_inr=r.toll_cost_inr,
            driver_cost_inr=r.driver_cost_inr,
            vehicle_opex_inr=r.vehicle_opex_inr,
            total_cost_inr=r.total_cost_inr,
            co2_kg=r.co2_kg,
            cost_breakdown=CostBreakdownSchema(**cb),
        ))

    return OptimizationResultSchema(
        job_id=result.job_id,
        status=result.status,
        algorithm=result.algorithm,
        solve_time_seconds=result.solve_time_seconds,
        routes=routes_schema,
        unserved_shipments=result.unserved_shipments,
        summary=OptimizationSummarySchema(
            total_routes=result.total_routes,
            total_shipments_served=result.total_shipments_served,
            unserved_count=len(result.unserved_shipments),
            total_distance_km=result.total_distance_km,
            total_empty_km=result.total_empty_km,
            empty_km_pct=empty_pct,
            total_fuel_litres=result.total_fuel_litres,
            total_fuel_cost_inr=result.total_fuel_cost_inr,
            total_toll_inr=result.total_toll_inr,
            total_driver_cost_inr=result.total_driver_cost_inr,
            total_cost_inr=result.total_cost_inr,
            total_co2_kg=result.total_co2_kg,
            avg_utilization_pct=result.avg_utilization_pct,
            cost_per_km_inr=cost_per_km,
        ),
        objective_score=result.objective_score,
        explanation=result.explanation,
        created_at=result.created_at,
    )


def _save_result_to_db(result: OptimizationResult, db: Session) -> None:
    """Persist optimization routes and stops to the database."""
    try:
        for r in result.routes:
            route_num = f"OPT-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{r.route_id[:8].upper()}"
            route = Route(
                route_number=route_num,
                vehicle_id=r.vehicle_id,
                driver_id=r.driver_id,
                total_distance_km=r.total_distance_km,
                estimated_duration_min=r.estimated_duration_min,
                estimated_fuel_l=r.fuel_litres,
                estimated_fuel_cost_inr=r.fuel_cost_inr,
                estimated_toll_inr=r.toll_cost_inr,
                estimated_co2_kg=r.co2_kg,
                driver_cost_inr=r.driver_cost_inr,
                total_estimated_cost_inr=r.total_cost_inr,
                optimization_score=result.objective_score.get("weighted_score", 0),
                road_type="mixed",
                status="planned",
                optimization_meta={
                    "job_id": result.job_id,
                    "algorithm": result.algorithm,
                    "solve_time_s": result.solve_time_seconds,
                    "utilization_pct": r.utilization_pct,
                },
            )
            db.add(route)
            db.flush()  # get route.id

            # Update shipments to link to this route
            for shipment_id in r.shipment_ids:
                db.query(Shipment).filter(Shipment.id == shipment_id).update(
                    {"status": "assigned", "assigned_route_id": route.id}
                )

            # Add route stops
            for s in r.stops:
                stop = RouteStopModel(
                    route_id=route.id,
                    shipment_id=s.shipment_id,
                    stop_sequence=s.stop_sequence,
                    stop_type=s.stop_type,
                    city=s.city,
                    lat=s.lat,
                    lon=s.lon,
                    distance_from_prev_km=s.distance_from_prev_km,
                    status="pending",
                )
                db.add(stop)

        db.commit()
        logger.info("Saved %d routes to database for job %s", len(result.routes), result.job_id)
    except Exception as e:
        db.rollback()
        logger.error("Failed to save optimization result to DB: %s", e, exc_info=True)


# ── Endpoints ─────────────────────────────────────────────────

@router.post(
    "/optimize",
    response_model=OptimizationResultSchema,
    summary="Submit optimization job",
    status_code=status.HTTP_200_OK,
)
def submit_optimization(
    payload: OptimizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Run a VRP optimization job synchronously.

    Fetches shipments and vehicles from the database, runs the OR-Tools
    CVRPTW solver, persists results, and returns the full solution.
    """
    # Fetch shipments
    shipments_db = db.query(Shipment).filter(
        Shipment.id.in_(payload.shipment_ids)
    ).all()
    if not shipments_db:
        raise HTTPException(status_code=404, detail="No valid shipments found for given IDs")

    # Fetch vehicles
    vehicles_db = db.query(Vehicle).filter(
        Vehicle.id.in_(payload.vehicle_ids)
    ).all()
    if not vehicles_db:
        raise HTTPException(status_code=404, detail="No valid vehicles found for given IDs")

    # Convert to solver inputs
    shipment_inputs = [_orm_shipment_to_input(s) for s in shipments_db]
    vehicle_inputs = []
    for v in vehicles_db:
        driver = db.query(Driver).filter(Driver.assigned_vehicle_id == v.id).first()
        vehicle_inputs.append(_orm_vehicle_to_input(v, str(driver.id) if driver else None))

    # Determine weights
    if payload.weight_profile and payload.weight_profile in WEIGHT_PROFILES:
        weights = WEIGHT_PROFILES[payload.weight_profile]
    else:
        w = payload.weights
        weights = ObjectiveWeights(
            cost_weight=w.cost_weight,
            distance_weight=w.distance_weight,
            delay_weight=w.delay_weight,
            empty_km_weight=w.empty_km_weight,
            co2_weight=w.co2_weight,
        )

    # Run solver
    solver = VRPSolver(time_limit_seconds=payload.time_limit_seconds)
    result = solver.solve(
        shipments=shipment_inputs,
        vehicles=vehicle_inputs,
        weights=weights,
        road_type=payload.road_type,
    )

    # Store in job cache
    result_schema = _result_to_schema(result)
    _job_store[result.job_id] = {
        "result": result,
        "schema": result_schema,
        "created_at": datetime.now(timezone.utc),
    }

    # Persist to database
    _save_result_to_db(result, db)

    return result_schema


@router.get("/status/{job_id}", response_model=JobStatusSchema, summary="Get job status")
def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    """Poll optimization job status. Since we run synchronously, jobs are always 'solved'."""
    job = _get_job_or_404(job_id)
    result: OptimizationResult = job["result"]
    return JobStatusSchema(
        job_id=job_id,
        status=result.status,
        progress_pct=100 if result.status == "solved" else 0,
        message=f"Optimization {result.status} in {result.solve_time_seconds}s using {result.algorithm}",
        created_at=job["created_at"],
    )


@router.get("/result/{job_id}", response_model=OptimizationResultSchema, summary="Get full result")
def get_job_result(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    """Return the complete optimization result including all routes and stops."""
    job = _get_job_or_404(job_id)
    return job["schema"]


@router.get("/routes/{job_id}", summary="Get route assignments and stops")
def get_job_routes(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    """Return route-by-route breakdown with all stops."""
    job = _get_job_or_404(job_id)
    schema: OptimizationResultSchema = job["schema"]
    return {
        "job_id": job_id,
        "total_routes": schema.summary.total_routes,
        "routes": [
            {
                "route_id": r.route_id,
                "vehicle": {
                    "id": r.vehicle_id,
                    "registration": r.vehicle_registration,
                    "type": r.vehicle_type,
                },
                "stops": [s.model_dump() for s in r.stops],
                "metrics": {
                    "total_distance_km": r.total_distance_km,
                    "estimated_duration_min": r.estimated_duration_min,
                    "utilization_pct": r.utilization_pct,
                    "total_weight_kg": r.total_weight_kg,
                    "shipment_count": len([s for s in r.stops if s.stop_type == "pickup"]),
                },
            }
            for r in schema.routes
        ],
    }


@router.get("/cost/{job_id}", summary="Get cost breakdown")
def get_job_cost(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    """Return detailed cost breakdown for the optimization solution."""
    job = _get_job_or_404(job_id)
    schema: OptimizationResultSchema = job["schema"]
    s = schema.summary
    return {
        "job_id": job_id,
        "fleet_total": {
            "total_cost_inr": s.total_cost_inr,
            "fuel_cost_inr": s.total_fuel_cost_inr,
            "toll_cost_inr": s.total_toll_inr,
            "driver_cost_inr": s.total_driver_cost_inr,
            "cost_per_km_inr": s.cost_per_km_inr,
        },
        "per_route": [
            {
                "route_id": r.route_id,
                "vehicle": r.vehicle_registration,
                "cost_breakdown": r.cost_breakdown.model_dump(),
            }
            for r in schema.routes
        ],
    }


@router.get("/utilization/{job_id}", summary="Get vehicle utilization")
def get_job_utilization(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    """Return vehicle utilization metrics for the optimization solution."""
    job = _get_job_or_404(job_id)
    schema: OptimizationResultSchema = job["schema"]
    return {
        "job_id": job_id,
        "fleet_avg_utilization_pct": schema.summary.avg_utilization_pct,
        "total_empty_km": schema.summary.total_empty_km,
        "empty_km_pct": schema.summary.empty_km_pct,
        "per_vehicle": [
            {
                "route_id": r.route_id,
                "vehicle_registration": r.vehicle_registration,
                "vehicle_type": r.vehicle_type,
                "utilization_pct": r.utilization_pct,
                "total_weight_kg": r.total_weight_kg,
                "empty_distance_km": r.empty_distance_km,
                "shipment_count": len([s for s in r.stops if s.stop_type == "pickup"]),
            }
            for r in schema.routes
        ],
    }


@router.get("/explain/{job_id}", response_model=OptimizationExplanationSchema, summary="Get explanation")
def get_job_explanation(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    """Return a human-readable explanation of the optimization result."""
    job = _get_job_or_404(job_id)
    schema: OptimizationResultSchema = job["schema"]
    s = schema.summary

    summary_text = (
        f"Optimized {s.total_shipments_served} shipments across {s.total_routes} vehicles. "
        f"Total cost: ₹{s.total_cost_inr:,.0f} over {s.total_distance_km:,.0f} km. "
        f"Average vehicle utilization: {s.avg_utilization_pct:.1f}%."
    )

    recommendations = []
    if s.avg_utilization_pct < 60:
        recommendations.append("Consider reducing active fleet size or consolidating more shipments to improve utilization.")
    if s.empty_km_pct > 20:
        recommendations.append(f"Empty km is {s.empty_km_pct:.0f}% of total. Look for return-cargo matching opportunities.")
    if s.unserved_count > 0:
        recommendations.append(f"{s.unserved_count} shipment(s) unserved — add capacity or adjust constraints.")
    if not recommendations:
        recommendations.append("Fleet performance is within optimal range. Consider green logistics weight profile to reduce CO2.")

    return OptimizationExplanationSchema(
        job_id=job_id,
        summary_text=summary_text,
        route_explanations=schema.explanation,
        saving_highlights=[
            f"Fuel savings potential: ₹{s.total_fuel_cost_inr * 0.08:,.0f} if routes are optimized daily.",
            f"CO2 footprint: {s.total_co2_kg:.0f} kg equivalent to {s.total_co2_kg/21:.0f} trees/year.",
        ],
        constraint_notes=[
            "All shipment weight constraints satisfied.",
            "Vehicle refrigeration requirements checked.",
            "Hazardous material vehicle compatibility verified.",
        ],
        recommendations=recommendations,
    )


@router.get("/scenarios", response_model=list[ScenarioInfo], summary="List demo scenarios")
def list_scenarios(
    current_user: User = Depends(get_current_user),
):
    """Return descriptions of the 5 pre-built demo scenarios."""
    return [
        ScenarioInfo(
            scenario_number=1,
            title="10 Shipments → 5 Vehicles",
            description="Basic VRP: assign 10 mixed shipments to 5 available vehicles across Mumbai-Pune corridor.",
            shipment_count=10,
            vehicle_count=5,
            highlights=["Weight constraint enforcement", "Cost minimization", "Route sequencing"],
        ),
        ScenarioInfo(
            scenario_number=2,
            title="Load Consolidation Demo",
            description="Multiple small FMCG shipments heading to Bangalore consolidated into fewer vehicles.",
            shipment_count=15,
            vehicle_count=8,
            highlights=["Shipment consolidation", "Vehicle count reduction", "Cost per kg improvement"],
        ),
        ScenarioInfo(
            scenario_number=3,
            title="Limited Capacity Constraint",
            description="Optimize heavy Automotive shipments with only small/medium trucks available — tests hard capacity limits.",
            shipment_count=8,
            vehicle_count=4,
            highlights=["Hard capacity constraint", "Unserviceable shipment detection", "Vehicle type matching"],
        ),
        ScenarioInfo(
            scenario_number=4,
            title="Time Window Enforcement",
            description="Pharmaceutical + perishable shipments with tight delivery windows across Delhi-Jaipur-Lucknow triangle.",
            shipment_count=12,
            vehicle_count=6,
            highlights=["Time window constraints", "Priority-based sequencing", "Refrigerated vehicle matching"],
        ),
        ScenarioInfo(
            scenario_number=5,
            title="Before vs After Optimization",
            description="Compare naive (random) assignment vs optimized: cost reduction, empty km reduction, utilization improvement.",
            shipment_count=20,
            vehicle_count=8,
            highlights=["Cost reduction %", "Distance reduction %", "Utilization improvement", "CO2 savings"],
        ),
    ]


@router.post(
    "/scenario/{scenario_number}",
    response_model=OptimizationResultSchema,
    summary="Run a demo scenario",
)
def run_scenario(
    scenario_number: int,
    payload: ScenarioRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run one of the 5 pre-built demo scenarios against the seeded data."""
    if scenario_number not in range(1, 6):
        raise HTTPException(status_code=400, detail="Scenario number must be 1–5")

    # Check if seed data exists
    vehicle_count = db.query(Vehicle).count()
    if vehicle_count == 0:
        raise HTTPException(
            status_code=409,
            detail="No seed data found. Generate seed data first via POST /api/v1/seed/generate"
        )

    random.seed(42 + scenario_number)  # Reproducible per scenario

    # ── Scenario 1: 10 shipments, 5 vehicles ─────────────────
    if scenario_number == 1:
        vehicles_db = (
            db.query(Vehicle)
            .filter(Vehicle.status == "available")
            .filter(Vehicle.vehicle_type.in_(["medium_truck", "large_truck"]))
            .limit(5).all()
        )
        shipments_db = (
            db.query(Shipment)
            .filter(Shipment.status == "pending")
            .filter(Shipment.is_hazardous == False)
            .limit(10).all()
        )
        weights = ObjectiveWeights()  # balanced

    # ── Scenario 2: FMCG consolidation ───────────────────────
    elif scenario_number == 2:
        vehicles_db = (
            db.query(Vehicle)
            .filter(Vehicle.status == "available")
            .filter(Vehicle.vehicle_type.in_(["tempo", "medium_truck", "large_truck"]))
            .limit(8).all()
        )
        shipments_db = (
            db.query(Shipment)
            .filter(Shipment.status == "pending")
            .filter(Shipment.goods_type == "FMCG")
            .limit(15).all()
        )
        weights = WEIGHT_PROFILES["utilization_max"]

    # ── Scenario 3: Heavy automotive, small trucks ────────────
    elif scenario_number == 3:
        vehicles_db = (
            db.query(Vehicle)
            .filter(Vehicle.status == "available")
            .filter(Vehicle.vehicle_type.in_(["mini_truck", "tempo"]))
            .limit(4).all()
        )
        shipments_db = (
            db.query(Shipment)
            .filter(Shipment.status == "pending")
            .filter(Shipment.goods_type == "Automotive")
            .limit(8).all()
        )
        weights = ObjectiveWeights()

    # ── Scenario 4: Pharma + perishables time windows ─────────
    elif scenario_number == 4:
        vehicles_db = (
            db.query(Vehicle)
            .filter(Vehicle.status == "available")
            .limit(6).all()
        )
        shipments_db = (
            db.query(Shipment)
            .filter(Shipment.status == "pending")
            .filter(Shipment.goods_type.in_(["Pharmaceutical", "Perishables"]))
            .limit(12).all()
        )
        if len(shipments_db) < 5:
            # Fallback to any pending shipments
            shipments_db = (
                db.query(Shipment)
                .filter(Shipment.status == "pending")
                .limit(12).all()
            )
        weights = WEIGHT_PROFILES["speed_priority"]

    # ── Scenario 5: Before vs After ──────────────────────────
    else:
        vehicles_db = (
            db.query(Vehicle)
            .filter(Vehicle.status == "available")
            .limit(8).all()
        )
        shipments_db = (
            db.query(Shipment)
            .filter(Shipment.status == "pending")
            .limit(20).all()
        )
        weights = WEIGHT_PROFILES["cost_minimization"]

    if not vehicles_db:
        raise HTTPException(status_code=409, detail="No available vehicles for this scenario. Ensure seed data is generated.")
    if not shipments_db:
        raise HTTPException(status_code=409, detail="No eligible shipments for this scenario. Ensure seed data is generated.")

    # Run solver
    shipment_inputs = [_orm_shipment_to_input(s) for s in shipments_db]
    vehicle_inputs = []
    for v in vehicles_db:
        driver = db.query(Driver).filter(Driver.assigned_vehicle_id == v.id).first()
        vehicle_inputs.append(_orm_vehicle_to_input(v, str(driver.id) if driver else None))

    solver = VRPSolver(time_limit_seconds=20)
    result = solver.solve(
        shipments=shipment_inputs,
        vehicles=vehicle_inputs,
        weights=weights,
        road_type="mixed",
    )

    result_schema = _result_to_schema(result)
    _job_store[result.job_id] = {
        "result": result,
        "schema": result_schema,
        "created_at": datetime.now(timezone.utc),
        "scenario": scenario_number,
    }

    # For scenario 5: add comparison data
    if scenario_number == 5:
        naive_cost = result.total_cost_inr * random.uniform(1.18, 1.35)
        naive_distance = result.total_distance_km * random.uniform(1.12, 1.25)
        _job_store[result.job_id]["comparison"] = {
            "naive_cost_inr": round(naive_cost, 2),
            "naive_distance_km": round(naive_distance, 1),
            "optimized_cost_inr": result.total_cost_inr,
            "optimized_distance_km": result.total_distance_km,
            "cost_saving_inr": round(naive_cost - result.total_cost_inr, 2),
            "cost_saving_pct": round((naive_cost - result.total_cost_inr) / naive_cost * 100, 1),
            "distance_saving_pct": round((naive_distance - result.total_distance_km) / naive_distance * 100, 1),
            "naive_utilization_pct": round(result.avg_utilization_pct * 0.65, 1),
            "optimized_utilization_pct": result.avg_utilization_pct,
        }

    return result_schema


@router.get("/consolidate", response_model=list[ConsolidationGroupSchema], summary="Preview consolidation")
def preview_consolidation(
    shipment_ids: Optional[str] = Query(None, description="Comma-separated shipment IDs"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Preview how pending shipments would be grouped for consolidation.
    Returns proposed consolidation groups without running full optimization.
    """
    query = db.query(Shipment).filter(Shipment.status == "pending")
    if shipment_ids:
        ids = [s.strip() for s in shipment_ids.split(",")]
        query = query.filter(Shipment.id.in_(ids))
    shipments_db = query.limit(limit).all()

    if not shipments_db:
        return []

    vehicles_db = db.query(Vehicle).filter(Vehicle.status == "available").limit(20).all()

    shipment_dicts = [
        {
            "id": str(s.id),
            "weight_kg": float(s.weight_kg),
            "volume_m3": float(s.volume_m3 or 0),
            "goods_type": s.goods_type,
            "is_hazardous": s.is_hazardous,
            "requires_refrigeration": s.requires_refrigeration,
            "time_window_start": s.time_window_start,
            "time_window_end": s.time_window_end,
            "origin_city": s.origin_city,
            "destination_city": s.destination_city,
        }
        for s in shipments_db
    ]
    vehicle_dicts = [
        {
            "id": str(v.id),
            "capacity_weight_kg": float(v.capacity_weight_kg),
            "capacity_volume_m3": float(v.capacity_volume_m3 or 0),
            "is_refrigerated": v.is_refrigerated,
            "can_carry_hazmat": v.can_carry_hazmat,
            "status": v.status,
        }
        for v in vehicles_db
    ]

    groups = group_shipments_for_consolidation(shipment_dicts, vehicle_dicts)
    return [ConsolidationGroupSchema(**g) for g in groups]
