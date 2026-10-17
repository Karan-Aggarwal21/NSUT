"""Activity result service."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.activity_result import ActivityResult
from app.models.assessment_session import AssessmentSession
from app.utils.exceptions import BadRequestError, ResourceNotFoundError
from app.security.permissions import require_owner_or_admin


def create_result(
    db: Session,
    user_id: uuid.UUID,
    data: dict,
) -> ActivityResult:
    """Store an individual activity result."""
    # Idempotent on client_result_id
    if data.get("client_result_id"):
        existing = (
            db.query(ActivityResult)
            .filter(ActivityResult.client_result_id == data["client_result_id"])
            .first()
        )
        if existing:
            if existing.user_id != user_id:
                raise BadRequestError("Result ID conflict.")
            return existing

    # Validate session ownership
    session = (
        db.query(AssessmentSession)
        .filter(AssessmentSession.id == data["session_id"])
        .first()
    )
    if not session:
        raise ResourceNotFoundError("Session not found.")
    if session.user_id != user_id:
        raise BadRequestError("Session does not belong to this user.")

    result = ActivityResult(
        client_result_id=data.get("client_result_id"),
        session_id=data["session_id"],
        user_id=user_id,
        task_index=data.get("task_index"),
        stimulus=data.get("stimulus"),
        user_response=data.get("user_response"),
        is_correct=data.get("is_correct"),
        response_time_ms=data.get("response_time_ms"),
        score=data.get("score"),
        metadata_json=data.get("metadata_json"),
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result
