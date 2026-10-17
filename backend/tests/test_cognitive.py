"""Tests for cognitive activity sessions and results."""

import uuid
from fastapi import status


def test_create_cognitive_session(client, user_auth_headers):
    """Test creating a cognitive assessment session."""
    client_session_id = f"sess-{uuid.uuid4().hex}"
    payload = {
        "client_session_id": client_session_id,
        "activity_type": "sequence_recall",
        "activity_version": "1.0",
        "difficulty": 2,
        "started_at": "2026-10-17T08:30:00Z",
        "tasks_attempted": 10,
        "correct_count": 8,
        "incorrect_count": 2,
        "duration_seconds": 120.5,
    }
    resp = client.post("/api/v1/cognitive/sessions", headers=user_auth_headers, json=payload)
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["client_session_id"] == client_session_id
    assert data["activity_type"] == "sequence_recall"
    assert data["correct_count"] == 8

    # Idempotent re-post should return existing session
    resp_repost = client.post("/api/v1/cognitive/sessions", headers=user_auth_headers, json=payload)
    assert resp_repost.status_code == status.HTTP_201_CREATED
    assert resp_repost.json()["id"] == data["id"]


def test_invalid_counts_payload_rejected(client, user_auth_headers):
    """Validation rule: correct_count + incorrect_count cannot exceed tasks_attempted."""
    payload = {
        "client_session_id": f"sess-{uuid.uuid4().hex}",
        "activity_type": "pattern_match",
        "tasks_attempted": 5,
        "correct_count": 4,
        "incorrect_count": 3,  # 4 + 3 = 7 > 5 -> must fail
    }
    resp = client.post("/api/v1/cognitive/sessions", headers=user_auth_headers, json=payload)
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_cross_user_session_access_forbidden(client, user_auth_headers, other_user_auth_headers):
    """Test that a user cannot access another user's session."""
    payload = {
        "client_session_id": f"sess-{uuid.uuid4().hex}",
        "activity_type": "reaction_time",
    }
    create_resp = client.post("/api/v1/cognitive/sessions", headers=user_auth_headers, json=payload)
    session_id = create_resp.json()["id"]

    # Other user attempts to read
    other_resp = client.get(f"/api/v1/cognitive/sessions/{session_id}", headers=other_user_auth_headers)
    assert other_resp.status_code == status.HTTP_403_FORBIDDEN


def test_complete_cognitive_session(client, user_auth_headers):
    """Test completing an ongoing session."""
    create_resp = client.post(
        "/api/v1/cognitive/sessions",
        headers=user_auth_headers,
        json={
            "client_session_id": f"sess-{uuid.uuid4().hex}",
            "activity_type": "object_matching",
        },
    )
    session_id = create_resp.json()["id"]

    complete_payload = {
        "tasks_attempted": 6,
        "correct_count": 5,
        "incorrect_count": 1,
        "duration_seconds": 95.0,
    }
    comp_resp = client.post(
        f"/api/v1/cognitive/sessions/{session_id}/complete",
        headers=user_auth_headers,
        json=complete_payload,
    )
    assert comp_resp.status_code == status.HTTP_200_OK
    assert comp_resp.json()["status"] == "completed"
    assert comp_resp.json()["correct_count"] == 5


def test_submit_cognitive_result(client, user_auth_headers):
    """Test submitting task-level granular results for a session."""
    create_resp = client.post(
        "/api/v1/cognitive/sessions",
        headers=user_auth_headers,
        json={
            "client_session_id": f"sess-{uuid.uuid4().hex}",
            "activity_type": "sequence_recall",
        },
    )
    session_id = create_resp.json()["id"]

    res_payload = {
        "client_result_id": f"res-{uuid.uuid4().hex}",
        "session_id": session_id,
        "task_index": 1,
        "stimulus": "red, blue, green",
        "user_response": "red, blue, green",
        "is_correct": True,
        "response_time_ms": 1250,
        "score": 100.0,
    }
    resp = client.post("/api/v1/cognitive/results", headers=user_auth_headers, json=res_payload)
    assert resp.status_code == status.HTTP_201_CREATED
    assert resp.json()["is_correct"] is True


def test_cognitive_history_and_summary(client, user_auth_headers):
    """Test listing cognitive history and calculating non-diagnostic summary."""
    # Create 2 sessions
    for _ in range(2):
        client.post(
            "/api/v1/cognitive/sessions",
            headers=user_auth_headers,
            json={
                "client_session_id": f"sess-{uuid.uuid4().hex}",
                "activity_type": "sequence_recall",
                "completed_at": "2026-10-17T08:35:00Z",
                "tasks_attempted": 10,
                "correct_count": 8,
                "incorrect_count": 2,
                "duration_seconds": 60,
            },
        )

    hist_resp = client.get("/api/v1/cognitive/history", headers=user_auth_headers)
    assert hist_resp.status_code == status.HTTP_200_OK
    assert len(hist_resp.json()) >= 2

    sum_resp = client.get("/api/v1/cognitive/history/summary", headers=user_auth_headers)
    assert sum_resp.status_code == status.HTTP_200_OK
    summary = sum_resp.json()
    assert summary["total_completed"] >= 2
    assert summary["total_tasks_attempted"] >= 20
