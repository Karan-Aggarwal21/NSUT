from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse
from app.services.session_service import SessionService

router = APIRouter()


@router.post("", response_model=UserResponse)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    user = SessionService.get_or_create_user(
        db,
        age_group=payload.age_group,
        preferred_language=payload.preferred_language
    )
    return user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    from app.models.user import User
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user
