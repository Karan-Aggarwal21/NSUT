"""Tests for offline batch synchronization and idempotency."""

import uuid
from fastapi import status


def test_offline_sync_batch_success(client, user_auth_headers):
    """Test synchronising a batch of offline sessions and questionnaires."""
    cog_client_id = f"sync-cog-{uuid.uuid4().hex}"
    pers_client_id = f"sync-pers-{uuid.uuid4().hex}"
    quest_client_id = f"sync-quest-{uuid.uuid4().hex}"

    sync_payload = {
        "cognitive_sessions": [
            {
                "client_session_id": cog_client_id,
                "activity_type": "symbol_sequence",
                "completed_at": "2026-10-17T07:30:00Z",
                "tasks_attempted": 8,
                "correct_count": 7,
                "incorrect_count": 1,
                "duration_seconds": 90,
            }
        ],
        "personalized_sessions": [
            {
                "client_session_id": pers_client_id,
                "activity_type": "familiar_places",
                "completed_at": "2026-10-17T07:35:00Z",
                "tasks_attempted": 4,
                "correct_count": 4,
                "incorrect_count": 0,
            }
        ],
        "questionnaire_responses": [
            {
                "client_submission_id": quest_client_id,
                "questionnaire_version": "1.0",
                "completed_at": "2026-10-17T07:40:00Z",
                "answers": [
                    {"question_id": "recent_memory_difficulties", "answer": "sometimes"},
                ],
            }
        ],
        "questionnaire_ids": ["memory-wellbeing-v1"],
    }

    resp = client.post("/api/v1/sync", headers=user_auth_headers, json=sync_payload)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["accepted_count"] == 3
    assert data["error_count"] == 0

    # Idempotent re-sync with the exact same batch should report duplicate instead of erroring
    re_resp = client.post("/api/v1/sync", headers=user_auth_headers, json=sync_payload)
    assert re_resp.status_code == status.HTTP_200_OK
    re_data = re_resp.json()
    assert re_data["duplicate_count"] == 3
    assert re_data["accepted_count"] == 0


def test_offline_sync_error_isolation(client, user_auth_headers):
    """Test that a failure in one invalid record does not block other valid records in batch."""
    valid_id = f"sync-valid-{uuid.uuid4().hex}"
    invalid_id = f"sync-invalid-{uuid.uuid4().hex}"

    sync_payload = {
        "cognitive_sessions": [
            {
                "client_session_id": valid_id,
                "activity_type": "sequence_recall",
                "tasks_attempted": 5,
                "correct_count": 4,
                "incorrect_count": 1,
            },
            # Invalid count: correct + incorrect (6) > tasks_attempted (4)
            # Will be caught by Pydantic before service if submitted directly as session,
            # But let's test questionnaire with invalid option
        ],
        "questionnaire_responses": [
            {
                "client_submission_id": invalid_id,
                "questionnaire_version": "1.0",
                "answers": [
                    {"question_id": "recent_memory_difficulties", "answer": "invalid_option_xyz"},
                ],
            }
        ],
        "questionnaire_ids": ["memory-wellbeing-v1"],
    }

    resp = client.post("/api/v1/sync", headers=user_auth_headers, json=sync_payload)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["accepted_count"] == 1
    assert data["error_count"] == 1

    statuses = {r["client_id"]: r["status"] for r in data["results"]}
    assert statuses[valid_id] == "accepted"
    assert statuses[invalid_id] == "error"
