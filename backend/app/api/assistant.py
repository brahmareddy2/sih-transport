"""
Universal Assistant API Endpoints — Phase 8
Exposes query intent processing, interactive trip planning, and highway facility lookups.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.assistant.intent_engine import get_assistant_intent_engine
from app.services.assistant.location_provider import get_location_provider

router = APIRouter(prefix="/assistant", tags=["Universal Logistics Assistant"])


class AssistantQueryRequest(BaseModel):
    query: str
    language: Optional[str] = "en"
    current_fuel_l: Optional[float] = 150.0
    food_budget_inr: Optional[float] = 400.0
    confirmed: Optional[bool] = False
    action_payload: Optional[Dict[str, Any]] = None


class AssistantQueryResponse(BaseModel):
    intent: str
    language: str
    message: str
    text: str
    speech_text: str
    card_type: Optional[str] = None
    card_data: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    requires_confirmation: Optional[bool] = False
    is_authorized: Optional[bool] = True
    data_source: Optional[str] = "database"


@router.post("/query", response_model=AssistantQueryResponse)
def execute_assistant_query(
    req: AssistantQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Execute a natural-language voice or search query via the unified Assistant Intent Engine.
    Enforces RBAC security and multimodal entity extraction.
    """
    engine = get_assistant_intent_engine()
    result = engine.process_query(
        query=req.query,
        user_role=current_user.role,
        user_id=str(current_user.id),
        language=req.language or "en",
        current_fuel_l=req.current_fuel_l,
        food_budget_inr=req.food_budget_inr,
        confirmed=req.confirmed or False,
        action_payload=req.action_payload,
        db=db,
    )
    return AssistantQueryResponse(**result)


@router.get("/trip-plan")
def get_trip_plan(
    origin: str = Query(default="Delhi"),
    destination: str = Query(default="Hyderabad"),
    current_fuel_l: float = Query(default=150.0),
    food_budget_inr: float = Query(default=400.0),
    language: str = Query(default="en"),
    current_user: User = Depends(get_current_user),
):
    """
    Generate complete multimodal trip plan (distance, duration, fuel, tolls, food, total cost, coordinates, POIs)
    for the interactive Trip Planner page.
    """
    engine = get_assistant_intent_engine()
    return engine.process_query(
        query=f"Plan trip from {origin} to {destination}",
        user_role=current_user.role,
        user_id=str(current_user.id),
        language=language,
        current_fuel_l=current_fuel_l,
        food_budget_inr=food_budget_inr,
    )


@router.get("/facilities")
def get_facilities(
    category: str = Query(default="restaurants"),
    origin: str = Query(default="Delhi"),
    destination: str = Query(default="Hyderabad"),
    current_user: User = Depends(get_current_user),
):
    """Fetch highway facilities (restaurants, parking, restrooms, fuel bunks, puncture shops)."""
    loc_prov = get_location_provider()
    corridor = loc_prov.get_corridor_data(origin, destination)
    items = corridor.get(category, [])
    return {
        "category": category,
        "count": len(items),
        "facilities": items,
        "data_source": corridor.get("data_source", "database"),
    }
