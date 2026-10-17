import pytest
from app.services.scoring_service import ScoringService
from fastapi import HTTPException


def test_shape_recognition_scoring():
    server_data = {
        "answer_key": {
            "shape_q_1": "opt_correct_1",
            "shape_q_2": "opt_correct_2",
            "shape_q_3": "opt_correct_3",
            "shape_q_4": "opt_correct_4",
            "shape_q_5": "opt_correct_5",
        },
        "difficulty": "medium",
    }

    user_answers = [
        {"question_id": "shape_q_1", "selected_option_id": "opt_correct_1"},
        {"question_id": "shape_q_2", "selected_option_id": "opt_correct_2"},
        {"question_id": "shape_q_3", "selected_option_id": "opt_correct_3"},
        {"question_id": "shape_q_4", "selected_option_id": "opt_correct_4"},
        {"question_id": "shape_q_5", "selected_option_id": "opt_wrong"},
    ]

    metrics = ScoringService.score_shape_recognition(server_data, user_answers, completion_time_ms=18000)

    assert metrics["correct_answers"] == 4
    assert metrics["incorrect_answers"] == 1
    assert metrics["total_questions"] == 5
    assert metrics["shape_accuracy"] == 80.0
    assert metrics["completion_time_ms"] == 18000
    assert metrics["difficulty"] == "medium"
    assert metrics["task_version"] == "v1.0"


def test_shape_recognition_invalid_question():
    server_data = {"answer_key": {"shape_q_1": "opt_1"}}
    with pytest.raises(HTTPException):
        ScoringService.score_shape_recognition(server_data, [{"question_id": "unknown_q", "selected_option_id": "opt_1"}])
