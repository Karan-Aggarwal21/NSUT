"""Sync schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.cognitive import SessionCreate, ResultCreate
from app.schemas.personalized import (
    PersonalizedSessionCreate,
    PersonalizedResultCreate,
)
from app.schemas.questionnaire import ResponseCreate


class SyncPayload(BaseModel):
    """Batch of offline records to synchronise."""
    cognitive_sessions: list[SessionCreate] = Field(default_factory=list)
    cognitive_results: list[ResultCreate] = Field(default_factory=list)
    personalized_sessions: list[PersonalizedSessionCreate] = Field(default_factory=list)
    personalized_results: list[PersonalizedResultCreate] = Field(default_factory=list)
    questionnaire_responses: list[ResponseCreate] = Field(default_factory=list)
    # Each ResponseCreate here also needs a questionnaire_id
    questionnaire_ids: list[str] = Field(
        default_factory=list,
        description="Parallel list of questionnaire slugs for each questionnaire response",
    )


class SyncRecordStatus(BaseModel):
    record_type: str
    client_id: str | None = None
    status: str  # "accepted" | "duplicate" | "error"
    server_id: str | None = None
    error: str | None = None


class SyncResponse(BaseModel):
    results: list[SyncRecordStatus]
    accepted_count: int
    duplicate_count: int
    error_count: int


class SyncStatusResponse(BaseModel):
    pending_count: int
    last_sync_at: str | None = None
