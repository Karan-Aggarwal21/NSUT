"""Questionnaire schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ----- Read schemas -----

class OptionOut(BaseModel):
    id: uuid.UUID
    option_value: str
    option_label: str
    order_index: int

    model_config = {"from_attributes": True}


class QuestionOut(BaseModel):
    id: uuid.UUID
    question_key: str
    question_text: str
    order_index: int
    is_required: bool
    answer_type: str
    options: list[OptionOut] = []

    model_config = {"from_attributes": True}


class VersionOut(BaseModel):
    id: uuid.UUID
    version_label: str
    is_active: bool
    created_at: datetime
    questions: list[QuestionOut] = []

    model_config = {"from_attributes": True}


class QuestionnaireOut(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    description: str | None
    is_active: bool
    created_at: datetime
    versions: list[VersionOut] = []

    model_config = {"from_attributes": True}


class QuestionnaireListItem(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    description: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ----- Submission schemas -----

class AnswerCreate(BaseModel):
    question_id: str = Field(..., description="Stable question_key")
    answer: str | None = None


class ResponseCreate(BaseModel):
    client_submission_id: str | None = Field(None, max_length=255)
    questionnaire_version: str = Field(..., max_length=20)
    completed_at: datetime | None = None
    answers: list[AnswerCreate] = Field(default_factory=list)


class AnswerOut(BaseModel):
    id: uuid.UUID
    question_key: str
    answer_value: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ResponseOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    questionnaire_id: uuid.UUID
    version_id: uuid.UUID
    completion_status: str
    completed_at: datetime | None
    submitted_at: datetime
    created_at: datetime
    answers: list[AnswerOut] = []

    model_config = {"from_attributes": True}


class ResponseListItem(BaseModel):
    id: uuid.UUID
    questionnaire_id: uuid.UUID
    version_id: uuid.UUID
    completion_status: str
    completed_at: datetime | None
    submitted_at: datetime

    model_config = {"from_attributes": True}
