"""
Phase 5 — Incident Management & Recovery Planning API Router.

Endpoints:
  POST   /incidents                                  Create incident
  GET    /incidents                                  List incidents
  GET    /incidents/{id}                             Incident detail
  POST   /incidents/{id}/simulate                    SIH demo simulation
  POST   /incidents/{id}/recover                     Generate recovery plans
  GET    /incidents/{id}/recovery-plans              List recovery plans
  POST   /incidents/{id}/recovery-plans/{pid}/approve  Approve & execute plan
  POST   /incidents/{id}/resolve                     Resolve incident
"""
import logging
import uuid
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.models.incident import Incident, RecoveryPlan
from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.models.route import Route
from app.models.notification import Notification
from app.schemas.incidents import (
    IncidentCreateRequest,
    IncidentSimulateRequest,
    IncidentResponse,
    IncidentListResponse,
    RecoveryPlanResponse,
    RecoveryOptionsResponse,
    ApproveRecoveryRequest,
    RecoveryExecutionResult,
    ResolveIncidentRequest,
)
from app.services.incidents.recovery import (
    simulate_incident,
    generate_recovery_options,
    persist_recovery_plans,
    execute_recovery_plan,
    find_affected_shipments,
    INCIDENT_SEVERITY_MAP,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/incidents", tags=["Incident Management"])


# ── Helper: Build IncidentResponse from ORM object ───────────────────────────

def _build_incident_response(inc: Incident, db: Session) -> dict:
    affected_count = 0
    if inc.route_id:
        affected_count = db.query(type(inc).__class__).filter(
            type(None) is not None
        ).count() if False else 0
        # Count from affected_shipment_ids list
        if inc.affected_shipment_ids:
            affected_count = len(inc.affected_shipment_ids)
        else:
            try:
                from app.models.shipment import Shipment
                affected_count = db.query(Shipment).filter(
                    Shipment.assigned_route_id == inc.route_id,
                    Shipment.status.in_(["assigned", "in_transit", "consolidated", "delayed"]),
                ).count()
            except Exception:
                pass

    plans_count = db.query(RecoveryPlan).filter(RecoveryPlan.incident_id == inc.id).count()

    return {
        "id": inc.id,
        "incident_type": inc.incident_type,
        "severity": inc.severity,
        "status": inc.status,
        "vehicle_id": inc.vehicle_id,
        "driver_id": inc.driver_id,
        "route_id": inc.route_id,
        "description": inc.description,
        "lat": inc.lat,
        "lon": inc.lon,
        "city": inc.city,
        "source": inc.source,
        "reported_at": inc.reported_at,
        "detected_at": inc.detected_at,
        "resolved_at": inc.resolved_at,
        "affected_shipment_ids": inc.affected_shipment_ids or [],
        "vehicle_registration": inc.vehicle.registration_number if inc.vehicle else None,
        "vehicle_type": inc.vehicle.vehicle_type if inc.vehicle else None,
        "driver_name": (
            inc.driver.full_name
            if inc.driver and hasattr(inc.driver, "full_name")
            else (inc.driver.employee_id if inc.driver else None)
        ),
        "route_number": inc.route.route_number if inc.route else None,
        "affected_shipment_count": affected_count,
        "recovery_plans_count": plans_count,
    }


def _build_plan_response(plan: RecoveryPlan) -> dict:
    return {
        "id": plan.id,
        "incident_id": plan.incident_id,
        "plan_type": plan.plan_type,
        "plan_description": plan.plan_description,
        "action_type": plan.action_type,
        "recommended_action": plan.recommended_action,
        "alternative_vehicle_id": plan.alternative_vehicle_id,
        "alternative_driver_id": plan.alternative_driver_id,
        "rerouted_route_id": plan.rerouted_route_id,
        "estimated_delay_min": plan.estimated_delay_min,
        "cost_impact_inr": float(plan.cost_impact_inr) if plan.cost_impact_inr else 0.0,
        "additional_distance_km": float(plan.additional_distance_km) if plan.additional_distance_km else 0.0,
        "recovery_score": float(plan.recovery_score) if plan.recovery_score else 0.0,
        "is_approved": plan.is_approved,
        "approved_at": plan.approved_at,
        "created_at": plan.created_at,
        "alternative_vehicle_registration": (
            plan.alternative_vehicle.registration_number
            if plan.alternative_vehicle else None
        ),
        "alternative_vehicle_type": (
            plan.alternative_vehicle.vehicle_type
            if plan.alternative_vehicle else None
        ),
        "alternative_driver_name": (
            plan.alternative_driver.full_name
            if plan.alternative_driver and hasattr(plan.alternative_driver, "full_name")
            else (plan.alternative_driver.employee_id if plan.alternative_driver else None)
        ),
    }


# ── POST /incidents ───────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new incident",
)
def create_incident(
    payload: IncidentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "operator", "fleet_manager", "driver")),
):
    """Create a new incident record manually."""
    severity = payload.severity or INCIDENT_SEVERITY_MAP.get(
        payload.incident_type.lower(), "medium"
    )

    # Validate vehicle exists
    vehicle = None
    if payload.vehicle_id:
        vehicle = db.query(Vehicle).filter(Vehicle.id == payload.vehicle_id).first()
        if not vehicle:
            raise HTTPException(status_code=404, detail=f"Vehicle {payload.vehicle_id} not found")

    # Validate route exists
    route = None
    if payload.route_id:
        route = db.query(Route).filter(Route.id == payload.route_id).first()
        if not route:
            raise HTTPException(status_code=404, detail=f"Route {payload.route_id} not found")

    # Collect affected shipments
    affected_ids = []
    if route:
        from app.models.shipment import Shipment
        shipments = db.query(Shipment).filter(
            Shipment.assigned_route_id == route.id,
            Shipment.status.in_(["assigned", "in_transit", "consolidated"]),
        ).all()
        affected_ids = [str(s.id) for s in shipments]

    incident = Incident(
        vehicle_id=payload.vehicle_id,
        driver_id=payload.driver_id,
        route_id=payload.route_id,
        incident_type=payload.incident_type.lower(),
        severity=severity,
        description=payload.description,
        lat=payload.lat or (vehicle.current_lat if vehicle else None),
        lon=payload.lon or (vehicle.current_lon if vehicle else None),
        city=payload.city or (vehicle.current_city if vehicle else None),
        source=payload.source or "manual",
        reported_at=datetime.now(timezone.utc),
        detected_at=datetime.now(timezone.utc),
        status="open",
        affected_shipment_ids=affected_ids,
    )
    db.add(incident)
    try:
        db.commit()
        db.refresh(incident)
    except Exception as e:
        db.rollback()
        logger.error("Failed to create incident: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

    return _build_incident_response(incident, db)


# ── GET /incidents ────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=IncidentListResponse,
    summary="List all incidents",
)
def list_incidents(
    status_filter: Optional[str] = Query(None, alias="status"),
    incident_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "operator", "fleet_manager")),
):
    """List incidents with optional filters. Most recent first."""
    q = db.query(Incident)
    if status_filter:
        q = q.filter(Incident.status == status_filter)
    if incident_type:
        q = q.filter(Incident.incident_type == incident_type.lower())
    if severity:
        q = q.filter(Incident.severity == severity.lower())

    total = q.count()
    incidents = q.order_by(Incident.reported_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "items": [_build_incident_response(inc, db) for inc in incidents],
    }


# ── GET /incidents/{incident_id} ──────────────────────────────────────────────

@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
    summary="Get incident details",
)
def get_incident(
    incident_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "operator", "fleet_manager")),
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    return _build_incident_response(incident, db)


# ── POST /incidents/{id}/simulate ─────────────────────────────────────────────

@router.post(
    "/{incident_id}/simulate",
    response_model=IncidentResponse,
    summary="[SIH Demo] Simulate an incident on a vehicle",
)
def simulate_incident_endpoint(
    incident_id: uuid.UUID,
    payload: IncidentSimulateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "operator")),
):
    """
    SIH Demo: Create and immediately trigger a simulated incident.
    Sets vehicle status, affects GPS simulation, creates alert notifications.
    """
    try:
        incident = simulate_incident(
            vehicle_id=payload.vehicle_id,
            incident_type=payload.incident_type,
            route_id=payload.route_id,
            db=db,
            description=payload.description,
        )
        return _build_incident_response(incident, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Simulate incident failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── POST /incidents/new/simulate (alternate: create + simulate in one shot) ──

@router.post(
    "/simulate",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="[SIH Demo] Create and simulate incident in one call",
)
def create_and_simulate(
    payload: IncidentSimulateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "operator")),
):
    """Create a fresh simulated incident from scratch (no pre-existing incident_id needed)."""
    try:
        incident = simulate_incident(
            vehicle_id=payload.vehicle_id,
            incident_type=payload.incident_type,
            route_id=payload.route_id,
            db=db,
            description=payload.description,
        )
        return _build_incident_response(incident, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Create+simulate incident failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── POST /incidents/{id}/recover ──────────────────────────────────────────────

@router.post(
    "/{incident_id}/recover",
    response_model=RecoveryOptionsResponse,
    summary="Generate recovery plan options for an incident",
)
def generate_recovery(
    incident_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "operator")),
):
    """
    Run the recovery engine against an open incident.
    Returns ranked list of recovery options (persisted to DB as RecoveryPlan rows).
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    if incident.status in ("resolved", "closed"):
        raise HTTPException(status_code=400, detail="Cannot generate recovery for a resolved incident")

    try:
        options = generate_recovery_options(incident_id, db)
        plans = persist_recovery_plans(incident_id, options, db)

        # Update incident status to acknowledged
        incident.status = "acknowledged"
        db.commit()

        plan_responses = [_build_plan_response(p) for p in plans]
        best = max(plan_responses, key=lambda x: x["recovery_score"]) if plan_responses else None

        return {
            "incident_id": incident.id,
            "incident_type": incident.incident_type,
            "plans": plan_responses,
            "recommended_plan_id": best["id"] if best else None,
        }
    except Exception as e:
        logger.error("Recovery generation failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── GET /incidents/{id}/recovery-plans ───────────────────────────────────────

@router.get(
    "/{incident_id}/recovery-plans",
    response_model=RecoveryOptionsResponse,
    summary="List recovery plans for an incident",
)
def list_recovery_plans(
    incident_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "operator", "fleet_manager")),
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    plans = db.query(RecoveryPlan).filter(
        RecoveryPlan.incident_id == incident_id
    ).order_by(RecoveryPlan.recovery_score.desc()).all()

    plan_responses = [_build_plan_response(p) for p in plans]
    best = max(plan_responses, key=lambda x: x["recovery_score"]) if plan_responses else None

    return {
        "incident_id": incident.id,
        "incident_type": incident.incident_type,
        "plans": plan_responses,
        "recommended_plan_id": best["id"] if best else None,
    }


# ── POST /incidents/{id}/recovery-plans/{plan_id}/approve ────────────────────

@router.post(
    "/{incident_id}/recovery-plans/{plan_id}/approve",
    response_model=RecoveryExecutionResult,
    summary="Approve and execute a recovery plan",
)
def approve_recovery_plan(
    incident_id: uuid.UUID,
    plan_id: uuid.UUID,
    payload: ApproveRecoveryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "operator")),
):
    """
    Approve the selected recovery plan and execute it:
    - Reassigns vehicle/driver on route
    - Updates shipments to 'delayed'
    - Recalculates route cost
    - Creates notifications
    - Updates GPS simulation
    - Marks incident as 'in_recovery'
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    plan = db.query(RecoveryPlan).filter(
        RecoveryPlan.id == plan_id,
        RecoveryPlan.incident_id == incident_id,
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail=f"Recovery plan {plan_id} not found")
    if plan.is_approved:
        raise HTTPException(status_code=400, detail="This recovery plan is already approved")

    try:
        result = execute_recovery_plan(
            incident=incident,
            plan=plan,
            approved_by_user_id=current_user.id,
            db=db,
        )
        return {
            "success": result["success"],
            "incident_id": uuid.UUID(result["incident_id"]),
            "plan_id": uuid.UUID(result["plan_id"]),
            "new_vehicle_id": uuid.UUID(result["new_vehicle_id"]) if result.get("new_vehicle_id") else None,
            "new_vehicle_registration": result.get("new_vehicle_registration"),
            "new_driver_id": uuid.UUID(result["new_driver_id"]) if result.get("new_driver_id") else None,
            "shipments_updated": result["shipments_updated"],
            "estimated_delay_min": result["estimated_delay_min"],
            "additional_cost_inr": result["additional_cost_inr"],
            "new_eta": result.get("new_eta"),
            "incident_status": result["incident_status"],
            "message": result["message"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Recovery execution failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── POST /incidents/{id}/resolve ──────────────────────────────────────────────

@router.post(
    "/{incident_id}/resolve",
    response_model=IncidentResponse,
    summary="Resolve an incident",
)
def resolve_incident(
    incident_id: uuid.UUID,
    payload: ResolveIncidentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "operator")),
):
    """Mark incident as resolved. Updates vehicle status back to available if applicable."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    incident.status = "resolved"
    incident.resolved_at = datetime.now(timezone.utc)
    if payload.resolution_notes:
        existing_desc = incident.description or ""
        incident.description = f"{existing_desc}\n\nResolution: {payload.resolution_notes}".strip()

    # If vehicle was in breakdown and now resolved, reset to available
    if incident.vehicle_id and incident.incident_type in ("breakdown", "tyre_puncture", "accident"):
        vehicle = db.query(Vehicle).filter(Vehicle.id == incident.vehicle_id).first()
        if vehicle and vehicle.status == "breakdown":
            vehicle.status = "available"

    try:
        db.commit()
        db.refresh(incident)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    # Notify operators
    try:
        operators = db.query(User).filter(User.role.in_(["admin", "operator"])).all()
        for op in operators:
            db.add(Notification(
                user_id=op.id,
                notification_type="incident_resolved",
                title=f"✅ Incident Resolved: {incident.incident_type.replace('_', ' ').title()}",
                message=(
                    f"Incident on vehicle "
                    f"{incident.vehicle.registration_number if incident.vehicle else 'N/A'} "
                    f"has been resolved."
                ),
                data_json={"incident_id": str(incident.id)},
                is_read=False,
            ))
        db.commit()
    except Exception:
        db.rollback()

    return _build_incident_response(incident, db)
