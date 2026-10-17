"""Administrative endpoints – platform metrics, audit logs, and account moderation."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user
from app.database import get_db
from app.models.user import User, UserRole
from app.security.permissions import require_admin
from app.services import admin_service

router = APIRouter(prefix="/admin", tags=["Administration"])


@router.get(
    "/metrics",
    summary="Get high-level platform usage and health metrics",
)
def get_metrics(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Retrieve non-sensitive platform statistics (total users, completed sessions, etc.)."""
    require_admin(current_user.role.value)
    return admin_service.get_system_metrics(db)


@router.get(
    "/audit-logs",
    summary="View system audit trail for security-sensitive operations",
)
def get_audit_logs(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List administrative audit entries."""
    require_admin(current_user.role.value)
    return admin_service.list_audit_logs(db, limit=limit, offset=offset)


@router.post(
    "/users/{user_id}/status",
    summary="Activate or deactivate a user account",
)
def set_user_status(
    user_id: uuid.UUID,
    is_active: bool,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Admin endpoint to suspend or reactivate an account."""
    require_admin(current_user.role.value)
    updated = admin_service.set_user_active_status(
        db=db,
        admin_id=current_user.id,
        target_user_id=user_id,
        is_active=is_active,
    )
    return {"user_id": str(updated.id), "is_active": updated.is_active}
