"""Tests for personalised activity items, sessions, and memory cue management."""

import uuid
from fastapi import status


def test_create_and_read_personalized_item(client, user_auth_headers):
    """Test creating a personalised memory item (e.g., familiar family member)."""
    payload = {
        "category": "familiar_person",
        "display_name": "Daughter Priya",
        "description": "Lives in Guwahati, visits on weekends",
        "image_reference": "local_storage://images/priya.jpg",
    }
    resp = client.post("/api/v1/personalized/items", headers=user_auth_headers, json=payload)
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["display_name"] == "Daughter Priya"
    assert data["category"] == "familiar_person"
    item_id = data["id"]

    # Read back
    get_resp = client.get(f"/api/v1/personalized/items/{item_id}", headers=user_auth_headers)
    assert get_resp.status_code == status.HTTP_200_OK
    assert get_resp.json()["display_name"] == "Daughter Priya"


def test_update_personalized_item(client, user_auth_headers):
    """Test editing personalised memory item."""
    create_resp = client.post(
        "/api/v1/personalized/items",
        headers=user_auth_headers,
        json={"category": "place", "display_name": "Old School"},
    )
    item_id = create_resp.json()["id"]

    patch_resp = client.patch(
        f"/api/v1/personalized/items/{item_id}",
        headers=user_auth_headers,
        json={"display_name": "Tezpur High School", "description": "Studied 1958-1964"},
    )
    assert patch_resp.status_code == status.HTTP_200_OK
    assert patch_resp.json()["display_name"] == "Tezpur High School"


def test_delete_personalized_item_deactivates(client, user_auth_headers):
    """Test soft-deleting personalised memory cues."""
    create_resp = client.post(
        "/api/v1/personalized/items",
        headers=user_auth_headers,
        json={"category": "object", "display_name": "Vintage Radio"},
    )
    item_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/v1/personalized/items/{item_id}", headers=user_auth_headers)
    assert del_resp.status_code == status.HTTP_200_OK

    # Item should be marked inactive and omitted from default list
    list_resp = client.get("/api/v1/personalized/items", headers=user_auth_headers)
    active_ids = [item["id"] for item in list_resp.json()]
    assert item_id not in active_ids


def test_cross_user_personalized_item_access_denied(client, user_auth_headers, other_user_auth_headers):
    """Test other users cannot view or modify someone else's memory items."""
    create_resp = client.post(
        "/api/v1/personalized/items",
        headers=user_auth_headers,
        json={"category": "place", "display_name": "Private Home Garden"},
    )
    item_id = create_resp.json()["id"]

    # Other user attempts read
    read_resp = client.get(f"/api/v1/personalized/items/{item_id}", headers=other_user_auth_headers)
    assert read_resp.status_code == status.HTTP_403_FORBIDDEN

    # Other user attempts patch
    patch_resp = client.patch(
        f"/api/v1/personalized/items/{item_id}",
        headers=other_user_auth_headers,
        json={"display_name": "Hacked Name"},
    )
    assert patch_resp.status_code == status.HTTP_403_FORBIDDEN


def test_personalized_session_and_history(client, user_auth_headers):
    """Test recording a session using personalized memory cues."""
    sess_payload = {
        "client_session_id": f"pers-sess-{uuid.uuid4().hex}",
        "activity_type": "face_recognition",
        "activity_version": "1.0",
        "difficulty": 1,
        "completed_at": "2026-10-17T09:00:00Z",
        "tasks_attempted": 5,
        "correct_count": 4,
        "incorrect_count": 1,
        "duration_seconds": 60,
    }
    resp = client.post("/api/v1/personalized/sessions", headers=user_auth_headers, json=sess_payload)
    assert resp.status_code == status.HTTP_201_CREATED
    assert resp.json()["activity_type"] == "personalized:face_recognition"

    # Verify history
    hist_resp = client.get("/api/v1/personalized/history", headers=user_auth_headers)
    assert hist_resp.status_code == status.HTTP_200_OK
    assert len(hist_resp.json()) >= 1
