from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field


class ActivityStartRequest(BaseModel):
    difficulty: Optional[str] = Field("medium", pattern="^(easy|medium|advanced)$")


class ActivityStartResponse(BaseModel):
    attempt_id: str
    session_id: str
    game_type: str
    task_version: str
    difficulty: str
    task_data: Dict[str, Any]  # Safe task data exposed to client (without answer keys)


# ---------------- Activity 1: Object Memory ----------------
class ObjectMemorySubmitRequest(BaseModel):
    selected_sequence: List[str]  # List of object IDs in the order user placed them
    response_time_ms: Optional[int] = None


# ---------------- Activity 2: Circle Search ----------------
class CircleSearchSubmitRequest(BaseModel):
    selected_ids: List[str]  # IDs of selected grid shapes
    completion_time_ms: Optional[int] = None


# ---------------- Activity 3: Calculation & Delayed Word Recall ----------------
class CalculationAnswer(BaseModel):
    question_id: str
    selected_answer: int


class CalculationRecallSubmitRequest(BaseModel):
    calculation_answers: List[CalculationAnswer]
    recalled_words: List[str]
    calculation_time_ms: Optional[int] = None
    word_recall_delay_seconds: Optional[float] = None
    total_time_ms: Optional[int] = None


# ---------------- Activity 4: Shape Recognition ----------------
class ShapeAnswer(BaseModel):
    question_id: str
    selected_option_id: str


class ShapeRecognitionSubmitRequest(BaseModel):
    answers: List[ShapeAnswer]
    completion_time_ms: Optional[int] = None


# ---------------- General Submit Response ----------------
class ActivitySubmitResponse(BaseModel):
    attempt_id: str
    session_id: str
    game_type: str
    status: str
    completed_at: datetime
    metrics: Dict[str, Any]
    feedback_message: str = "Activity completed. Let's move to the next activity."
