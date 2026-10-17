import pytest
from app.services.scoring_service import ScoringService
from fastapi import HTTPException


def test_object_memory_scoring_exact_match():
    server_data = {
        "correct_sequence": ["apple", "book", "key", "cup"],
        "difficulty": "medium",
    }
    user_sequence = ["apple", "book", "key", "cup"]

    result = ScoringService.score_object_memory(server_data, user_sequence, response_time_ms=5400)

    assert result["correct_positions"] == 4
    assert result["total_objects"] == 4
    assert result["position_accuracy"] == 100.0
    assert result["exact_sequence"] is True
    assert result["correct_identified"] == 4
    assert result["response_time_ms"] == 5400


def test_object_memory_partial_match():
    server_data = {
        "correct_sequence": ["apple", "book", "key", "cup"],
        "difficulty": "medium",
    }
    # apple (correct), key (wrong pos), book (wrong pos), cup (correct pos)
    user_sequence = ["apple", "key", "book", "cup"]

    result = ScoringService.score_object_memory(server_data, user_sequence)

    assert result["correct_positions"] == 2
    assert result["total_objects"] == 4
    assert result["position_accuracy"] == 50.0
    assert result["exact_sequence"] is False


def test_object_memory_duplicate_rejection():
    server_data = {
        "correct_sequence": ["apple", "book", "key", "cup"],
        "difficulty": "medium",
    }
    user_sequence = ["apple", "apple", "key", "cup"]

    with pytest.raises(HTTPException) as exc_info:
        ScoringService.score_object_memory(server_data, user_sequence)
    assert exc_info.value.status_code == 400
    assert "Duplicate object IDs" in exc_info.value.detail


def test_object_memory_invalid_id_rejection():
    server_data = {
        "correct_sequence": ["apple", "book", "key", "cup"],
        "difficulty": "medium",
    }
    user_sequence = ["apple", "spaceship", "key", "cup"]

    with pytest.raises(HTTPException) as exc_info:
        ScoringService.score_object_memory(server_data, user_sequence)
    assert exc_info.value.status_code == 400
    assert "Invalid object ID" in exc_info.value.detail


def test_object_memory_api_flow(client):
    # 1. Create session
    session_res = client.post("/api/v1/sessions", json={"age_group": "70-79"})
    assert session_res.status_code == 200
    session_id = session_res.json()["id"]

    # 2. Start object memory
    start_res = client.post(f"/api/v1/sessions/{session_id}/object-memory/start", json={"difficulty": "medium"})
    assert start_res.status_code == 200
    task_data = start_res.json()["task_data"]
    attempt_id = start_res.json()["attempt_id"]
    assert "presentation_items" in task_data
    assert "shuffled_choices" in task_data
    assert len(task_data["presentation_items"]) == 4

    # 3. Submit through API
    # Use the items in presentation order
    correct_order = [item["id"] for item in task_data["presentation_items"]]
    submit_res = client.post(f"/api/v1/activities/{attempt_id}/submit", json={
        "selected_sequence": correct_order,
        "response_time_ms": 3200
    })
    assert submit_res.status_code == 200
    res_json = submit_res.json()
    assert res_json["status"] == "completed"
    assert res_json["metrics"]["exact_sequence"] is True
    assert res_json["metrics"]["position_accuracy"] == 100.0

    # 4. Attempting duplicate submission fails
    dup_res = client.post(f"/api/v1/activities/{attempt_id}/submit", json={
        "selected_sequence": correct_order
    })
    assert dup_res.status_code == 400
