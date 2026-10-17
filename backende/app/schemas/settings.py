"""Settings / preferences schemas."""

from __future__ import annotations

from pydantic import BaseModel


class UserPreferences(BaseModel):
    preferred_language: str | None = None
    notifications_enabled: bool | None = None
    data_sharing_consent: bool | None = None
    font_size: str | None = None  # "small", "medium", "large"
