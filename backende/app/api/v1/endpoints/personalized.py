"""Personalised activity endpoints – items, photo/name references, sessions, and history."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.cognitive import ResultOut, SessionOut
from app.schemas.personalized import (
    PersonalizedItemCreate,
    PersonalizedItemOut,
    PersonalizedItemUpdate,
    PersonalizedResultCreate,
    PersonalizedSessionCreate,
)
from app.services import personalized_service

router = APIRouter(prefix="/personalized", tags=["Personalised Activities"])


# ---------- Personalised Items ----------

@router.post(
    "/items",
    response_model=PersonalizedItemOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a personalised memory item (person, place, object, event)",
)
def create_personalized_item(
    payload: PersonalizedItemCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Register a familiar person, place, or object for memory engagement activities."""
    return personalized_service.create_item(
        db=db, user_id=current_user.id, data=payload.model_dump()
    )


@router.get(
    "/items",
    response_model=list[PersonalizedItemOut],
    summary="List active personalised memory items for current user",
)
def list_personalized_items(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    include_inactive: bool = Query(False),
):
    """Retrieve all personalised memory cues associated with the account."""
    return personalized_service.list_items(
        db=db, user_id=current_user.id, include_inactive=include_inactive
    )


@router.get(
    "/items/{item_id}",
    response_model=PersonalizedItemOut,
    summary="Get details of a specific personalised item",
)
def get_personalized_item(
    item_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Retrieve a single item with ownership verification."""
    return personalized_service.get_item(
        db=db,
        item_id=item_id,
        user_id=current_user.id,
        user_role=current_user.role.value,
    )


@router.patch(
    "/items/{item_id}",
    response_model=PersonalizedItemOut,
    summary="Update a personalised memory item",
)
def update_personalized_item(
    item_id: uuid.UUID,
    payload: PersonalizedItemUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Modify name, description, category, or active status of a personalised memory item."""
    return personalized_service.update_item(
        db=db,
        item_id=item_id,
        user_id=current_user.id,
        user_role=current_user.role.value,
        data=payload.model_dump(exclude_unset=True),
    )


@router.delete(
    "/items/{item_id}",
    response_model=MessageResponse,
    summary="Delete (deactivate) a personalised memory item",
)
def delete_personalized_item(
    item_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Soft-delete a personalised memory item."""
    personalized_service.delete_item(
        db=db,
        item_id=item_id,
        user_id=current_user.id,
        user_role=current_user.role.value,
    )
    return MessageResponse(message="Item deactivated.")


# ---------- Personalised Sessions and Results ----------

@router.post(
    "/sessions",
    response_model=SessionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Record a session of a personalised memory activity",
)
def create_personalized_session(
    payload: PersonalizedSessionCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Create or upload a personalized activity session record."""
    return personalized_service.create_personalized_session(
        db=db, user_id=current_user.id, data=payload.model_dump()
    )


@router.post(
    "/results",
    response_model=ResultOut,
    status_code=status.HTTP_201_CREATED,
    summary="Submit result for a personalized activity task",
)
def submit_personalized_result(
    payload: PersonalizedResultCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Store granular result referencing familiar memory stimulus."""
    return personalized_service.create_personalized_result(
        db=db, user_id=current_user.id, data=payload.model_dump()
    )


@router.get(
    "/history",
    response_model=list[SessionOut],
    summary="List past personalised activity sessions",
)
def list_personalized_history(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """Retrieve history of completed personalised memory activities."""
    return personalized_service.get_personalized_history(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
