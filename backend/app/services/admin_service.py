"""Administration service – operations metrics, audit trail, account management."""

from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.assessment_session import AssessmentSession, SessionStatus
from app.models.questionnaire_response import QuestionnaireResponse
from app.models.audit_log import AuditLog
from app.utils.exceptions import ResourceNotFoundError


def get_system_metrics(db: Session) -> dict:
    """Retrieve operational totals without exposing personal questionnaire content."""
    total_users = db.query(User).filter(User.is_deleted == False).count()  # noqa: E712
    completed_sessions = (
        db.query(AssessmentSession)
        .filter(AssessmentSession.status == SessionStatus.COMPLETED)
        .count()
    )
    total_submissions = db.query(QuestionnaireResponse).count()

    return {
        "total_registered_users": total_users,
        "total_completed_activity_sessions": completed_sessions,
        "total_questionnaire_submissions": total_submissions,
        "system_status": "healthy",
    }


def list_audit_logs(db: Session, limit: int = 100, offset: int = 0) -> Sequence[AuditLog]:
    """Retrieve sensitive administrative audit logs."""
    return (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def set_user_active_status(
    db: Session, admin_id: uuid.UUID, target_user_id: uuid.UUID, is_active: bool
) -> User:
    """Toggle account status with audit record."""
    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        raise ResourceNotFoundError("User not found.")

    target_user.is_active = is_active
    audit = AuditLog(
        actor_id=admin_id,
        action="user_status_changed",
        resource_type="user",
        resource_id=str(target_user.id),
        detail=f"is_active set to {is_active}",
    )
    db.add(audit)
    db.commit()
    db.refresh(target_user)
    return target_user
