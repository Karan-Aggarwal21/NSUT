"""Questionnaire question model (includes options as JSON or separate table)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class QuestionnaireQuestion(Base):
    __tablename__ = "questionnaire_questions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("questionnaire_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_key: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    answer_type: Mapped[str] = mapped_column(
        String(50), default="single_choice", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    version: Mapped["QuestionnaireVersion"] = relationship(
        "QuestionnaireVersion", back_populates="questions"
    )
    options: Mapped[list["QuestionnaireOption"]] = relationship(
        "QuestionnaireOption",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="QuestionnaireOption.order_index",
    )

    def __repr__(self) -> str:
        return f"<QuestionnaireQuestion {self.question_key}>"


class QuestionnaireOption(Base):
    """Valid answer options for a single-choice or multi-choice question."""

    __tablename__ = "questionnaire_options"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("questionnaire_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    option_value: Mapped[str] = mapped_column(String(100), nullable=False)
    option_label: Mapped[str] = mapped_column(String(300), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    question: Mapped["QuestionnaireQuestion"] = relationship(
        "QuestionnaireQuestion", back_populates="options"
    )

    def __repr__(self) -> str:
        return f"<QuestionnaireOption {self.option_value}>"
