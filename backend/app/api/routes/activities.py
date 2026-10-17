from typing import Dict, Any
from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.activity import ActivitySubmitResponse
from app.services.session_service import SessionService

router = APIRouter()


@router.post("/{attempt_id}/submit", response_model=ActivitySubmitResponse)
def submit_activity(
    attempt_id: str,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Authoritative answer submission for all 4 activities.
    Retrieves the attempt and correct answer key from DB, scores deterministically,
    and returns validated metrics.
    """
    attempt = SessionService.submit_game_attempt(db, attempt_id, payload)
    return {
        "attempt_id": attempt.id,
        "session_id": attempt.session_id,
        "game_type": attempt.game_type,
        "status": attempt.status,
        "completed_at": attempt.completed_at,
        "metrics": attempt.metrics,
        "feedback_message": "Activity completed. Let's move to the next activity."
    }
