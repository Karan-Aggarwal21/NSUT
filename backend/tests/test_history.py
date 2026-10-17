"""Tests for combined activity history and summary aggregation."""

import uuid
from fastapi import status


def test_combined_activity_history(client, user_auth_headers):
    """Test unified history combines cognitive, personalized, and questionnaire submissions."""
    # 1. Cognitive session
    client.post(
        "/api/v1/cognitive/sessions",
        headers=user_auth_headers,
        json={
            "client_session_id": f"cog-{uuid.uuid4().hex}",
            "activity_type": "sequence_recall",
            "completed_at": "2026-10-17T08:30:00Z",
        },
    )

    # 2. Personalized session
    client.post(
        "/api/v1/personalized/sessions",
        headers=user_auth_headers,
        json={
            "client_session_id": f"pers-{uuid.uuid4().hex}",
            "activity_type": "familiar_person",
            "completed_at": "2026-10-17T08:35:00Z",
        },
    )

    # 3. Questionnaire submission
    client.post(
        "/api/v1/questionnaires/memory-wellbeing-v1/responses",
        headers=user_auth_headers,
        json={
            "client_submission_id": f"quest-{uuid.uuid4().hex}",
            "questionnaire_version": "1.0",
            "answers": [
                {"question_id": "recent_memory_difficulties", "answer": "never"},
            ],
        },
    )

    # Fetch combined history
    resp = client.get("/api/v1/history", headers=user_auth_headers)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    items = data["items"]
    record_types = {item["record_type"] for item in items}

    assert "cognitive_activity" in record_types
    assert "personalized_activity" in record_types
    assert "questionnaire" in record_types

    # Ensure sensitive question answers are not exposed in history items
    for item in items:
        assert "answers" not in item
        assert "answer_value" not in item


def test_combined_history_filtering(client, user_auth_headers):
    """Test filtering combined history by category."""
    # Filter cognitive only
    cog_resp = client.get(
        "/api/v1/history?activity_category=cognitive", headers=user_auth_headers
    )
    assert cog_resp.status_code == status.HTTP_200_OK
    for item in cog_resp.json()["items"]:
        assert item["record_type"] == "cognitive_activity"

    # Filter questionnaire only
    quest_resp = client.get(
        "/api/v1/history?activity_category=questionnaire", headers=user_auth_headers
    )
    assert quest_resp.status_code == status.HTTP_200_OK
    for item in quest_resp.json()["items"]:
        assert item["record_type"] == "questionnaire"


def test_combined_history_summary(client, user_auth_headers):
    """Test history summary statistics."""
    resp = client.get("/api/v1/history/summary", headers=user_auth_headers)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert "total_cognitive_sessions" in data
    assert "total_personalized_sessions" in data
    assert "total_questionnaire_responses" in data
