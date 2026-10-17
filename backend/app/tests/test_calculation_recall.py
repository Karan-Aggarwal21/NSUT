import pytest
from app.services.scoring_service import ScoringService
from fastapi import HTTPException


def test_calculation_and_word_recall_scoring():
    server_data = {
        "calculation_answer_key": {"q1": 3, "q2": 5, "q3": 6, "q4": 4, "q5": 7, "q6": 2},
        "target_words": ["Apple", "House", "River"],
        "recall_word_choices": ["Apple", "House", "River", "Key", "Chair", "Flower"],
        "difficulty": "medium",
    }

    # Calculation: 5 correct out of 6
    user_calc_answers = [
        {"question_id": "q1", "selected_answer": 3},
        {"question_id": "q2", "selected_answer": 5},
        {"question_id": "q3", "selected_answer": 6},
        {"question_id": "q4", "selected_answer": 4},
        {"question_id": "q5", "selected_answer": 7},
        {"question_id": "q6", "selected_answer": 9},  # Incorrect
    ]

    # Recalled words: Apple, House, Key (2 correct out of 3, 1 false-positive)
    user_words = ["Apple", "House", "Key"]

    metrics = ScoringService.score_calculation_recall(
        server_data=server_data,
        calculation_answers=user_calc_answers,
        recalled_words=user_words,
        calculation_time_ms=15000,
        word_recall_delay_seconds=42.5,
        total_time_ms=62000
    )

    # Check calculation metrics
    calc = metrics["calculation"]
    assert calc["correct_answers"] == 5
    assert calc["incorrect_answers"] == 1
    assert calc["questions_attempted"] == 6
    assert calc["calculation_accuracy"] == 83.33

    # Check word recall metrics
    recall = metrics["word_recall"]
    assert recall["task_name"] == "delayed_word_recognition"
    assert recall["correct_words"] == 2
    assert recall["missed_words"] == 1
    assert recall["false_positive_selections"] == 1
    assert recall["word_recall_accuracy"] == 66.67
    assert recall["actual_delay_seconds"] == 42.5


def test_calculation_invalid_question_id():
    server_data = {
        "calculation_answer_key": {"q1": 3},
        "target_words": ["Apple"],
        "recall_word_choices": ["Apple", "River"],
    }
    with pytest.raises(HTTPException):
        ScoringService.score_calculation_recall(
            server_data=server_data,
            calculation_answers=[{"question_id": "invalid_q", "selected_answer": 3}],
            recalled_words=["Apple"]
        )
