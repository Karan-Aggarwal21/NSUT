from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.session import SessionCreate, SessionResponse, SessionReportResponse
from app.services.session_service import SessionService

router = APIRouter()


@router.post("", response_model=SessionResponse)
def create_session(payload: SessionCreate, db: Session = Depends(get_db)):
    session = SessionService.create_session(
        db,
        user_id=payload.user_id,
        age_group=payload.age_group,
        preferred_language=payload.preferred_language
    )
    return session


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, db: Session = Depends(get_db)):
    session = SessionService.get_session(db, session_id)
    return session


@router.post("/{session_id}/complete", response_model=SessionResponse)
def complete_session(session_id: str, db: Session = Depends(get_db)):
    session = SessionService.complete_session(db, session_id)
    return session


@router.get("/{session_id}/report", response_model=SessionReportResponse)
def get_session_report(session_id: str, db: Session = Depends(get_db)):
    report = SessionService.get_session_report(db, session_id)
    return report
