"""Game interaction and task orchestration service.

Generates challenges with server-side answer keys, validates incoming client inputs,
runs the scoring engine, and persists detailed results.
"""

from __future__ import annotations

import json
import random
import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy.orm import Session

from app.models.activity_result import ActivityResult
from app.models.assessment_session import AssessmentSession, SessionStatus
from app.models.personalized_item import PersonalizedItem
from app.schemas.cognitive import (
    AttentionResultOut,
    AttentionStartResponse,
    AttentionSubmitRequest,
    GridItem,
    PatternResultOut,
    PatternSubmitRequest,
    PersonalizedGameResultOut,
    PersonalizedGameStartResponse,
    PersonalizedGameSubmitRequest,
    SequenceResultOut,
    SequenceStartResponse,
    SequenceSubmitRequest,
)
from app.security.permissions import require_owner_or_admin
from app.services.scoring_service import (
    score_attention_cancellation,
    score_personalized_recognition,
    score_sequence_memory,
    score_visual_matching,
)
from app.utils.exceptions import BadRequestError, ResourceNotFoundError

# Everyday familiar objects for elderly cognitive sequence recall
FAMILIAR_OBJECTS_POOL = [
    "apple",
    "book",
    "key",
    "clock",
    "umbrella",
    "cup",
    "flower",
    "glasses",
    "lamp",
    "shoe",
    "leaf",
    "bird",
]


# ============================================================================
# Game 1: Object Sequence Memory Service
# ============================================================================

def start_sequence_task(
    db: Session,
    user_id: uuid.UUID,
    user_role: str,
    session_id: uuid.UUID,
    difficulty: int = 1,
    sequence_length: int | None = None,
) -> SequenceStartResponse:
    """Generate a sequence of objects, store the secret key on backend, return viewing sequence."""
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if not session:
        raise ResourceNotFoundError("Assessment session not found.")
    require_owner_or_admin(str(session.user_id), str(user_id), user_role)

    # Determine sequence length based on difficulty (default: 3 items for level 1, up to 6 for level 5)
    length = sequence_length or min(2 + difficulty, 7)
    sample_pool = random.sample(FAMILIAR_OBJECTS_POOL, k=min(len(FAMILIAR_OBJECTS_POOL), length + 4))
    display_sequence = sample_pool[:length]
    # Provide candidate choices containing all target items plus 3-4 distractors, shuffled
    available_choices = list(sample_pool)
    random.shuffle(available_choices)

    task_id = f"seq-task-{uuid.uuid4().hex}"
    task_index = len(session.results) + 1

    # Store stimulus (the secret answer sequence) securely in an ActivityResult placeholder
    result_record = ActivityResult(
        id=uuid.uuid4(),
        client_result_id=task_id,
        session_id=session.id,
        user_id=user_id,
        task_index=task_index,
        stimulus=json.dumps({"target_sequence": display_sequence}),
        score=0.0,
        metadata_json=json.dumps({"status": "pending_submission"}),
    )
    db.add(result_record)
    db.commit()

    # Recommended viewing duration: 1.5 seconds per item + 1 sec buffer
    display_duration_ms = (length * 1500) + 1000

    return SequenceStartResponse(
        task_id=task_id,
        session_id=session.id,
        task_index=task_index,
        display_sequence=display_sequence,
        available_choices=available_choices,
        display_duration_ms=display_duration_ms,
    )


def submit_sequence_task(
    db: Session,
    user_id: uuid.UUID,
    user_role: str,
    payload: SequenceSubmitRequest,
) -> SequenceResultOut:
    """Validate submitted sequence, calculate scoring metrics, and update record."""
    result_record = (
        db.query(ActivityResult)
        .filter(
            ActivityResult.client_result_id == payload.task_id,
            ActivityResult.session_id == payload.session_id,
        )
        .first()
    )
    if not result_record:
        raise ResourceNotFoundError("Sequence task not found or expired.")
    require_owner_or_admin(str(result_record.user_id), str(user_id), user_role)

    # Parse target sequence
    try:
        stimulus_data = json.loads(result_record.stimulus or "{}")
        target_sequence = stimulus_data.get("target_sequence", [])
    except Exception:
        raise BadRequestError("Malformed task stimulus data.")

    # Calculate metrics using scoring engine
    metrics = score_sequence_memory(
        target_sequence=target_sequence,
        submitted_sequence=payload.submitted_sequence,
        response_time_ms=payload.response_time_ms,
        attempts=payload.attempts,
    )

    # Update ActivityResult record
    result_record.user_response = json.dumps(payload.submitted_sequence)
    result_record.is_correct = metrics["exact_sequence_match"]
    result_record.response_time_ms = payload.response_time_ms
    result_record.score = metrics["score"]
    result_record.metadata_json = json.dumps({
        "game_type": "sequence_memory",
        **metrics,
    })

    # Update parent session counters
    session = result_record.session
    session.tasks_attempted = (session.tasks_attempted or 0) + 1
    if metrics["exact_sequence_match"]:
        session.correct_count = (session.correct_count or 0) + 1
    else:
        session.incorrect_count = (session.incorrect_count or 0) + 1

    if payload.response_time_ms:
        duration_sec = payload.response_time_ms / 1000.0
        session.duration_seconds = (session.duration_seconds or 0) + duration_sec

    db.commit()
    db.refresh(result_record)

    return SequenceResultOut(
        task_id=payload.task_id,
        session_id=payload.session_id,
        total_positions=metrics["total_positions"],
        correct_positions=metrics["correct_positions"],
        items_recalled=metrics["items_recalled"],
        position_accuracy=metrics["position_accuracy"],
        recall_accuracy=metrics["recall_accuracy"],
        exact_sequence_match=metrics["exact_sequence_match"],
        score=metrics["score"],
        response_time_seconds=metrics["response_time_seconds"],
        attempts=metrics["attempts"],
    )


# ============================================================================
# Game 2: Circle Identification & Attention Service
# ============================================================================

SHAPES_POOL = ["circle", "square", "triangle", "star"]


def start_attention_task(
    db: Session,
    user_id: uuid.UUID,
    user_role: str,
    session_id: uuid.UUID,
    difficulty: int = 1,
    grid_rows: int = 4,
    grid_cols: int = 4,
) -> AttentionStartResponse:
    """Generate visual cancellation grid containing target circles and distractors."""
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if not session:
        raise ResourceNotFoundError("Assessment session not found.")
    require_owner_or_admin(str(session.user_id), str(user_id), user_role)

    total_cells = grid_rows * grid_cols
    # Target circle count: roughly 25% - 40% of grid items
    target_count = max(3, int(total_cells * (0.25 + 0.03 * difficulty)))
    
    positions = [(r, c) for r in range(grid_rows) for c in range(grid_cols)]
    random.shuffle(positions)

    target_positions = set(positions[:target_count])

    items: list[GridItem] = []
    target_ids: list[str] = []
    all_grid_ids: list[str] = []

    for r in range(grid_rows):
        for c in range(grid_cols):
            item_id = f"item_{r}_{c}"
            all_grid_ids.append(item_id)
            if (r, c) in target_positions:
                shape = "circle"
                target_ids.append(item_id)
            else:
                shape = random.choice(["square", "triangle", "star"])

            items.append(GridItem(id=item_id, shape_type=shape, row=r, col=c))

    task_id = f"att-task-{uuid.uuid4().hex}"
    task_index = len(session.results) + 1

    # Store target IDs and all item IDs securely on backend
    result_record = ActivityResult(
        id=uuid.uuid4(),
        client_result_id=task_id,
        session_id=session.id,
        user_id=user_id,
        task_index=task_index,
        stimulus=json.dumps({
            "target_ids": target_ids,
            "all_grid_ids": all_grid_ids,
        }),
        score=0.0,
        metadata_json=json.dumps({"status": "pending_submission"}),
    )
    db.add(result_record)
    db.commit()

    return AttentionStartResponse(
        task_id=task_id,
        session_id=session.id,
        task_index=task_index,
        target_instruction="Select all circles while ignoring other shapes.",
        items=items,
        time_limit_seconds=30,
    )


def submit_attention_task(
    db: Session,
    user_id: uuid.UUID,
    user_role: str,
    payload: AttentionSubmitRequest,
) -> AttentionResultOut:
    """Validate circle selections, compute signal detection metrics, and persist result."""
    result_record = (
        db.query(ActivityResult)
        .filter(
            ActivityResult.client_result_id == payload.task_id,
            ActivityResult.session_id == payload.session_id,
        )
        .first()
    )
    if not result_record:
        raise ResourceNotFoundError("Attention task not found or expired.")
    require_owner_or_admin(str(result_record.user_id), str(user_id), user_role)

    try:
        stimulus_data = json.loads(result_record.stimulus or "{}")
        target_ids = stimulus_data.get("target_ids", [])
        all_grid_ids = stimulus_data.get("all_grid_ids", [])
    except Exception:
        raise BadRequestError("Malformed task stimulus data.")

    metrics = score_attention_cancellation(
        target_ids=target_ids,
        all_grid_ids=all_grid_ids,
        selected_ids=payload.selected_ids,
        response_time_ms=payload.response_time_ms,
    )

    result_record.user_response = json.dumps(payload.selected_ids)
    # Consider correct if attention score >= 70% and no excessive false alarms
    is_satisfactory = (metrics["attention_score"] >= 70.0 and metrics["distractor_selections"] <= 1)
    result_record.is_correct = is_satisfactory
    result_record.response_time_ms = payload.response_time_ms
    result_record.score = metrics["attention_score"]
    result_record.metadata_json = json.dumps({
        "game_type": "circle_attention",
        **metrics,
    })

    session = result_record.session
    session.tasks_attempted = (session.tasks_attempted or 0) + 1
    if is_satisfactory:
        session.correct_count = (session.correct_count or 0) + 1
    else:
        session.incorrect_count = (session.incorrect_count or 0) + 1

    if payload.response_time_ms:
        session.duration_seconds = (session.duration_seconds or 0) + (payload.response_time_ms / 1000.0)

    db.commit()
    db.refresh(result_record)

    return AttentionResultOut(
        task_id=payload.task_id,
        session_id=payload.session_id,
        total_targets=metrics["total_targets"],
        total_distractors=metrics["total_distractors"],
        correct_selections=metrics["correct_selections"],
        missed_targets=metrics["missed_targets"],
        distractor_selections=metrics["distractor_selections"],
        precision=metrics["precision"],
        recall=metrics["recall"],
        f1_score=metrics["f1_score"],
        score=metrics["score"],
        attention_score=metrics["attention_score"],
        response_time_seconds=metrics["response_time_seconds"],
    )


# ============================================================================
# Game 3: Personalized Memory Task
# ============================================================================

def start_personalized_task(
    db: Session,
    user_id: uuid.UUID,
    user_role: str,
    session_id: uuid.UUID,
    item_id: uuid.UUID | None = None,
) -> PersonalizedGameStartResponse:
    """Generate memory prompt referencing a familiar person, place, or object."""
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if not session:
        raise ResourceNotFoundError("Assessment session not found.")
    require_owner_or_admin(str(session.user_id), str(user_id), user_role)

    query = db.query(PersonalizedItem).filter(
        PersonalizedItem.user_id == user_id,
        PersonalizedItem.is_active == True,  # noqa: E712
    )
    if item_id:
        target_item = query.filter(PersonalizedItem.id == item_id).first()
    else:
        target_item = query.order_by(PersonalizedItem.created_at.desc()).first()

    if not target_item:
        # Fallback default item if none created yet
        target_item = PersonalizedItem(
            id=uuid.uuid4(),
            user_id=user_id,
            category=PersonalizedItem.__table__.columns['category'].type.enum_class.FAMILIAR_PERSON,
            display_name="Family Friend Ravi",
            description="Childhood friend from Shillong",
        )
        db.add(target_item)
        db.commit()

    # Generate 3 reasonable distractors
    distractors_pool = ["Grandson Rohan", "Dr. Sharma", "Neighbor Meena", "Teacher Mukherjee"]
    distractors = [d for d in distractors_pool if d.lower() != target_item.display_name.lower()][:3]
    options = [target_item.display_name] + distractors
    random.shuffle(options)

    task_id = f"pers-task-{uuid.uuid4().hex}"
    task_index = len(session.results) + 1

    prompt = f"Who or what is shown in this memory card?"
    if target_item.description:
        prompt += f" Hint: {target_item.description}"

    result_record = ActivityResult(
        id=uuid.uuid4(),
        client_result_id=task_id,
        session_id=session.id,
        user_id=user_id,
        task_index=task_index,
        stimulus=json.dumps({
            "item_id": str(target_item.id),
            "expected_answer": target_item.display_name,
        }),
        score=0.0,
        metadata_json=json.dumps({"status": "pending_submission"}),
    )
    db.add(result_record)
    db.commit()

    return PersonalizedGameStartResponse(
        task_id=task_id,
        session_id=session.id,
        task_index=task_index,
        item_id=target_item.id,
        category=target_item.category.value,
        prompt=prompt,
        image_reference=target_item.image_reference,
        options=options,
    )


def submit_personalized_task(
    db: Session,
    user_id: uuid.UUID,
    user_role: str,
    payload: PersonalizedGameSubmitRequest,
) -> PersonalizedGameResultOut:
    """Validate personalized memory response."""
    result_record = (
        db.query(ActivityResult)
        .filter(
            ActivityResult.client_result_id == payload.task_id,
            ActivityResult.session_id == payload.session_id,
        )
        .first()
    )
    if not result_record:
        raise ResourceNotFoundError("Personalized task not found.")
    require_owner_or_admin(str(result_record.user_id), str(user_id), user_role)

    stimulus_data = json.loads(result_record.stimulus or "{}")
    expected_answer = stimulus_data.get("expected_answer", "")

    metrics = score_personalized_recognition(
        expected_answer=expected_answer,
        user_answer=payload.selected_answer,
        response_time_ms=payload.response_time_ms,
    )

    result_record.user_response = payload.selected_answer
    result_record.is_correct = metrics["is_correct"]
    result_record.response_time_ms = payload.response_time_ms
    result_record.score = metrics["score"]
    result_record.metadata_json = json.dumps({
        "game_type": "personalized_recognition",
        **metrics,
    })

    session = result_record.session
    session.tasks_attempted = (session.tasks_attempted or 0) + 1
    if metrics["is_correct"]:
        session.correct_count = (session.correct_count or 0) + 1
    else:
        session.incorrect_count = (session.incorrect_count or 0) + 1

    if payload.response_time_ms:
        session.duration_seconds = (session.duration_seconds or 0) + (payload.response_time_ms / 1000.0)

    db.commit()
    db.refresh(result_record)

    return PersonalizedGameResultOut(
        task_id=payload.task_id,
        session_id=payload.session_id,
        is_correct=metrics["is_correct"],
        score=metrics["score"],
        response_time_seconds=metrics["response_time_seconds"],
    )


# ============================================================================
# Game 4: Pattern / Visual Matching Task
# ============================================================================

def submit_pattern_task(
    db: Session,
    user_id: uuid.UUID,
    user_role: str,
    payload: PatternSubmitRequest,
) -> PatternResultOut:
    """Record speeded visual pattern match task."""
    session = db.query(AssessmentSession).filter(AssessmentSession.id == payload.session_id).first()
    if not session:
        raise ResourceNotFoundError("Session not found.")
    require_owner_or_admin(str(session.user_id), str(user_id), user_role)

    metrics = score_visual_matching(
        matched_correctly=payload.matched,
        response_time_ms=payload.response_time_ms,
    )

    result_record = ActivityResult(
        id=uuid.uuid4(),
        client_result_id=payload.task_id,
        session_id=session.id,
        user_id=user_id,
        task_index=payload.task_index,
        stimulus="visual_pattern_match",
        user_response=str(payload.matched),
        is_correct=metrics["is_correct"],
        response_time_ms=payload.response_time_ms,
        score=metrics["score"],
        metadata_json=json.dumps({
            "game_type": "pattern_matching",
            **metrics,
        }),
    )
    db.add(result_record)

    session.tasks_attempted = (session.tasks_attempted or 0) + 1
    if metrics["is_correct"]:
        session.correct_count = (session.correct_count or 0) + 1
    else:
        session.incorrect_count = (session.incorrect_count or 0) + 1

    if payload.response_time_ms:
        session.duration_seconds = (session.duration_seconds or 0) + (payload.response_time_ms / 1000.0)

    db.commit()
    db.refresh(result_record)

    return PatternResultOut(
        task_id=payload.task_id,
        session_id=payload.session_id,
        is_correct=metrics["is_correct"],
        score=metrics["score"],
        response_time_seconds=metrics["response_time_seconds"],
    )
