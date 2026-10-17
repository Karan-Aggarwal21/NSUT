"""Questionnaire service – questionnaire definitions, versions, and response submissions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy.orm import Session, joinedload

from app.models.questionnaire import Questionnaire
from app.models.questionnaire_version import QuestionnaireVersion
from app.models.questionnaire_question import QuestionnaireQuestion, QuestionnaireOption
from app.models.questionnaire_response import QuestionnaireResponse
from app.models.questionnaire_answer import QuestionnaireAnswer
from app.utils.exceptions import BadRequestError, ResourceNotFoundError
from app.security.permissions import require_owner_or_admin


# Standard default 7 well-being / memory check-in questions
DEFAULT_QUESTIONS_DATA = [
    {
        "question_key": "recent_memory_difficulties",
        "question_text": "How often have you experienced recent memory difficulties?",
        "order_index": 1,
        "is_required": False,
        "answer_type": "single_choice",
        "options": [
            ("never", "Never", 1),
            ("sometimes", "Sometimes", 2),
            ("often", "Often", 3),
            ("prefer_not_to_answer", "Prefer not to answer", 4),
        ],
    },
    {
        "question_key": "misplacing_familiar_objects",
        "question_text": "Do you find difficulty remembering where familiar objects were placed?",
        "order_index": 2,
        "is_required": False,
        "answer_type": "single_choice",
        "options": [
            ("never", "Never", 1),
            ("sometimes", "Sometimes", 2),
            ("often", "Often", 3),
            ("prefer_not_to_answer", "Prefer not to answer", 4),
        ],
    },
    {
        "question_key": "difficulty_concentrating",
        "question_text": "Do you find it difficult to concentrate on tasks or conversations?",
        "order_index": 3,
        "is_required": False,
        "answer_type": "single_choice",
        "options": [
            ("never", "Never", 1),
            ("sometimes", "Sometimes", 2),
            ("often", "Often", 3),
            ("prefer_not_to_answer", "Prefer not to answer", 4),
        ],
    },
    {
        "question_key": "daily_routines_difficulty",
        "question_text": "Do you have difficulty remembering familiar daily routines?",
        "order_index": 4,
        "is_required": False,
        "answer_type": "single_choice",
        "options": [
            ("never", "Never", 1),
            ("sometimes", "Sometimes", 2),
            ("often", "Often", 3),
            ("prefer_not_to_answer", "Prefer not to answer", 4),
        ],
    },
    {
        "question_key": "noticed_changes_thinking",
        "question_text": "Have you or someone close to you noticed changes in your memory or thinking?",
        "order_index": 5,
        "is_required": False,
        "answer_type": "single_choice",
        "options": [
            ("never", "Never", 1),
            ("sometimes", "Sometimes", 2),
            ("often", "Often", 3),
            ("prefer_not_to_answer", "Prefer not to answer", 4),
        ],
    },
    {
        "question_key": "recent_emotional_wellbeing",
        "question_text": "How would you rate your recent emotional well-being and mood?",
        "order_index": 6,
        "is_required": False,
        "answer_type": "single_choice",
        "options": [
            ("good", "Good", 1),
            ("fair", "Fair", 2),
            ("low", "Low / Feeling down", 3),
            ("prefer_not_to_answer", "Prefer not to answer", 4),
        ],
    },
    {
        "question_key": "level_of_concern",
        "question_text": "What is your level of concern about your memory or thinking?",
        "order_index": 7,
        "is_required": False,
        "answer_type": "single_choice",
        "options": [
            ("not_concerned", "Not concerned", 1),
            ("mildly_concerned", "Mildly concerned", 2),
            ("very_concerned", "Very concerned", 3),
            ("prefer_not_to_answer", "Prefer not to answer", 4),
        ],
    },
]


def seed_default_questionnaire(db: Session) -> Questionnaire:
    """Ensure the standard 7-question well-being check-in questionnaire exists."""
    q = db.query(Questionnaire).filter(Questionnaire.slug == "memory-wellbeing-v1").first()
    if q:
        return q

    q = Questionnaire(
        slug="memory-wellbeing-v1",
        title="Self-Reported Memory and Well-Being Check-in",
        description="Informal self-reported questionnaire assessing recent memory concerns and emotional well-being. Not a diagnostic tool.",
        is_active=True,
    )
    db.add(q)
    db.flush()

    v = QuestionnaireVersion(
        questionnaire_id=q.id,
        version_label="1.0",
        is_active=True,
    )
    db.add(v)
    db.flush()

    for item in DEFAULT_QUESTIONS_DATA:
        question = QuestionnaireQuestion(
            version_id=v.id,
            question_key=item["question_key"],
            question_text=item["question_text"],
            order_index=item["order_index"],
            is_required=item["is_required"],
            answer_type=item["answer_type"],
        )
        db.add(question)
        db.flush()

        for val, label, ord_idx in item["options"]:
            opt = QuestionnaireOption(
                question_id=question.id,
                option_value=val,
                option_label=label,
                order_index=ord_idx,
            )
            db.add(opt)

    db.commit()
    db.refresh(q)
    return q


def get_all_questionnaires(db: Session, active_only: bool = True) -> Sequence[Questionnaire]:
    query = db.query(Questionnaire)
    if active_only:
        query = query.filter(Questionnaire.is_active == True)  # noqa: E712
    return query.order_by(Questionnaire.created_at.desc()).all()


def get_questionnaire_by_id_or_slug(db: Session, identifier: str) -> Questionnaire:
    query = db.query(Questionnaire).options(
        joinedload(Questionnaire.versions).joinedload(QuestionnaireVersion.questions).joinedload(QuestionnaireQuestion.options)
    )
    try:
        qid = uuid.UUID(identifier)
        q = query.filter(Questionnaire.id == qid).first()
    except ValueError:
        q = query.filter(Questionnaire.slug == identifier).first()

    if not q:
        raise ResourceNotFoundError("Questionnaire not found.")
    return q


def submit_questionnaire_response(
    db: Session,
    user_id: uuid.UUID,
    questionnaire_identifier: str,
    data: dict,
) -> QuestionnaireResponse:
    """Submit questionnaire answers with strict version and option validation."""
    questionnaire = get_questionnaire_by_id_or_slug(db, questionnaire_identifier)
    version_label = data["questionnaire_version"]

    version = (
        db.query(QuestionnaireVersion)
        .options(
            joinedload(QuestionnaireVersion.questions).joinedload(QuestionnaireQuestion.options)
        )
        .filter(
            QuestionnaireVersion.questionnaire_id == questionnaire.id,
            QuestionnaireVersion.version_label == version_label,
        )
        .first()
    )
    if not version:
        raise BadRequestError(f"Questionnaire version '{version_label}' does not exist.")

    # Idempotent check via client_submission_id
    client_sub_id = data.get("client_submission_id")
    if client_sub_id:
        existing = (
            db.query(QuestionnaireResponse)
            .options(joinedload(QuestionnaireResponse.answers))
            .filter(QuestionnaireResponse.client_submission_id == client_sub_id)
            .first()
        )
        if existing:
            if existing.user_id != user_id:
                raise BadRequestError("Submission ID conflict.")
            return existing

    # Map question keys to Question object and valid option values
    valid_questions = {q.question_key: q for q in version.questions}
    valid_options_per_question = {
        q.question_key: {opt.option_value for opt in q.options}
        for q in version.questions
    }

    # Validate answers
    answers_to_create = []
    received_keys = set()
    for ans in data.get("answers", []):
        q_key = ans["question_id"]
        val = ans.get("answer")

        if q_key not in valid_questions:
            raise BadRequestError(f"Question '{q_key}' is not part of questionnaire version {version_label}.")

        # If answer is supplied, validate against allowed options for single_choice
        q_obj = valid_questions[q_key]
        if val is not None and q_obj.answer_type == "single_choice":
            allowed_opts = valid_options_per_question.get(q_key, set())
            if allowed_opts and val not in allowed_opts:
                raise BadRequestError(f"Invalid option '{val}' for question '{q_key}'.")

        received_keys.add(q_key)
        answers_to_create.append((q_obj.id, q_key, val))

    # Check required questions
    for q_key, q_obj in valid_questions.items():
        if q_obj.is_required and (q_key not in received_keys or next((a[2] for a in answers_to_create if a[1] == q_key), None) is None):
            raise BadRequestError(f"Question '{q_key}' is required.")

    # Create QuestionnaireResponse
    resp = QuestionnaireResponse(
        client_submission_id=client_sub_id,
        user_id=user_id,
        questionnaire_id=questionnaire.id,
        version_id=version.id,
        completion_status="completed",
        completed_at=data.get("completed_at") or datetime.now(timezone.utc),
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(resp)
    db.flush()

    for q_id, q_key, ans_val in answers_to_create:
        ans_record = QuestionnaireAnswer(
            response_id=resp.id,
            question_id=q_id,
            question_key=q_key,
            answer_value=ans_val,
        )
        db.add(ans_record)

    db.commit()
    db.refresh(resp)
    return resp


def get_user_responses(
    db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 50
) -> Sequence[QuestionnaireResponse]:
    return (
        db.query(QuestionnaireResponse)
        .filter(QuestionnaireResponse.user_id == user_id)
        .order_by(QuestionnaireResponse.submitted_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_response_detail(
    db: Session, response_id: uuid.UUID, user_id: uuid.UUID, user_role: str
) -> QuestionnaireResponse:
    resp = (
        db.query(QuestionnaireResponse)
        .options(joinedload(QuestionnaireResponse.answers))
        .filter(QuestionnaireResponse.id == response_id)
        .first()
    )
    if not resp:
        raise ResourceNotFoundError("Questionnaire response not found.")
    require_owner_or_admin(str(resp.user_id), str(user_id), user_role)
    return resp
