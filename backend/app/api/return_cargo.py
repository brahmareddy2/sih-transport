"""
Phase 6 — Return Cargo Matching and Empty-Kilometer Reduction API Router.

Endpoints:
  POST   /return-cargo                             → Search/generate return cargo matches
  GET    /return-cargo                             → List return cargo matches
  GET    /return-cargo/opportunities               → List vehicles eligible for return cargo
  GET    /return-cargo/{id}                        → Get match detail
  GET    /return-cargo/matches/{vehicle_id}        → Find & rank return shipments for a vehicle
  POST   /return-cargo/{id}/match                  → Re-match / re-score a specific match
  POST   /return-cargo/matches/{match_id}/approve  → Approve match & generate return route
  POST   /return-cargo/matches/{match_id}/reject   → Reject match with reason
  GET    /return-cargo/analytics                   → Aggregate empty-km reduction analytics
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.return_cargo import ReturnCargoMatch
from app.models.shipment import Shipment
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.return_cargo import (
    ApproveMatchRequest,
    RejectMatchRequest,
    ReturnCargoAnalyticsResponse,
    ReturnCargoListResponse,
    ReturnCargoMatchResponse,
    ReturnCargoSearchRequest,
    ReturnRouteExecutionResult,
    VehicleReturnOpportunity,
)
from app.services.return_cargo.matching_engine import (
    execute_approve_return_match,
    find_return_matches_for_vehicle,
    get_safe_city_distance,
    persist_return_matches,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/return-cargo", tags=["Return Cargo & Empty-KM Reduction"])


def _build_match_response(m: ReturnCargoMatch) -> Dict[str, Any]:
    """Helper to convert ORM match to enriched response dict."""
    veh = m.vehicle
    shp = m.shipment
    return {
        "id": m.id,
        "vehicle_id": m.vehicle_id,
        "shipment_id": m.shipment_id,
        "route_id": m.route_id,
        "return_route_id": m.return_route_id,
        "origin_city": m.origin_city,
        "destination_city": m.destination_city,
        "vehicle_current_city": m.vehicle_current_city,
        "vehicle_home_city": m.vehicle_home_city,
        "empty_km_before": float(m.empty_km_before or 0),
        "empty_km_after": float(m.empty_km_after or 0),
        "empty_km_reduced": float(m.empty_km_reduced or 0),
        "empty_km_reduction_pct": float(m.empty_km_reduction_pct or 0),
        "loaded_distance_km": float(m.loaded_distance_km or 0),
        "detour_distance_km": float(m.detour_distance_km or 0),
        "additional_fuel_l": float(m.additional_fuel_l or 0),
        "additional_fuel_cost_inr": float(m.additional_fuel_cost_inr or 0),
        "additional_toll_cost_inr": float(m.additional_toll_cost_inr or 0),
        "total_additional_cost_inr": float(m.total_additional_cost_inr or 0),
        "estimated_revenue_inr": float(m.estimated_revenue_inr or 0),
        "net_benefit_inr": float(m.net_benefit_inr or 0),
        "match_score": float(m.match_score or 0),
        "compatibility_details": m.compatibility_details or {},
        "status": m.status,
        "rejection_reason": m.rejection_reason,
        "approved_by": m.approved_by,
        "approved_at": m.approved_at,
        "created_at": m.created_at,
        "updated_at": m.updated_at,
        "vehicle_registration": veh.registration_number if veh else None,
        "vehicle_type": veh.vehicle_type if veh else None,
        "vehicle_capacity_weight_kg": float(veh.capacity_weight_kg) if veh else None,
        "shipment_number": shp.shipment_number if shp else None,
        "shipment_weight_kg": float(shp.weight_kg) if shp else None,
        "shipment_goods_type": shp.goods_type if shp else None,
        "shipment_priority": shp.priority if shp else None,
        "is_refrigerated": shp.requires_refrigeration if shp else False,
        "is_hazardous": shp.is_hazardous if shp else False,
    }


# ── GET /return-cargo/opportunities ───────────────────────────────────────────

@router.get(
    "/opportunities",
    response_model=List[VehicleReturnOpportunity],
    summary="List vehicles with return cargo opportunities",
)
def get_return_opportunities(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "operator", "fleet_manager")),
):
    """
    List all vehicles in the fleet that are currently away from their home depot
    or have pending return cargo potential.
    """
    vehicles = db.query(Vehicle).all()
    opportunities = []

    for v in vehicles:
        curr_city = v.current_city or "Mumbai"
        home_city = v.home_depot_city or "Mumbai"
        potential_empty_km = get_safe_city_distance(curr_city, home_city)

        # Count available matches for this vehicle
        match_count = (
            db.query(ReturnCargoMatch)
            .filter(
                ReturnCargoMatch.vehicle_id == v.id,
                ReturnCargoMatch.status == "pending",
            )
            .count()
        )

        best_score = (
            db.query(func.max(ReturnCargoMatch.match_score))
            .filter(
                ReturnCargoMatch.vehicle_id == v.id,
                ReturnCargoMatch.status == "pending",
            )
            .scalar()
        )

        opportunities.append({
            "vehicle_id": v.id,
            "registration_number": v.registration_number,
            "vehicle_type": v.vehicle_type,
            "current_city": curr_city,
            "home_depot_city": home_city,
            "status": v.status,
            "capacity_weight_kg": float(v.capacity_weight_kg),
            "fuel_efficiency_kmpl": float(v.fuel_efficiency_kmpl),
            "is_refrigerated": v.is_refrigerated,
            "can_carry_hazmat": v.can_carry_hazmat,
            "potential_empty_km": round(potential_empty_km, 1),
            "available_matches_count": match_count,
            "best_match_score": float(best_score) if best_score is not None else None,
        })

    # Sort: vehicles with active matches and high potential empty-km first
    opportunities.sort(
        key=lambda o: (o["available_matches_count"] > 0, o["potential_empty_km"]),
        reverse=True,
    )
    return opportunities


# ── POST /return-cargo ────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=ReturnCargoListResponse,
    status_code=status.HTTP_200_OK,
    summary="Search & evaluate return cargo matches",
)
def search_return_cargo(
    payload: ReturnCargoSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "operator", "fleet_manager")),
):
    """
    Search and generate ranked return cargo matches for a vehicle or city pair.
    Persists evaluated matches in DB and returns ranked results.
    """
    results = []

    if payload.vehicle_id:
        veh = db.query(Vehicle).filter(Vehicle.id == payload.vehicle_id).first()
        if not veh:
            raise HTTPException(status_code=404, detail=f"Vehicle {payload.vehicle_id} not found")

        matches = find_return_matches_for_vehicle(
            vehicle=veh,
            db=db,
            current_city=payload.current_city,
            home_city=payload.destination_city,
            max_detour_km=payload.max_detour_km or 300.0,
            min_score=payload.min_score or 0.0,
        )
        persisted = persist_return_matches(veh, matches, db)
        results.extend(persisted)
    else:
        # Search for all vehicles with non-depot positioning
        vehicles = db.query(Vehicle).filter(Vehicle.status.in_(["available", "idle"])).limit(20).all()
        for v in vehicles:
            matches = find_return_matches_for_vehicle(
                vehicle=v,
                db=db,
                current_city=payload.current_city,
                home_city=payload.destination_city,
                max_detour_km=payload.max_detour_km or 300.0,
                min_score=payload.min_score or 0.0,
            )
            persisted = persist_return_matches(v, matches, db)
            results.extend(persisted)

    # Sort results by match score descending
    results.sort(key=lambda r: float(r.match_score or 0), reverse=True)

    return {
        "total": len(results),
        "items": [_build_match_response(r) for r in results],
    }


# ── GET /return-cargo ─────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=ReturnCargoListResponse,
    summary="List return cargo matches",
)
def list_return_cargo_matches(
    status_filter: Optional[str] = Query(None, alias="status"),
    vehicle_id: Optional[uuid.UUID] = Query(None),
    shipment_id: Optional[uuid.UUID] = Query(None),
    min_score: Optional[float] = Query(None, ge=0.0, le=100.0),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "operator", "fleet_manager")),
):
    """List return cargo matches with status, vehicle, and score filters."""
    q = db.query(ReturnCargoMatch)

    if status_filter:
        q = q.filter(ReturnCargoMatch.status == status_filter)
    if vehicle_id:
        q = q.filter(ReturnCargoMatch.vehicle_id == vehicle_id)
    if shipment_id:
        q = q.filter(ReturnCargoMatch.shipment_id == shipment_id)
    if min_score is not None:
        q = q.filter(ReturnCargoMatch.match_score >= min_score)

    total = q.count()
    items = q.order_by(ReturnCargoMatch.match_score.desc(), ReturnCargoMatch.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "items": [_build_match_response(m) for m in items],
    }


# ── GET /return-cargo/analytics ───────────────────────────────────────────────

@router.get(
    "/analytics",
    response_model=ReturnCargoAnalyticsResponse,
    summary="Return cargo empty-km and cost reduction analytics",
)
def get_return_cargo_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "operator", "fleet_manager")),
):
    """Calculate aggregate KPIs on empty-kilometer reduction, fuel saved, and cost benefits."""
    total_matches = db.query(ReturnCargoMatch).count()
    approved_matches = db.query(ReturnCargoMatch).filter(ReturnCargoMatch.status == "approved").all()
    rejected_matches_count = db.query(ReturnCargoMatch).filter(ReturnCargoMatch.status == "rejected").count()

    total_potential_empty = 0.0
    total_empty_reduced = 0.0
    total_fuel_saved_l = 0.0
    total_fuel_saved_inr = 0.0
    total_net_benefit = 0.0
    scores = []

    for m in approved_matches:
        empty_bef = float(m.empty_km_before or 0)
        empty_red = float(m.empty_km_reduced or 0)
        fuel_eff = float(m.vehicle.fuel_efficiency_kmpl if m.vehicle else 5.0)

        total_potential_empty += empty_bef
        total_empty_reduced += empty_red
        fuel_l = empty_red / max(0.1, fuel_eff)
        total_fuel_saved_l += fuel_l
        total_fuel_saved_inr += fuel_l * 93.0  # Diesel benchmark
        total_net_benefit += float(m.net_benefit_inr or 0)

    # Average score across all evaluated matches
    all_scores = db.query(ReturnCargoMatch.match_score).all()
    avg_score = round(sum(float(s[0] or 0) for s in all_scores) / max(1, len(all_scores)), 1) if all_scores else 0.0

    overall_pct = (
        round((total_empty_reduced / max(1.0, total_potential_empty)) * 100.0, 1)
        if total_potential_empty > 0
        else 0.0
    )

    # Top saving routes
    top_routes = []
    for m in approved_matches[:5]:
        top_routes.append({
            "route_pair": f"{m.origin_city} → {m.destination_city}",
            "empty_km_reduced": float(m.empty_km_reduced or 0),
            "savings_inr": float(m.net_benefit_inr or 0),
            "match_score": float(m.match_score or 0),
        })

    return {
        "total_potential_empty_km": round(total_potential_empty, 1),
        "total_empty_km_reduced": round(total_empty_reduced, 1),
        "overall_reduction_pct": overall_pct,
        "total_fuel_saved_l": round(total_fuel_saved_l, 1),
        "total_fuel_saved_inr": round(total_fuel_saved_inr, 2),
        "total_net_benefit_inr": round(total_net_benefit, 2),
        "total_matches_generated": total_matches,
        "total_approved_matches": len(approved_matches),
        "total_rejected_matches": rejected_matches_count,
        "average_match_score": avg_score,
        "top_saving_routes": top_routes,
    }


# ── GET /return-cargo/{id} ────────────────────────────────────────────────────

@router.get(
    "/{match_id}",
    response_model=ReturnCargoMatchResponse,
    summary="Get single return cargo match details",
)
def get_return_cargo_match(
    match_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "operator", "fleet_manager")),
):
    m = db.query(ReturnCargoMatch).filter(ReturnCargoMatch.id == match_id).first()
    if not m:
        raise HTTPException(status_code=404, detail=f"Return cargo match {match_id} not found")
    return _build_match_response(m)


# ── GET /return-cargo/matches/{vehicle_id} ────────────────────────────────────

@router.get(
    "/matches/{vehicle_id}",
    response_model=ReturnCargoListResponse,
    summary="Search & rank return cargo matches for a vehicle",
)
def get_matches_for_vehicle(
    vehicle_id: uuid.UUID,
    max_detour_km: float = Query(300.0, ge=0.0),
    min_score: float = Query(0.0, ge=0.0, le=100.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "operator", "fleet_manager")),
):
    """
    Evaluate and return ranked compatible return cargo shipments for a specific vehicle.
    """
    veh = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not veh:
        raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found")

    matches = find_return_matches_for_vehicle(
        vehicle=veh,
        db=db,
        max_detour_km=max_detour_km,
        min_score=min_score,
    )
    persisted = persist_return_matches(veh, matches, db)
    persisted.sort(key=lambda r: float(r.match_score or 0), reverse=True)

    return {
        "total": len(persisted),
        "items": [_build_match_response(p) for p in persisted],
    }


# ── POST /return-cargo/{id}/match ─────────────────────────────────────────────

@router.post(
    "/{match_id}/match",
    response_model=ReturnCargoMatchResponse,
    summary="Re-evaluate / refresh a return cargo match",
)
def refresh_return_match(
    match_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "operator")),
):
    """Recompute compatibility, cost metrics, and score for a match."""
    m = db.query(ReturnCargoMatch).filter(ReturnCargoMatch.id == match_id).first()
    if not m:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found")

    veh = m.vehicle
    shp = m.shipment
    if not veh or not shp:
        raise HTTPException(status_code=400, detail="Vehicle or shipment missing from match record")

    matches = find_return_matches_for_vehicle(
        vehicle=veh,
        db=db,
        current_city=m.vehicle_current_city,
        home_city=m.vehicle_home_city,
    )
    persisted = persist_return_matches(veh, matches, db)
    refreshed = next((p for p in persisted if p.id == match_id), m)
    return _build_match_response(refreshed)


# ── POST /return-cargo/matches/{match_id}/approve ─────────────────────────────

@router.post(
    "/matches/{match_id}/approve",
    response_model=ReturnRouteExecutionResult,
    summary="Approve return cargo match and generate optimized return route",
)
def approve_match(
    match_id: uuid.UUID,
    payload: ApproveMatchRequest = ApproveMatchRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "operator")),
):
    """
    Approve a return cargo match:
    - Creates an optimized return route in PostgreSQL
    - Assigns the return shipment
    - Updates vehicle status to in_transit
    - Emits in-app notifications
    """
    m = db.query(ReturnCargoMatch).filter(ReturnCargoMatch.id == match_id).first()
    if not m:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found")
    if m.status == "approved":
        raise HTTPException(status_code=400, detail="Match is already approved")
    if m.status == "rejected":
        raise HTTPException(status_code=400, detail="Cannot approve a rejected match")

    try:
        result = execute_approve_return_match(
            match=m,
            approver_user_id=current_user.id,
            db=db,
            notes=payload.notes,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to approve match: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── POST /return-cargo/matches/{match_id}/reject ──────────────────────────────

@router.post(
    "/matches/{match_id}/reject",
    response_model=ReturnCargoMatchResponse,
    summary="Reject a return cargo match",
)
def reject_match(
    match_id: uuid.UUID,
    payload: RejectMatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "operator")),
):
    """Reject a return cargo match with an explanation reason."""
    m = db.query(ReturnCargoMatch).filter(ReturnCargoMatch.id == match_id).first()
    if not m:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found")
    if m.status == "approved":
        raise HTTPException(status_code=400, detail="Cannot reject an already approved match")

    m.status = "rejected"
    m.rejection_reason = payload.rejection_reason
    try:
        db.commit()
        db.refresh(m)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return _build_match_response(m)
