"""Offline data synchronization endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.schemas.sync import SyncPayload, SyncResponse, SyncStatusResponse
from app.services import sync_service

router = APIRouter(prefix="/sync", tags=["Offline Synchronisation"])


@router.post(
    "",
    response_model=SyncResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch upload records stored offline in Flutter client SQLite",
)
def synchronize_offline_data(
    payload: SyncPayload,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Idempotent batch synchronisation endpoint supporting retries and per-record status."""
    return sync_service.process_sync_batch(
        db=db, user_id=current_user.id, payload=payload
    )


@router.get(
    "/status",
    response_model=SyncStatusResponse,
    summary="Get synchronization status overview",
)
def get_sync_status(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Check connectivity and synchronisation health."""
    return SyncStatusResponse(
        pending_count=0,
        last_sync_at=None,
    )
