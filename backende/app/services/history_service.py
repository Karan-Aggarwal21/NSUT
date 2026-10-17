"""Combined activity history service."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.assessment_session import AssessmentSession
from app.models.questionnaire_response import QuestionnaireResponse
from app.models.questionnaire_version import QuestionnaireVersion


def get_combined_history(
    db: Session,
    user_id: uuid.UUID,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    activity_category: str | None = None,  # "cognitive", "personalized", "questionnaire"
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Retrieve chronological unified history of cognitive activities, personalised activities, and questionnaires."""
    items = []

    # 1. Cognitive Assessment Sessions (non-personalized)
    if activity_category in (None, "cognitive", "all"):
        q_cog = db.query(AssessmentSession).filter(
            AssessmentSession.user_id == user_id,
            ~AssessmentSession.activity_type.startswith("personalized:"),
        )
        if start_date:
            q_cog = q_cog.filter(AssessmentSession.created_at >= start_date)
        if end_date:
            q_cog = q_cog.filter(AssessmentSession.created_at <= end_date)

        for s in q_cog.all():
            items.append({
                "record_type": "cognitive_activity",
                "record_id": s.id,
                "activity_type": s.activity_type,
                "questionnaire_version": None,
                "created_at": s.created_at,
            })

    # 2. Personalized Sessions
    if activity_category in (None, "personalized", "all"):
        q_pers = db.query(AssessmentSession).filter(
            AssessmentSession.user_id == user_id,
            AssessmentSession.activity_type.startswith("personalized:"),
        )
        if start_date:
            q_pers = q_pers.filter(AssessmentSession.created_at >= start_date)
        if end_date:
            q_pers = q_pers.filter(AssessmentSession.created_at <= end_date)

        for s in q_pers.all():
            items.append({
                "record_type": "personalized_activity",
                "record_id": s.id,
                "activity_type": s.activity_type.replace("personalized:", "", 1),
                "questionnaire_version": None,
                "created_at": s.created_at,
            })

    # 3. Questionnaire Responses
    if activity_category in (None, "questionnaire", "all"):
        q_quest = (
            db.query(QuestionnaireResponse, QuestionnaireVersion.version_label)
            .join(QuestionnaireVersion, QuestionnaireResponse.version_id == QuestionnaireVersion.id)
            .filter(QuestionnaireResponse.user_id == user_id)
        )
        if start_date:
            q_quest = q_quest.filter(QuestionnaireResponse.submitted_at >= start_date)
        if end_date:
            q_quest = q_quest.filter(QuestionnaireResponse.submitted_at <= end_date)

        for resp, v_label in q_quest.all():
            items.append({
                "record_type": "questionnaire",
                "record_id": resp.id,
                "activity_type": None,
                "questionnaire_version": v_label,
                "created_at": resp.submitted_at,
            })

    # Sort descending by date
    items.sort(key=lambda x: x["created_at"], reverse=True)

    total_records = len(items)
    paginated_items = items[offset : offset + limit]
    next_cursor = str(offset + limit) if (offset + limit) < total_records else None

    return {
        "items": paginated_items,
        "next_cursor": next_cursor,
        "total": total_records,
    }


def get_history_summary(
    db: Session,
    user_id: uuid.UUID,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict:
    """Aggregate counts for unified history overview."""
    q_cog = db.query(AssessmentSession).filter(
        AssessmentSession.user_id == user_id,
        ~AssessmentSession.activity_type.startswith("personalized:"),
    )
    q_pers = db.query(AssessmentSession).filter(
        AssessmentSession.user_id == user_id,
        AssessmentSession.activity_type.startswith("personalized:"),
    )
    q_quest = db.query(QuestionnaireResponse).filter(
        QuestionnaireResponse.user_id == user_id
    )

    if start_date:
        q_cog = q_cog.filter(AssessmentSession.created_at >= start_date)
        q_pers = q_pers.filter(AssessmentSession.created_at >= start_date)
        q_quest = q_quest.filter(QuestionnaireResponse.submitted_at >= start_date)
    if end_date:
        q_cog = q_cog.filter(AssessmentSession.created_at <= end_date)
        q_pers = q_pers.filter(AssessmentSession.created_at <= end_date)
        q_quest = q_quest.filter(QuestionnaireResponse.submitted_at <= end_date)

    return {
        "total_cognitive_sessions": q_cog.count(),
        "total_personalized_sessions": q_pers.count(),
        "total_questionnaire_responses": q_quest.count(),
        "date_range_start": start_date,
        "date_range_end": end_date,
    }
