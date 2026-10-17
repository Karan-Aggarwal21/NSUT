from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.activity import ActivityStartRequest, ActivityStartResponse
from app.services.session_service import SessionService

router = APIRouter()


@router.post("/sessions/{session_id}/shape-recognition/start", response_model=ActivityStartResponse)
def start_shape_recognition(
    session_id: str,
    payload: ActivityStartRequest = ActivityStartRequest(),
    db: Session = Depends(get_db)
):
    attempt_info = SessionService.start_game_attempt(
        db,
        session_id=session_id,
        game_type="shape_recognition",
        difficulty=payload.difficulty or "medium"
    )
    return attempt_info
