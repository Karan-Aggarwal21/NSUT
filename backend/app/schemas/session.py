from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class SessionCreate(BaseModel):
    user_id: Optional[str] = None
    age_group: Optional[str] = None
    preferred_language: str = "en"


class GameAttemptSummary(BaseModel):
    id: str
    game_type: str
    task_version: str
    difficulty: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    metrics: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class SessionResponse(BaseModel):
    id: str
    user_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime
    attempts: List[GameAttemptSummary] = []

    model_config = ConfigDict(from_attributes=True)


class SessionReportResponse(BaseModel):
    session_id: str
    user_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    activities: Dict[str, Any]
    disclaimer: str = (
        "These activities are experimental cognitive games for observational and engagement purposes only. "
        "They are not validated clinical diagnostic instruments and must not be used to diagnose dementia "
        "or Alzheimer's disease."
    )
