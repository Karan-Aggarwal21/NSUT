"""Questionnaire version model."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class QuestionnaireVersion(Base):
    __tablename__ = "questionnaire_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    questionnaire_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("questionnaires.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_label: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    questionnaire: Mapped["Questionnaire"] = relationship(
        "Questionnaire", back_populates="versions"
    )
    questions: Mapped[list["QuestionnaireQuestion"]] = relationship(
        "QuestionnaireQuestion",
        back_populates="version",
        cascade="all, delete-orphan",
        order_by="QuestionnaireQuestion.order_index",
    )

    def __repr__(self) -> str:
        return f"<QuestionnaireVersion {self.version_label}>"
