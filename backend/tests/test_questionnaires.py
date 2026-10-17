"""Tests for questionnaires – 7-question definition, answer validation, and response history."""

import uuid
from fastapi import status


def test_list_questionnaires_and_get_definition(client):
    """Test getting available questionnaires and the 7-question default structure."""
    list_resp = client.get("/api/v1/questionnaires")
    assert list_resp.status_code == status.HTTP_200_OK
    items = list_resp.json()
    assert len(items) >= 1

    # Fetch default questionnaire
    q_resp = client.get("/api/v1/questionnaires/memory-wellbeing-v1")
    assert q_resp.status_code == status.HTTP_200_OK
    data = q_resp.json()
    assert data["slug"] == "memory-wellbeing-v1"
    assert len(data["versions"]) >= 1

    version = data["versions"][0]
    assert version["version_label"] == "1.0"
    questions = version["questions"]
    assert len(questions) == 7

    # Check question keys include recent_memory_difficulties and level_of_concern
    q_keys = [q["question_key"] for q in questions]
    assert "recent_memory_difficulties" in q_keys
    assert "misplacing_familiar_objects" in q_keys
    assert "difficulty_concentrating" in q_keys
    assert "daily_routines_difficulty" in q_keys
    assert "noticed_changes_thinking" in q_keys
    assert "recent_emotional_wellbeing" in q_keys
    assert "level_of_concern" in q_keys


def test_submit_questionnaire_success(client, user_auth_headers):
    """Test submitting valid answers for the questionnaire."""
    client_sub_id = f"qsub-{uuid.uuid4().hex}"
    payload = {
        "client_submission_id": client_sub_id,
        "questionnaire_version": "1.0",
        "completed_at": "2026-10-17T08:40:00Z",
        "answers": [
            {"question_id": "recent_memory_difficulties", "answer": "sometimes"},
            {"question_id": "difficulty_concentrating", "answer": "never"},
            {"question_id": "recent_emotional_wellbeing", "answer": "good"},
            {"question_id": "level_of_concern", "answer": "prefer_not_to_answer"},
        ],
    }
    resp = client.post(
        "/api/v1/questionnaires/memory-wellbeing-v1/responses",
        headers=user_auth_headers,
        json=payload,
    )
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["completion_status"] == "completed"
    assert len(data["answers"]) == 4

    # Idempotent resubmission on network retries
    resub_resp = client.post(
        "/api/v1/questionnaires/memory-wellbeing-v1/responses",
        headers=user_auth_headers,
        json=payload,
    )
    assert resub_resp.status_code == status.HTTP_201_CREATED
    assert resub_resp.json()["id"] == data["id"]


def test_submit_questionnaire_invalid_question_id_fails(client, user_auth_headers):
    """Test submitting a non-existent question ID fails with 400."""
    payload = {
        "questionnaire_version": "1.0",
        "answers": [
            {"question_id": "unrecognized_question_key", "answer": "never"},
        ],
    }
    resp = client.post(
        "/api/v1/questionnaires/memory-wellbeing-v1/responses",
        headers=user_auth_headers,
        json=payload,
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "not part of questionnaire" in resp.json()["detail"]


def test_submit_questionnaire_invalid_option_fails(client, user_auth_headers):
    """Test submitting an invalid option for a question fails with 400."""
    payload = {
        "questionnaire_version": "1.0",
        "answers": [
            {"question_id": "recent_memory_difficulties", "answer": "always_every_minute"},
        ],
    }
    resp = client.post(
        "/api/v1/questionnaires/memory-wellbeing-v1/responses",
        headers=user_auth_headers,
        json=payload,
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid option" in resp.json()["detail"]


def test_questionnaire_history_and_detail(client, user_auth_headers):
    """Test retrieving list of submissions and inspecting response detail."""
    sub_resp = client.post(
        "/api/v1/questionnaires/memory-wellbeing-v1/responses",
        headers=user_auth_headers,
        json={
            "client_submission_id": f"qsub-{uuid.uuid4().hex}",
            "questionnaire_version": "1.0",
            "answers": [
                {"question_id": "recent_memory_difficulties", "answer": "sometimes"},
            ],
        },
    )
    response_id = sub_resp.json()["id"]

    # List responses
    list_resp = client.get("/api/v1/questionnaires/responses", headers=user_auth_headers)
    assert list_resp.status_code == status.HTTP_200_OK
    assert len(list_resp.json()) >= 1

    # Read response detail
    detail_resp = client.get(
        f"/api/v1/questionnaires/responses/{response_id}", headers=user_auth_headers
    )
    assert detail_resp.status_code == status.HTTP_200_OK
    assert detail_resp.json()["id"] == response_id
    assert len(detail_resp.json()["answers"]) == 1


def test_cross_user_questionnaire_response_access_denied(
    client, user_auth_headers, other_user_auth_headers
):
    """Ensure questionnaire answers are strictly private to the owner."""
    sub_resp = client.post(
        "/api/v1/questionnaires/memory-wellbeing-v1/responses",
        headers=user_auth_headers,
        json={
            "client_submission_id": f"qsub-{uuid.uuid4().hex}",
            "questionnaire_version": "1.0",
            "answers": [
                {"question_id": "level_of_concern", "answer": "mildly_concerned"},
            ],
        },
    )
    response_id = sub_resp.json()["id"]

    # Other user attempts to view private answers
    other_resp = client.get(
        f"/api/v1/questionnaires/responses/{response_id}", headers=other_user_auth_headers
    )
    assert other_resp.status_code == status.HTTP_403_FORBIDDEN
