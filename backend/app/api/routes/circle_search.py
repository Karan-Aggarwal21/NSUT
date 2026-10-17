from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.activity import ActivityStartRequest, ActivityStartResponse, CircleSearchSubmitRequest, ActivitySubmitResponse
from app.services.session_service import SessionService

router = APIRouter()


@router.post("/sessions/{session_id}/circle-search/start", response_model=ActivityStartResponse)
def start_circle_search(
    session_id: str,
    payload: ActivityStartRequest = ActivityStartRequest(),
    db: Session = Depends(get_db)
):
    attempt_info = SessionService.start_game_attempt(
        db,
        session_id=session_id,
        game_type="circle_search",
        difficulty=payload.difficulty or "medium"
    )
    return attempt_info
