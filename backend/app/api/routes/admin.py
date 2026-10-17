from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.assessment_session import AssessmentSession
from app.models.game_attempt import GameAttempt

router = APIRouter()


@router.get("/stats")
def get_admin_stats(db: Session = Depends(get_db)):
    """
    Internal dev stats endpoint - does not expose sensitive patient info.
    """
    user_count = db.query(User).count()
    session_count = db.query(AssessmentSession).count()
    attempt_count = db.query(GameAttempt).count()
    completed_sessions = db.query(AssessmentSession).filter(AssessmentSession.status == "completed").count()

    recent_sessions = db.query(AssessmentSession).order_by(AssessmentSession.created_at.desc()).limit(10).all()
    recent = []
    for s in recent_sessions:
        recent.append({
            "id": s.id,
            "status": s.status,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            "attempts_count": len(s.attempts)
        })

    return {
        "user_count": user_count,
        "session_count": session_count,
        "completed_sessions": completed_sessions,
        "attempt_count": attempt_count,
        "recent_sessions": recent,
    }
