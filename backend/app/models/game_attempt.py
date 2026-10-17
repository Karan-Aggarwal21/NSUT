import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base


class GameAttempt(Base):
    __tablename__ = "game_attempts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    session_id = Column(String(36), ForeignKey("assessment_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    game_type = Column(String(50), nullable=False, index=True)  # object_memory, circle_search, calculation_recall, shape_recognition
    task_version = Column(String(20), default="v1.0", nullable=False)
    difficulty = Column(String(20), default="medium", nullable=False)  # easy, medium, advanced
    task_data = Column(JSON, nullable=True)  # Server-side task definition (e.g., answer keys, generated items)
    response_data = Column(JSON, nullable=True)  # User submitted responses
    metrics = Column(JSON, nullable=True)  # Computed authoritative score and task metrics
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="in_progress", nullable=False)  # in_progress, completed, abandoned

    session = relationship("AssessmentSession", back_populates="attempts")
