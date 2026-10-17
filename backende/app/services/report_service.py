"""Assessment session final report generator for the frontend UI.

Combines game performance metrics across cognitive domains with self-reported well-being
questionnaire responses into a structured final report ready for frontend display.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.activity_result import ActivityResult
from app.models.assessment_session import AssessmentSession
from app.models.questionnaire_response import QuestionnaireResponse
from app.models.questionnaire_answer import QuestionnaireAnswer
from app.schemas.cognitive import (
    DomainScore,
    GameSummary,
    QuestionnaireSummary,
    SessionReportOut,
)
from app.security.permissions import require_owner_or_admin
from app.utils.exceptions import ResourceNotFoundError


def _get_performance_level(score: float) -> str:
    if score >= 85.0:
        return "High Engagement & Strong Accuracy"
    elif score >= 70.0:
        return "Steady Focus & Consistent Performance"
    elif score >= 50.0:
        return "Active Participation & Good Effort"
    else:
        return "Gentle Practice & Warm-up"


def generate_session_report(
    db: Session,
    user_id: uuid.UUID,
    user_role: str,
    session_id: uuid.UUID,
) -> SessionReportOut:
    """Generate comprehensive assessment report aggregating game metrics and questionnaire responses."""
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if not session:
        raise ResourceNotFoundError("Assessment session not found.")
    require_owner_or_admin(str(session.user_id), str(user_id), user_role)

    # 1. Inspect all task results
    results: list[ActivityResult] = session.results
    game_summaries: list[GameSummary] = []

    domain_buckets: dict[str, list[float]] = {
        "Working Memory": [],
        "Selective Attention": [],
        "Personalized Recall": [],
        "Processing Speed": [],
    }

    total_score_sum = 0.0
    task_count = 0

    for res in results:
        meta: dict[str, Any] = {}
        if res.metadata_json:
            try:
                meta = json.loads(res.metadata_json)
            except Exception:
                meta = {}

        game_type = meta.get("game_type", "generic_task")
        score = res.score if res.score is not None else 0.0
        total_score_sum += score
        task_count += 1

        duration_sec = (res.response_time_ms / 1000.0) if res.response_time_ms else None

        if game_type == "sequence_memory":
            domain_buckets["Working Memory"].append(score)
            game_summaries.append(
                GameSummary(
                    game_name="Object Sequence Memory",
                    game_type="sequence_memory",
                    score=score,
                    accuracy=meta.get("position_accuracy", 1.0 if res.is_correct else 0.0),
                    duration_seconds=duration_sec,
                    metrics={
                        "correct_positions": meta.get("correct_positions", 0),
                        "total_positions": meta.get("total_positions", 0),
                        "exact_match": meta.get("exact_sequence_match", False),
                        "items_recalled": meta.get("items_recalled", 0),
                    },
                )
            )
        elif game_type == "circle_attention":
            domain_buckets["Selective Attention"].append(score)
            game_summaries.append(
                GameSummary(
                    game_name="Circle Identification & Attention",
                    game_type="circle_attention",
                    score=score,
                    accuracy=meta.get("precision", 1.0 if res.is_correct else 0.0),
                    duration_seconds=duration_sec,
                    metrics={
                        "correct_selections": meta.get("correct_selections", 0),
                        "total_targets": meta.get("total_targets", 0),
                        "missed_targets": meta.get("missed_targets", 0),
                        "distractor_selections": meta.get("distractor_selections", 0),
                        "f1_score": meta.get("f1_score", 0.0),
                    },
                )
            )
        elif game_type == "personalized_recognition":
            domain_buckets["Personalized Recall"].append(score)
            game_summaries.append(
                GameSummary(
                    game_name="Personalized Memory Recognition",
                    game_type="personalized_recognition",
                    score=score,
                    accuracy=1.0 if res.is_correct else 0.0,
                    duration_seconds=duration_sec,
                    metrics={"is_correct": res.is_correct},
                )
            )
        else:
            domain_buckets["Processing Speed"].append(score)
            game_summaries.append(
                GameSummary(
                    game_name="Visual Matching & Recognition",
                    game_type="pattern_matching",
                    score=score,
                    accuracy=1.0 if res.is_correct else 0.0,
                    duration_seconds=duration_sec,
                    metrics={"is_correct": res.is_correct},
                )
            )

    # 2. Build Domain Breakdown
    domains: list[DomainScore] = []
    for domain_name, scores in domain_buckets.items():
        if scores:
            avg_score = round(sum(scores) / len(scores), 1)
            domains.append(
                DomainScore(
                    domain=domain_name,
                    score=avg_score,
                    performance_level=_get_performance_level(avg_score),
                    tasks_completed=len(scores),
                )
            )

    overall_score = round(total_score_sum / task_count, 1) if task_count > 0 else 0.0

    # Overall encouragement rating
    if overall_score >= 80.0:
        performance_rating = "Excellent Engagement & Sharp Focus"
    elif overall_score >= 60.0:
        performance_rating = "Steady Focus & Active Participation"
    else:
        performance_rating = "Encouraging Progress & Dedicated Practice"

    # 3. Integrate Questionnaire Response
    q_resp = (
        db.query(QuestionnaireResponse)
        .filter(QuestionnaireResponse.user_id == user_id)
        .order_by(QuestionnaireResponse.submitted_at.desc())
        .first()
    )

    q_summary: QuestionnaireSummary | None = None
    if q_resp:
        answers_map = {ans.question_key: ans.answer_value for ans in q_resp.answers}
        q_summary = QuestionnaireSummary(
            completed=True,
            submission_id=q_resp.id,
            submitted_at=q_resp.submitted_at,
            emotional_wellbeing=answers_map.get("recent_emotional_wellbeing"),
            level_of_concern=answers_map.get("level_of_concern"),
            answers_count=len(q_resp.answers),
        )
    else:
        q_summary = QuestionnaireSummary(
            completed=False,
            answers_count=0,
        )

    return SessionReportOut(
        session_id=session.id,
        user_id=session.user_id,
        activity_type=session.activity_type,
        status=session.status.value,
        started_at=session.started_at,
        completed_at=session.completed_at,
        duration_seconds=session.duration_seconds,
        overall_score=overall_score,
        performance_rating=performance_rating,
        domains=domains,
        game_results=game_summaries,
        questionnaire_summary=q_summary,
    )
