from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.progress_service import ProgressService

router = APIRouter()


@router.get("/users/{user_id}/progress")
def get_user_progress(user_id: str, db: Session = Depends(get_db)):
    """
    Returns the user's historical assessment results.
    """
    return ProgressService.get_user_progress(db, user_id)
