"""Profile schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ProfileOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    display_name: str | None = None
    age: int | None = None
    gender: str | None = None
    preferred_language: str | None = None
    region: str | None = None
    bio: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(None, max_length=200)
    age: int | None = Field(None, ge=0, le=150)
    gender: str | None = Field(None, max_length=50)
    preferred_language: str | None = Field(None, max_length=50)
    region: str | None = Field(None, max_length=100)
    bio: str | None = None
