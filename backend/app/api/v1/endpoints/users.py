"""User endpoints – current user inspection, update, and account deletion."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.user import UserOut, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get current user details",
)
def get_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Retrieve the currently authenticated user's profile account information."""
    return current_user


@router.patch(
    "/me",
    response_model=UserOut,
    summary="Update current user account details",
)
def update_me(
    payload: UserUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Update username or email for current user."""
    updated = user_service.update_user(
        db=db,
        user=current_user,
        update_data=payload.model_dump(exclude_unset=True),
    )
    return updated


@router.delete(
    "/me",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete (deactivate) current user account",
)
def delete_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Securely soft-delete user account and revoke all authentication sessions."""
    user_service.delete_user(db=db, user=current_user)
    return MessageResponse(message="Account successfully deactivated.")
