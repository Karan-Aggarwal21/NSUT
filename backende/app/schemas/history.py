"""Unified history schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class HistoryItem(BaseModel):
    record_type: str
    record_id: uuid.UUID
    activity_type: str | None = None
    questionnaire_version: str | None = None
    created_at: datetime


class HistoryResponse(BaseModel):
    items: list[HistoryItem]
    next_cursor: str | None = None
    total: int | None = None


class HistorySummaryResponse(BaseModel):
    total_cognitive_sessions: int
    total_personalized_sessions: int
    total_questionnaire_responses: int
    date_range_start: datetime | None = None
    date_range_end: datetime | None = None
