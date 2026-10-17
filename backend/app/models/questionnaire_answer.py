"""Individual questionnaire answer model."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class QuestionnaireAnswer(Base):
    __tablename__ = "questionnaire_answers"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    response_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("questionnaire_responses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("questionnaire_questions.id", ondelete="SET NULL"),
        nullable=True,
    )
    question_key: Mapped[str] = mapped_column(String(100), nullable=False)
    answer_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    response: Mapped["QuestionnaireResponse"] = relationship(
        "QuestionnaireResponse", back_populates="answers"
    )

    def __repr__(self) -> str:
        return f"<QuestionnaireAnswer q={self.question_key}>"
