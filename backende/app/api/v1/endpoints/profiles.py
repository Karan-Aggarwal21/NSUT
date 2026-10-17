"""Profile endpoints – elderly user profile settings and preferences."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.schemas.profile import ProfileOut, ProfileUpdate
from app.services import user_service

router = APIRouter(prefix="/profiles", tags=["Profiles"])


@router.get(
    "/me",
    response_model=ProfileOut,
    summary="Get current user's profile",
)
def get_my_profile(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Retrieve profile metadata (age, display name, language, region)."""
    return user_service.get_profile(db, current_user.id)


@router.patch(
    "/me",
    response_model=ProfileOut,
    summary="Update current user's profile",
)
def update_my_profile(
    payload: ProfileUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Update profile metadata such as preferred language, region, or display name."""
    return user_service.update_profile(
        db=db,
        user_id=current_user.id,
        update_data=payload.model_dump(exclude_unset=True),
    )
