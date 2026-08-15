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
    current_user: User = Depends(require_roles("admin", "operator", "customer")),
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
    return _shipment_to_dict(shipment)


@router.get("/pending", summary="List unassigned pending shipments")
def list_pending_shipments(
    current_user: User = Depends(require_roles("admin", "operator")),
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
    current_user: User = Depends(require_roles("admin", "operator")),
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
