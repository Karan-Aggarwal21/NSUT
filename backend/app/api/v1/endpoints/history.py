"""Combined activity history endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.schemas.history import HistoryResponse, HistorySummaryResponse
from app.services import history_service

router = APIRouter(prefix="/history", tags=["Combined Activity History"])


@router.get(
    "",
    response_model=HistoryResponse,
    summary="Get unified activity history (cognitive, personalized, questionnaire)",
)
def get_history(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    activity_category: str | None = Query(
        None, description="Filter: 'cognitive', 'personalized', 'questionnaire', or null for all"
    ),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Retrieve chronological unified history of all user activities without mixing meanings."""
    return history_service.get_combined_history(
        db=db,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        activity_category=activity_category,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/summary",
    response_model=HistorySummaryResponse,
    summary="Get aggregated counts across all activity categories",
)
def get_history_summary(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
):
    """Summary of total completions per category for overview dashboards."""
    return history_service.get_history_summary(
        db=db,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
    )
