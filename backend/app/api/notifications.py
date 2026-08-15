"""
Phase 7 — Notifications API Router.

Provides real-time in-app notification management for disruptions, recovery recommendations,
trip assignments, and return cargo matches.
"""
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.notification import Notification
from app.models.user import User
from app.schemas.analytics import NotificationListResponse, NotificationResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "",
    response_model=NotificationListResponse,
    summary="List in-app notifications",
)
def list_notifications(
    unread_only: bool = Query(False, description="Filter only unread alerts"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List notifications for current user or all operational alerts for admin/operator."""
    q = db.query(Notification)

    # Filter by user if not admin/operator, or if requested
    if current_user.role not in ["admin", "operator", "fleet_manager"]:
        q = q.filter(Notification.user_id == current_user.id)

    if unread_only:
        q = q.filter(Notification.is_read == False)

    total = q.count()
    unread_count = (
        db.query(Notification)
        .filter(Notification.is_read == False)
        .count()
    )
    items = q.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "unread_count": unread_count,
        "items": items,
    }


@router.get(
    "/unread-count",
    summary="Get unread notification count badge",
)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fast counter endpoint for navigation bar badge."""
    q = db.query(Notification).filter(Notification.is_read == False)
    if current_user.role not in ["admin", "operator", "fleet_manager"]:
        q = q.filter(Notification.user_id == current_user.id)

    return {"unread_count": q.count()}


@router.post(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Mark single notification as read",
)
def mark_notification_read(
    notification_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.is_read = True
    try:
        db.commit()
        db.refresh(notif)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return notif


@router.post(
    "/mark-all-read",
    summary="Mark all notifications as read",
)
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Notification).filter(Notification.is_read == False)
    if current_user.role not in ["admin", "operator", "fleet_manager"]:
        q = q.filter(Notification.user_id == current_user.id)

    updated_count = q.update({Notification.is_read: True}, synchronize_session=False)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {"success": True, "marked_read_count": updated_count}
