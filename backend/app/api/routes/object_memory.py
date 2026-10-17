from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.activity import ActivityStartRequest, ActivityStartResponse, ObjectMemorySubmitRequest, ActivitySubmitResponse
from app.services.session_service import SessionService

router = APIRouter()


@router.post("/sessions/{session_id}/object-memory/start", response_model=ActivityStartResponse)
def start_object_memory(
    session_id: str,
    payload: ActivityStartRequest = ActivityStartRequest(),
    db: Session = Depends(get_db)
):
    attempt_info = SessionService.start_game_attempt(
        db,
        session_id=session_id,
        game_type="object_memory",
        difficulty=payload.difficulty or "medium"
    )
    return attempt_info


@router.post("/sessions/{session_id}/object-memory/submit", response_model=ActivitySubmitResponse)
def submit_object_memory_session_path(
    session_id: str,
    attempt_id: str,
    payload: ObjectMemorySubmitRequest,
    db: Session = Depends(get_db)
):
    attempt = SessionService.submit_game_attempt(db, attempt_id, payload.model_dump())
    return {
        "attempt_id": attempt.id,
        "session_id": attempt.session_id,
        "game_type": attempt.game_type,
        "status": attempt.status,
        "completed_at": attempt.completed_at,
        "metrics": attempt.metrics,
        "feedback_message": "Activity completed. Let's move to the next activity."
    }
