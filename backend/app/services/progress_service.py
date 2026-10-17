from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.assessment_session import AssessmentSession
from app.models.game_attempt import GameAttempt


class ProgressService:
    @staticmethod
    def get_user_progress(db: Session, user_id: str) -> Dict[str, Any]:
        sessions = db.query(AssessmentSession).filter(
            AssessmentSession.user_id == user_id
        ).order_by(AssessmentSession.started_at.desc()).all()

        history = []
        for s in sessions:
            attempts = db.query(GameAttempt).filter(
                GameAttempt.session_id == s.id,
                GameAttempt.status == "completed"
            ).all()

            attempt_metrics = {}
            for a in attempts:
                attempt_metrics[a.game_type] = {
                    "attempt_id": a.id,
                    "difficulty": a.difficulty,
                    "task_version": a.task_version,
                    "metrics": a.metrics,
                }

            history.append({
                "session_id": s.id,
                "status": s.status,
                "started_at": s.started_at.isoformat() if s.started_at else None,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
                "activities_completed": len(attempts),
                "activities": attempt_metrics,
            })

        return {
            "user_id": user_id,
            "total_sessions": len(sessions),
            "sessions": history,
            "disclaimer": (
                "These cognitive metrics reflect engagement and performance on experimental tasks. "
                "They are not clinical indicators or diagnoses of dementia or Alzheimer's disease."
            )
        }
