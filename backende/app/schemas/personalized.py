"""Personalised activity schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PersonalizedItemCreate(BaseModel):
    category: str = Field(..., max_length=100)
    display_name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    image_reference: str | None = Field(None, max_length=500)


class PersonalizedItemUpdate(BaseModel):
    category: str | None = Field(None, max_length=100)
    display_name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    image_reference: str | None = Field(None, max_length=500)
    is_active: bool | None = None


class PersonalizedItemOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    category: str
    display_name: str
    description: str | None
    image_reference: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PersonalizedSessionCreate(BaseModel):
    client_session_id: str = Field(..., max_length=255)
    activity_type: str = Field(..., max_length=100)
    activity_version: str = Field("1.0", max_length=20)
    item_ids: list[uuid.UUID] = Field(default_factory=list)
    difficulty: int | None = Field(None, ge=1, le=20)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    tasks_attempted: int | None = Field(None, ge=0)
    correct_count: int | None = Field(None, ge=0)
    incorrect_count: int | None = Field(None, ge=0)
    duration_seconds: float | None = Field(None, ge=0)


class PersonalizedResultCreate(BaseModel):
    client_result_id: str | None = Field(None, max_length=255)
    session_id: uuid.UUID
    item_id: uuid.UUID | None = None
    task_index: int | None = None
    stimulus: str | None = None
    user_response: str | None = None
    is_correct: bool | None = None
    response_time_ms: int | None = Field(None, ge=0)
    score: float | None = None
