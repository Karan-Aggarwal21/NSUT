"""Cognitive activity session service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.assessment_session import AssessmentSession, SessionStatus
from app.utils.exceptions import (
    BadRequestError,
    DuplicateResourceError,
    ResourceNotFoundError,
)
from app.security.permissions import require_owner_or_admin


def create_session(
    db: Session,
    user_id: uuid.UUID,
    data: dict,
) -> AssessmentSession:
    """Create a new cognitive assessment session (idempotent on client_session_id)."""
    existing = (
        db.query(AssessmentSession)
        .filter(AssessmentSession.client_session_id == data["client_session_id"])
        .first()
    )
    if existing:
        if existing.user_id != user_id:
            raise BadRequestError("Session ID conflict.")
        return existing  # idempotent

    status = SessionStatus.STARTED
    if data.get("completed_at"):
        status = SessionStatus.COMPLETED

    session = AssessmentSession(
        client_session_id=data["client_session_id"],
        user_id=user_id,
        activity_type=data["activity_type"],
        activity_version=data.get("activity_version", "1.0"),
        difficulty=data.get("difficulty"),
        status=status,
        started_at=data.get("started_at"),
        completed_at=data.get("completed_at"),
        tasks_attempted=data.get("tasks_attempted"),
        correct_count=data.get("correct_count"),
        incorrect_count=data.get("incorrect_count"),
        duration_seconds=data.get("duration_seconds"),
        task_response_data=data.get("task_response_data"),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(
    db: Session, session_id: uuid.UUID, user_id: uuid.UUID, user_role: str
) -> AssessmentSession:
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if not session:
        raise ResourceNotFoundError("Session not found.")
    require_owner_or_admin(str(session.user_id), str(user_id), user_role)
    return session


def complete_session(
    db: Session,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    user_role: str,
    data: dict,
) -> AssessmentSession:
    session = get_session(db, session_id, user_id, user_role)
    if session.status == SessionStatus.COMPLETED:
        raise BadRequestError("Session already completed.")

    session.status = SessionStatus.COMPLETED
    session.completed_at = data.get("completed_at") or datetime.now(timezone.utc)
    if data.get("tasks_attempted") is not None:
        session.tasks_attempted = data["tasks_attempted"]
    if data.get("correct_count") is not None:
        session.correct_count = data["correct_count"]
    if data.get("incorrect_count") is not None:
        session.incorrect_count = data["incorrect_count"]
    if data.get("duration_seconds") is not None:
        session.duration_seconds = data["duration_seconds"]

    db.commit()
    db.refresh(session)
    return session


def get_user_sessions(
    db: Session,
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
) -> list[AssessmentSession]:
    return (
        db.query(AssessmentSession)
        .filter(AssessmentSession.user_id == user_id)
        .order_by(AssessmentSession.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_user_session_summary(db: Session, user_id: uuid.UUID) -> dict:
    from sqlalchemy import func

    sessions = (
        db.query(AssessmentSession)
        .filter(AssessmentSession.user_id == user_id)
    )
    total = sessions.count()
    completed = sessions.filter(
        AssessmentSession.status == SessionStatus.COMPLETED
    ).count()
    agg = (
        db.query(
            func.coalesce(func.sum(AssessmentSession.tasks_attempted), 0),
            func.coalesce(func.sum(AssessmentSession.correct_count), 0),
            func.coalesce(func.sum(AssessmentSession.incorrect_count), 0),
            func.avg(AssessmentSession.duration_seconds),
        )
        .filter(AssessmentSession.user_id == user_id)
        .first()
    )
    return {
        "total_sessions": total,
        "total_completed": completed,
        "total_tasks_attempted": int(agg[0]) if agg else 0,
        "total_correct": int(agg[1]) if agg else 0,
        "total_incorrect": int(agg[2]) if agg else 0,
        "average_duration_seconds": float(agg[3]) if agg and agg[3] else None,
    }
