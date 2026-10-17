import pytest
from app.services.scoring_service import ScoringService
from fastapi import HTTPException


def test_circle_search_scoring():
    server_data = {
        "circle_ids": ["c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8"],
        "non_circle_ids": ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8"],
        "difficulty": "medium"
    }

    # Selected 6 correct circles and 1 incorrect square
    selected_ids = ["c1", "c2", "c3", "c4", "c5", "c6", "s1"]

    metrics = ScoringService.score_circle_search(server_data, selected_ids, completion_time_ms=12000)

    assert metrics["correct_circles_selected"] == 6
    assert metrics["circles_missed"] == 2
    assert metrics["incorrect_non_circle_selections"] == 1
    assert metrics["total_circles"] == 8
    assert metrics["total_non_circles"] == 8
    assert metrics["target_detection_rate"] == 75.0
    assert metrics["false_selection_rate"] == 12.5


def test_circle_search_deduplication():
    server_data = {
        "circle_ids": ["c1", "c2"],
        "non_circle_ids": ["s1", "s2"],
    }
    # Duplicate selection of c1 should not count twice
    selected_ids = ["c1", "c1", "c1"]
    metrics = ScoringService.score_circle_search(server_data, selected_ids)
    assert metrics["correct_circles_selected"] == 1
    assert metrics["target_detection_rate"] == 50.0


def test_circle_search_invalid_id():
    server_data = {
        "circle_ids": ["c1", "c2"],
        "non_circle_ids": ["s1", "s2"],
    }
    with pytest.raises(HTTPException):
        ScoringService.score_circle_search(server_data, ["unknown_cell_999"])
