"""
Phase 7 — What-If Simulation API Router.

Provides sandbox simulation endpoints to evaluate disruptions, demand surges,
and operational contingencies without modifying production data.
"""
import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.schemas.analytics import WhatIfScenarioResult, WhatIfSimulateRequest
from app.services.what_if.simulation_engine import (
    SCENARIO_TITLES,
    simulate_what_if_scenario,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/what-if", tags=["What-If Simulation"])


@router.get("/scenarios", summary="List supported What-If scenario types")
def list_supported_scenarios(
    current_user: User = Depends(require_roles("admin", "operator", "fleet_manager")),
):
    """Return available scenario types with descriptive labels."""
    return [
        {"type": key, "title": title, "category": "incident" if key in ["breakdown", "tyre_puncture", "low_fuel"] else "operational"}
        for key, title in SCENARIO_TITLES.items()
    ]


@router.post(
    "/simulate",
    response_model=WhatIfScenarioResult,
    summary="Run sandbox What-If simulation (Before vs After)",
)
def run_what_if_simulation(
    payload: WhatIfSimulateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "operator", "fleet_manager")),
):
    """
    Execute a non-destructive What-If simulation comparing baseline vs post-disruption metrics
    and return an explainable recovery/optimization action plan.
    """
    try:
        result = simulate_what_if_scenario(
            scenario_type=payload.scenario_type,
            db=db,
            vehicle_id=payload.vehicle_id,
            route_id=payload.route_id,
            extra_delay_min=payload.extra_delay_min,
            detour_km=payload.detour_km,
            additional_weight_kg=payload.additional_weight_kg,
            notes=payload.notes,
        )
        return result
    except Exception as e:
        logger.error("What-If simulation failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation error: {str(e)}",
        )
