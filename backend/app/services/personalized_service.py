"""Personalised activity item and session service."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.personalized_item import ItemCategory, PersonalizedItem
from app.models.assessment_session import AssessmentSession, SessionStatus
from app.models.activity_result import ActivityResult
from app.security.permissions import require_owner_or_admin
from app.utils.exceptions import BadRequestError, ResourceNotFoundError


# ---------- Items ----------

def create_item(
    db: Session, user_id: uuid.UUID, data: dict
) -> PersonalizedItem:
    # Validate category
    try:
        cat = ItemCategory(data["category"])
    except ValueError:
        raise BadRequestError(
            f"Invalid category. Must be one of: {[c.value for c in ItemCategory]}"
        )

    item = PersonalizedItem(
        user_id=user_id,
        category=cat,
        display_name=data["display_name"],
        description=data.get("description"),
        image_reference=data.get("image_reference"),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def list_items(
    db: Session, user_id: uuid.UUID, include_inactive: bool = False
) -> list[PersonalizedItem]:
    q = db.query(PersonalizedItem).filter(PersonalizedItem.user_id == user_id)
    if not include_inactive:
        q = q.filter(PersonalizedItem.is_active == True)  # noqa: E712
    return q.order_by(PersonalizedItem.created_at.desc()).all()


def get_item(
    db: Session, item_id: uuid.UUID, user_id: uuid.UUID, user_role: str
) -> PersonalizedItem:
    item = db.query(PersonalizedItem).filter(PersonalizedItem.id == item_id).first()
    if not item:
        raise ResourceNotFoundError("Item not found.")
    require_owner_or_admin(str(item.user_id), str(user_id), user_role)
    return item


def update_item(
    db: Session, item_id: uuid.UUID, user_id: uuid.UUID, user_role: str, data: dict
) -> PersonalizedItem:
    item = get_item(db, item_id, user_id, user_role)
    for key, value in data.items():
        if value is not None and hasattr(item, key):
            if key == "category":
                try:
                    value = ItemCategory(value)
                except ValueError:
                    raise BadRequestError("Invalid category.")
            setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


def delete_item(
    db: Session, item_id: uuid.UUID, user_id: uuid.UUID, user_role: str
) -> None:
    """Soft-delete a personalised item."""
    item = get_item(db, item_id, user_id, user_role)
    item.is_active = False
    db.commit()


# ---------- Personalised sessions ----------

def create_personalized_session(
    db: Session, user_id: uuid.UUID, data: dict
) -> AssessmentSession:
    """Create a session for a personalised activity (reuses assessment_sessions table)."""
    existing = (
        db.query(AssessmentSession)
        .filter(AssessmentSession.client_session_id == data["client_session_id"])
        .first()
    )
    if existing:
        if existing.user_id != user_id:
            raise BadRequestError("Session ID conflict.")
        return existing

    status = SessionStatus.STARTED
    if data.get("completed_at"):
        status = SessionStatus.COMPLETED

    session = AssessmentSession(
        client_session_id=data["client_session_id"],
        user_id=user_id,
        activity_type=f"personalized:{data['activity_type']}",
        activity_version=data.get("activity_version", "1.0"),
        difficulty=data.get("difficulty"),
        status=status,
        started_at=data.get("started_at"),
        completed_at=data.get("completed_at"),
        tasks_attempted=data.get("tasks_attempted"),
        correct_count=data.get("correct_count"),
        incorrect_count=data.get("incorrect_count"),
        duration_seconds=data.get("duration_seconds"),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def create_personalized_result(
    db: Session, user_id: uuid.UUID, data: dict
) -> ActivityResult:
    """Store an individual personalised activity result."""
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
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def get_personalized_history(
    db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 50
) -> list[AssessmentSession]:
    return (
        db.query(AssessmentSession)
        .filter(
            AssessmentSession.user_id == user_id,
            AssessmentSession.activity_type.startswith("personalized:"),
        )
        .order_by(AssessmentSession.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
