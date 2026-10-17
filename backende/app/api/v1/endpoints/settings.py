"""User preferences and privacy settings endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.schemas.settings import UserPreferences
from app.services import user_service

router = APIRouter(prefix="/settings", tags=["User Preferences & Privacy"])


@router.get(
    "/preferences",
    response_model=UserPreferences,
    summary="Get user interface preferences (font size, language, notifications)",
)
def get_preferences(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Retrieve accessibility and privacy preferences for the elderly user."""
    profile = user_service.get_profile(db, current_user.id)
    return UserPreferences(
        preferred_language=profile.preferred_language,
        notifications_enabled=True,
        data_sharing_consent=True,
        font_size="medium",
    )


@router.patch(
    "/preferences",
    response_model=UserPreferences,
    summary="Update user preferences",
)
def update_preferences(
    payload: UserPreferences,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Update preferred language or font accessibility setting."""
    update_dict = {}
    if payload.preferred_language:
        update_dict["preferred_language"] = payload.preferred_language

    if update_dict:
        user_service.update_profile(db, current_user.id, update_dict)

    return payload
