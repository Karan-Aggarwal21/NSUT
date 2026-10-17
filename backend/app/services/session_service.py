import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.user import User
from app.models.assessment_session import AssessmentSession
from app.models.game_attempt import GameAttempt
from app.services.task_generator import TaskGenerator
from app.services.scoring_service import ScoringService


class SessionService:
    @staticmethod
    def get_or_create_user(db: Session, user_id: Optional[str] = None, age_group: Optional[str] = None, preferred_language: str = "en") -> User:
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                return user
        new_user = User(
            id=user_id or str(uuid.uuid4()),
            age_group=age_group,
            preferred_language=preferred_language
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def create_session(db: Session, user_id: Optional[str] = None, age_group: Optional[str] = None, preferred_language: str = "en") -> AssessmentSession:
        user = SessionService.get_or_create_user(db, user_id, age_group, preferred_language)
        session = AssessmentSession(
            id=str(uuid.uuid4()),
            user_id=user.id,
            status="in_progress",
            started_at=datetime.now(timezone.utc)
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_session(db: Session, session_id: str) -> AssessmentSession:
        session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Assessment session not found.")
        return session

    @staticmethod
    def complete_session(db: Session, session_id: str) -> AssessmentSession:
        session = SessionService.get_session(db, session_id)
        session.status = "completed"
        session.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def start_game_attempt(db: Session, session_id: str, game_type: str, difficulty: str = "medium") -> Dict[str, Any]:
        session = SessionService.get_session(db, session_id)
        if session.status == "completed":
            raise HTTPException(status_code=400, detail="Cannot start activity on a completed session.")

        # Generate task
        if game_type == "object_memory":
            gen = TaskGenerator.generate_object_memory_task(difficulty)
        elif game_type == "circle_search":
            gen = TaskGenerator.generate_circle_search_task(difficulty)
        elif game_type == "calculation_recall":
            gen = TaskGenerator.generate_calculation_recall_task(difficulty)
        elif game_type == "shape_recognition":
            gen = TaskGenerator.generate_shape_recognition_task(difficulty)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown game type '{game_type}'.")

        attempt = GameAttempt(
            id=str(uuid.uuid4()),
            session_id=session.id,
            game_type=game_type,
            task_version="v1.0",
            difficulty=difficulty,
            task_data=gen["server_data"],
            status="in_progress",
            started_at=datetime.now(timezone.utc)
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)

        return {
            "attempt_id": attempt.id,
            "session_id": session.id,
            "game_type": game_type,
            "task_version": attempt.task_version,
            "difficulty": difficulty,
            "task_data": gen["client_data"],
        }

    @staticmethod
    def submit_game_attempt(db: Session, attempt_id: str, response_payload: Dict[str, Any]) -> GameAttempt:
        attempt = db.query(GameAttempt).filter(GameAttempt.id == attempt_id).first()
        if not attempt:
            raise HTTPException(status_code=404, detail="Game attempt not found.")

        if attempt.status == "completed":
            raise HTTPException(status_code=400, detail="This activity attempt has already been submitted.")

        # Authoritative scoring on the backend
        if attempt.game_type == "object_memory":
            metrics = ScoringService.score_object_memory(
                server_data=attempt.task_data,
                selected_sequence=response_payload.get("selected_sequence", []),
                response_time_ms=response_payload.get("response_time_ms")
            )
        elif attempt.game_type == "circle_search":
            metrics = ScoringService.score_circle_search(
                server_data=attempt.task_data,
                selected_ids=response_payload.get("selected_ids", []),
                completion_time_ms=response_payload.get("completion_time_ms")
            )
        elif attempt.game_type == "calculation_recall":
            metrics = ScoringService.score_calculation_recall(
                server_data=attempt.task_data,
                calculation_answers=response_payload.get("calculation_answers", []),
                recalled_words=response_payload.get("recalled_words", []),
                calculation_time_ms=response_payload.get("calculation_time_ms"),
                word_recall_delay_seconds=response_payload.get("word_recall_delay_seconds"),
                total_time_ms=response_payload.get("total_time_ms")
            )
        elif attempt.game_type == "shape_recognition":
            metrics = ScoringService.score_shape_recognition(
                server_data=attempt.task_data,
                answers=response_payload.get("answers", []),
                completion_time_ms=response_payload.get("completion_time_ms")
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported game type for scoring.")

        attempt.response_data = response_payload
        attempt.metrics = metrics
        attempt.status = "completed"
        attempt.completed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(attempt)
        return attempt

    @staticmethod
    def get_session_report(db: Session, session_id: str) -> Dict[str, Any]:
        session = SessionService.get_session(db, session_id)
        attempts = db.query(GameAttempt).filter(
            GameAttempt.session_id == session_id,
            GameAttempt.status == "completed"
        ).all()

        activities_data = {}
        for att in attempts:
            activities_data[att.game_type] = {
                "attempt_id": att.id,
                "task_version": att.task_version,
                "difficulty": att.difficulty,
                "completed_at": att.completed_at.isoformat() if att.completed_at else None,
                "metrics": att.metrics,
            }

        return {
            "session_id": session.id,
            "user_id": session.user_id,
            "status": session.status,
            "started_at": session.started_at,
            "completed_at": session.completed_at,
            "activities": activities_data,
        }
