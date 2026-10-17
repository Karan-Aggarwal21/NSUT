"""Questionnaire endpoints – definitions, questions, response ingestion, and history."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.schemas.questionnaire import (
    QuestionnaireListItem,
    QuestionnaireOut,
    ResponseCreate,
    ResponseListItem,
    ResponseOut,
)
from app.services import questionnaire_service

router = APIRouter(prefix="/questionnaires", tags=["Questionnaires"])


@router.get(
    "",
    response_model=list[QuestionnaireListItem],
    summary="List available questionnaires",
)
def list_questionnaires(
    db: Annotated[Session, Depends(get_db)],
):
    """Retrieve list of all active questionnaires available for the user."""
    return questionnaire_service.get_all_questionnaires(db)


@router.get(
    "/responses",
    response_model=list[ResponseListItem],
    summary="List previous questionnaire submissions for current user",
)
def list_responses(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """Chronological list of questionnaire submissions by the current user."""
    return questionnaire_service.get_user_responses(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )


@router.get(
    "/history",
    response_model=list[ResponseListItem],
    summary="Alias for questionnaire responses history",
)
def get_questionnaire_history(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """Retrieve questionnaire completion history."""
    return questionnaire_service.get_user_responses(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )


@router.get(
    "/responses/{response_id}",
    response_model=ResponseOut,
    summary="Get details of a specific questionnaire submission including answers",
)
def get_response_detail(
    response_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Retrieve full answer details for an authorized response record."""
    return questionnaire_service.get_response_detail(
        db=db,
        response_id=response_id,
        user_id=current_user.id,
        user_role=current_user.role.value,
    )


@router.get(
    "/{questionnaire_id}",
    response_model=QuestionnaireOut,
    summary="Get full questionnaire definition with questions, version, and options",
)
def get_questionnaire(
    questionnaire_id: str,
    db: Annotated[Session, Depends(get_db)],
):
    """Retrieve questionnaire structure by ID or slug (e.g. 'memory-wellbeing-v1')."""
    return questionnaire_service.get_questionnaire_by_id_or_slug(db, questionnaire_id)


@router.post(
    "/{questionnaire_id}/responses",
    response_model=ResponseOut,
    status_code=status.HTTP_201_CREATED,
    summary="Submit answers for a questionnaire",
)
def submit_response(
    questionnaire_id: str,
    payload: ResponseCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Validate and store answers for the specified questionnaire version."""
    return questionnaire_service.submit_questionnaire_response(
        db=db,
        user_id=current_user.id,
        questionnaire_identifier=questionnaire_id,
        data=payload.model_dump(),
    )
