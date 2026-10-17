"""Cognitive activity endpoints – sessions, task results, and historical records."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.schemas.cognitive import (
    AttentionResultOut,
    AttentionStartRequest,
    AttentionStartResponse,
    AttentionSubmitRequest,
    HistorySummary,
    PatternResultOut,
    PatternSubmitRequest,
    PersonalizedGameResultOut,
    PersonalizedGameStartRequest,
    PersonalizedGameStartResponse,
    PersonalizedGameSubmitRequest,
    ResultCreate,
    ResultOut,
    SequenceResultOut,
    SequenceStartRequest,
    SequenceStartResponse,
    SequenceSubmitRequest,
    SessionComplete,
    SessionCreate,
    SessionOut,
    SessionReportOut,
)
from app.services import game_service, report_service, result_service, session_service

router = APIRouter(prefix="/cognitive", tags=["Cognitive Activities"])


@router.post(
    "/sessions",
    response_model=SessionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create or register a cognitive activity session",
)
def create_cognitive_session(
    payload: SessionCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Idempotently register or upload a cognitive session executed on the client."""
    return session_service.create_session(
        db=db,
        user_id=current_user.id,
        data=payload.model_dump(),
    )


@router.get(
    "/sessions/{session_id}",
    response_model=SessionOut,
    summary="Get details of a specific cognitive session",
)
def get_cognitive_session(
    session_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Retrieve session details with ownership verification."""
    return session_service.get_session(
        db=db,
        session_id=session_id,
        user_id=current_user.id,
        user_role=current_user.role.value,
    )


@router.post(
    "/sessions/{session_id}/complete",
    response_model=SessionOut,
    summary="Mark an in-progress session as completed",
)
def complete_cognitive_session(
    session_id: uuid.UUID,
    payload: SessionComplete,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Finalize an ongoing cognitive session with completion metrics."""
    return session_service.complete_session(
        db=db,
        session_id=session_id,
        user_id=current_user.id,
        user_role=current_user.role.value,
        data=payload.model_dump(),
    )


@router.post(
    "/results",
    response_model=ResultOut,
    status_code=status.HTTP_201_CREATED,
    summary="Submit individual task result",
)
def submit_cognitive_result(
    payload: ResultCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Ingest granular task-level response data for an assessment session."""
    return result_service.create_result(
        db=db,
        user_id=current_user.id,
        data=payload.model_dump(),
    )


@router.get(
    "/history",
    response_model=list[SessionOut],
    summary="List past cognitive sessions for current user",
)
def list_cognitive_history(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """Retrieve chronological history of cognitive game sessions."""
    return session_service.get_user_sessions(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )


@router.get(
    "/history/summary",
    response_model=HistorySummary,
    summary="Get aggregated statistics across cognitive activity history",
)
def get_cognitive_history_summary(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Aggregated cognitive metrics without generating medical diagnoses."""
    return session_service.get_user_session_summary(db=db, user_id=current_user.id)


# ============================================================================
# Dedicated Game Integration Endpoints
# ============================================================================

# Game 1: Object Sequence Memory
@router.post(
    "/games/sequence/start",
    response_model=SequenceStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start Object Sequence Memory task (generates sequence, stores secret key)",
)
def start_sequence_task(
    payload: SequenceStartRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Returns sequence to display to user; answer key remains securely stored on backend."""
    return game_service.start_sequence_task(
        db=db,
        user_id=current_user.id,
        user_role=current_user.role.value,
        session_id=payload.session_id,
        difficulty=payload.difficulty,
        sequence_length=payload.sequence_length,
    )


@router.post(
    "/games/sequence/submit",
    response_model=SequenceResultOut,
    status_code=status.HTTP_200_OK,
    summary="Submit user recalled sequence and calculate position/accuracy metrics",
)
def submit_sequence_task(
    payload: SequenceSubmitRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Validates user's sequence against secret stimulus, records accuracy, order, and timing."""
    return game_service.submit_sequence_task(
        db=db,
        user_id=current_user.id,
        user_role=current_user.role.value,
        payload=payload,
    )


# Game 2: Circle Identification and Attention
@router.post(
    "/games/attention/start",
    response_model=AttentionStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start Circle Identification cancellation grid task",
)
def start_attention_task(
    payload: AttentionStartRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Generates visual shape grid with hidden target identifiers stored on backend."""
    return game_service.start_attention_task(
        db=db,
        user_id=current_user.id,
        user_role=current_user.role.value,
        session_id=payload.session_id,
        difficulty=payload.difficulty,
        grid_rows=payload.grid_rows,
        grid_cols=payload.grid_cols,
    )


@router.post(
    "/games/attention/submit",
    response_model=AttentionResultOut,
    status_code=status.HTTP_200_OK,
    summary="Submit circle cancellation selections and calculate precision/recall/attention score",
)
def submit_attention_task(
    payload: AttentionSubmitRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Calculates signal detection metrics (hits, misses, false alarms, F1 attention score)."""
    return game_service.submit_attention_task(
        db=db,
        user_id=current_user.id,
        user_role=current_user.role.value,
        payload=payload,
    )


# Game 3: Personalized Memory Recognition
@router.post(
    "/games/personalized/start",
    response_model=PersonalizedGameStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start Personalized Memory Recognition task",
)
def start_personalized_task(
    payload: PersonalizedGameStartRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Generates challenge based on familiar family member, place, or object."""
    return game_service.start_personalized_task(
        db=db,
        user_id=current_user.id,
        user_role=current_user.role.value,
        session_id=payload.session_id,
        item_id=payload.item_id,
    )


@router.post(
    "/games/personalized/submit",
    response_model=PersonalizedGameResultOut,
    status_code=status.HTTP_200_OK,
    summary="Submit answer for Personalized Memory Recognition task",
)
def submit_personalized_task(
    payload: PersonalizedGameSubmitRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Scores response for familiar memory cue."""
    return game_service.submit_personalized_task(
        db=db,
        user_id=current_user.id,
        user_role=current_user.role.value,
        payload=payload,
    )


# Game 4: Pattern / Visual Matching
@router.post(
    "/games/pattern/submit",
    response_model=PatternResultOut,
    status_code=status.HTTP_200_OK,
    summary="Submit result for visual pattern matching",
)
def submit_pattern_task(
    payload: PatternSubmitRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Scores rapid visual pattern match."""
    return game_service.submit_pattern_task(
        db=db,
        user_id=current_user.id,
        user_role=current_user.role.value,
        payload=payload,
    )


# ============================================================================
# Final UI Assessment Report Endpoint
# ============================================================================

@router.get(
    "/sessions/{session_id}/report",
    response_model=SessionReportOut,
    summary="Generate final assessment report for frontend UI consumption",
)
def get_session_report(
    session_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Compiles multi-game session performance, domain breakdown, and questionnaire check-in."""
    return report_service.generate_session_report(
        db=db,
        user_id=current_user.id,
        user_role=current_user.role.value,
        session_id=session_id,
    )

