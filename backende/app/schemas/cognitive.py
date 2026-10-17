"""Cognitive activity schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator


class SessionCreate(BaseModel):
    client_session_id: str = Field(..., max_length=255)
    activity_type: str = Field(..., max_length=100)
    activity_version: str = Field("1.0", max_length=20)
    difficulty: int | None = Field(None, ge=1, le=20)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    tasks_attempted: int | None = Field(None, ge=0)
    correct_count: int | None = Field(None, ge=0)
    incorrect_count: int | None = Field(None, ge=0)
    duration_seconds: float | None = Field(None, ge=0)
    task_response_data: str | None = None

    @model_validator(mode="after")
    def _check_counts(self):
        if (
            self.tasks_attempted is not None
            and self.correct_count is not None
            and self.incorrect_count is not None
        ):
            if self.correct_count + self.incorrect_count > self.tasks_attempted:
                raise ValueError(
                    "correct_count + incorrect_count cannot exceed tasks_attempted"
                )
        if self.started_at and self.completed_at and self.completed_at < self.started_at:
            raise ValueError("completed_at must be after started_at")
        return self


class SessionOut(BaseModel):
    id: uuid.UUID
    client_session_id: str
    user_id: uuid.UUID
    activity_type: str
    activity_version: str
    difficulty: int | None
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    tasks_attempted: int | None
    correct_count: int | None
    incorrect_count: int | None
    duration_seconds: float | None
    sync_status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SessionComplete(BaseModel):
    completed_at: datetime | None = None
    tasks_attempted: int | None = Field(None, ge=0)
    correct_count: int | None = Field(None, ge=0)
    incorrect_count: int | None = Field(None, ge=0)
    duration_seconds: float | None = Field(None, ge=0)


class ResultCreate(BaseModel):
    client_result_id: str | None = Field(None, max_length=255)
    session_id: uuid.UUID
    task_index: int | None = None
    stimulus: str | None = None
    user_response: str | None = None
    is_correct: bool | None = None
    response_time_ms: int | None = Field(None, ge=0)
    score: float | None = None
    metadata_json: str | None = None


class ResultOut(BaseModel):
    id: uuid.UUID
    client_result_id: str | None
    session_id: uuid.UUID
    user_id: uuid.UUID
    task_index: int | None
    stimulus: str | None
    user_response: str | None
    is_correct: bool | None
    response_time_ms: int | None
    score: float | None
    created_at: datetime

    model_config = {"from_attributes": True}


class HistorySummary(BaseModel):
    total_sessions: int
    total_completed: int
    total_tasks_attempted: int
    total_correct: int
    total_incorrect: int
    average_duration_seconds: float | None


# ============================================================================
# Game 1: Object Sequence Memory Schemas
# ============================================================================

class SequenceStartRequest(BaseModel):
    session_id: uuid.UUID
    difficulty: int = Field(1, ge=1, le=5)
    sequence_length: int | None = Field(None, ge=3, le=8)


class SequenceStartResponse(BaseModel):
    task_id: str
    session_id: uuid.UUID
    task_index: int
    display_sequence: list[str] = Field(
        ...,
        description="Objects to display in sequence during observation phase (e.g. ['apple', 'book', 'key'])",
    )
    available_choices: list[str] = Field(
        ...,
        description="Candidate objects for the user to select from during recall phase",
    )
    display_duration_ms: int = Field(
        ...,
        description="Recommended viewing duration based on difficulty",
    )


class SequenceSubmitRequest(BaseModel):
    task_id: str
    session_id: uuid.UUID
    task_index: int = 1
    submitted_sequence: list[str] = Field(
        ..., description="Ordered list of objects chosen by the user"
    )
    response_time_ms: int | None = Field(None, ge=0)
    attempts: int = Field(1, ge=1)


class SequenceResultOut(BaseModel):
    task_id: str
    session_id: uuid.UUID
    total_positions: int
    correct_positions: int
    items_recalled: int
    position_accuracy: float
    recall_accuracy: float
    exact_sequence_match: bool
    score: float
    response_time_seconds: float | None
    attempts: int


# ============================================================================
# Game 2: Circle Identification & Attention Schemas
# ============================================================================

class GridItem(BaseModel):
    id: str
    shape_type: str  # "circle", "square", "triangle", "star"
    row: int
    col: int


class AttentionStartRequest(BaseModel):
    session_id: uuid.UUID
    difficulty: int = Field(1, ge=1, le=5)
    grid_rows: int = Field(4, ge=3, le=8)
    grid_cols: int = Field(4, ge=3, le=8)


class AttentionStartResponse(BaseModel):
    task_id: str
    session_id: uuid.UUID
    task_index: int
    target_instruction: str = "Select all circles while ignoring other shapes."
    items: list[GridItem] = Field(
        ..., description="Visual grid items displayed to user (answer key hidden)"
    )
    time_limit_seconds: int = 30


class AttentionSubmitRequest(BaseModel):
    task_id: str
    session_id: uuid.UUID
    task_index: int = 2
    selected_ids: list[str] = Field(
        ..., description="List of item IDs selected by the user"
    )
    response_time_ms: int | None = Field(None, ge=0)


class AttentionResultOut(BaseModel):
    task_id: str
    session_id: uuid.UUID
    total_targets: int
    total_distractors: int
    correct_selections: int
    missed_targets: int
    distractor_selections: int
    precision: float
    recall: float
    f1_score: float
    score: float
    attention_score: float
    response_time_seconds: float | None


# ============================================================================
# Game 3: Personalized Memory Schemas
# ============================================================================

class PersonalizedGameStartRequest(BaseModel):
    session_id: uuid.UUID
    item_id: uuid.UUID | None = None


class PersonalizedGameStartResponse(BaseModel):
    task_id: str
    session_id: uuid.UUID
    task_index: int
    item_id: uuid.UUID
    category: str
    prompt: str
    image_reference: str | None = None
    options: list[str] = Field(
        ..., description="Candidate names/answers including 1 correct and 3 distractors"
    )


class PersonalizedGameSubmitRequest(BaseModel):
    task_id: str
    session_id: uuid.UUID
    task_index: int = 3
    item_id: uuid.UUID
    selected_answer: str
    response_time_ms: int | None = Field(None, ge=0)


class PersonalizedGameResultOut(BaseModel):
    task_id: str
    session_id: uuid.UUID
    is_correct: bool
    score: float
    response_time_seconds: float | None


# ============================================================================
# Game 4: Pattern / Visual Matching Schemas
# ============================================================================

class PatternSubmitRequest(BaseModel):
    task_id: str
    session_id: uuid.UUID
    task_index: int = 4
    matched: bool
    response_time_ms: int | None = Field(None, ge=0)


class PatternResultOut(BaseModel):
    task_id: str
    session_id: uuid.UUID
    is_correct: bool
    score: float
    response_time_seconds: float | None


# ============================================================================
# Final UI Assessment Report Schemas
# ============================================================================

class DomainScore(BaseModel):
    domain: str  # e.g., "Working Memory", "Selective Attention", "Personalized Recall", "Processing Speed"
    score: float  # 0 to 100
    performance_level: str  # "High Engagement", "Good Performance", "Mild Difficulty", "Needs Practice"
    tasks_completed: int


class GameSummary(BaseModel):
    game_name: str
    game_type: str
    score: float
    accuracy: float
    duration_seconds: float | None
    metrics: dict[str, Any] = {}


class QuestionnaireSummary(BaseModel):
    completed: bool
    submission_id: uuid.UUID | None = None
    submitted_at: datetime | None = None
    emotional_wellbeing: str | None = None
    level_of_concern: str | None = None
    answers_count: int = 0


class SessionReportOut(BaseModel):
    session_id: uuid.UUID
    user_id: uuid.UUID
    activity_type: str
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: float | None = None
    overall_score: float
    performance_rating: str  # e.g., "Active Engagement", "Steady Focus", "Encouraging Participation"
    domains: list[DomainScore] = []
    game_results: list[GameSummary] = []
    questionnaire_summary: QuestionnaireSummary | None = None
    clinical_disclaimer: str = (
        "Cognivia is an engagement and cognitive assistance platform. "
        "This report reflects recreational and exercise performance only and does not "
        "constitute a medical diagnosis, clinical evaluation, or dementia risk assessment."
    )

