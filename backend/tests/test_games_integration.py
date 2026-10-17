"""Tests for cognitive game integration and final assessment report generation.

Covers:
1. Object Sequence Memory (task generation, hidden key, accurate scoring)
2. Circle Identification and Attention (cancellation grid, hits, misses, false alarms)
3. Personalized Memory Recognition
4. Pattern Matching
5. Final Assessment Session Report for Frontend UI (with questionnaire correlation)
"""

import uuid
from fastapi import status


def test_game_1_sequence_memory_flow(client, user_auth_headers):
    """Test Game 1: Object Sequence Memory start, hidden answer key, submission, and scoring."""
    # 1. Create Assessment Session
    sess_resp = client.post(
        "/api/v1/cognitive/sessions",
        headers=user_auth_headers,
        json={
            "client_session_id": f"sess-seq-{uuid.uuid4().hex}",
            "activity_type": "sequence_recall",
            "difficulty": 1,
        },
    )
    assert sess_resp.status_code == status.HTTP_201_CREATED
    session_id = sess_resp.json()["id"]

    # 2. Start Sequence Task
    start_resp = client.post(
        "/api/v1/cognitive/games/sequence/start",
        headers=user_auth_headers,
        json={
            "session_id": session_id,
            "difficulty": 1,
            "sequence_length": 3,
        },
    )
    assert start_resp.status_code == status.HTTP_201_CREATED
    start_data = start_resp.json()
    task_id = start_data["task_id"]
    display_sequence = start_data["display_sequence"]
    assert len(display_sequence) == 3
    assert len(start_data["available_choices"]) >= 3
    # The user should have received the sequence to view
    item_a, item_b, item_c = display_sequence

    # 3. Submit exact match
    submit_resp = client.post(
        "/api/v1/cognitive/games/sequence/submit",
        headers=user_auth_headers,
        json={
            "task_id": task_id,
            "session_id": session_id,
            "task_index": 1,
            "submitted_sequence": [item_a, item_b, item_c],
            "response_time_ms": 3500,
            "attempts": 1,
        },
    )
    assert submit_resp.status_code == status.HTTP_200_OK
    res_data = submit_resp.json()
    assert res_data["total_positions"] == 3
    assert res_data["correct_positions"] == 3
    assert res_data["items_recalled"] == 3
    assert res_data["exact_sequence_match"] is True
    assert res_data["position_accuracy"] == 1.0
    assert res_data["score"] == 100.0
    assert res_data["response_time_seconds"] == 3.5


def test_game_1_sequence_memory_partial_match(client, user_auth_headers):
    """Test Game 1 handles misplaced and missing objects gracefully."""
    sess_resp = client.post(
        "/api/v1/cognitive/sessions",
        headers=user_auth_headers,
        json={
            "client_session_id": f"sess-seq2-{uuid.uuid4().hex}",
            "activity_type": "sequence_recall",
        },
    )
    session_id = sess_resp.json()["id"]

    start_resp = client.post(
        "/api/v1/cognitive/games/sequence/start",
        headers=user_auth_headers,
        json={"session_id": session_id, "sequence_length": 4},
    )
    start_data = start_resp.json()
    task_id = start_data["task_id"]
    seq = start_data["display_sequence"]

    # Swap 2 items: positions 0 and 1 are swapped, 2 and 3 match
    swapped_submission = [seq[1], seq[0], seq[2], seq[3]]

    submit_resp = client.post(
        "/api/v1/cognitive/games/sequence/submit",
        headers=user_auth_headers,
        json={
            "task_id": task_id,
            "session_id": session_id,
            "submitted_sequence": swapped_submission,
            "response_time_ms": 5200,
            "attempts": 1,
        },
    )
    assert submit_resp.status_code == status.HTTP_200_OK
    res_data = submit_resp.json()
    assert res_data["correct_positions"] == 2
    assert res_data["items_recalled"] == 4  # All items present, but 2 in wrong positions
    assert res_data["position_accuracy"] == 0.5
    assert res_data["exact_sequence_match"] is False
    assert res_data["score"] > 0.0


def test_game_2_circle_attention_cancellation_flow(client, user_auth_headers):
    """Test Game 2: Circle Identification & Attention cancellation task flow."""
    sess_resp = client.post(
        "/api/v1/cognitive/sessions",
        headers=user_auth_headers,
        json={
            "client_session_id": f"sess-att-{uuid.uuid4().hex}",
            "activity_type": "circle_attention",
        },
    )
    session_id = sess_resp.json()["id"]

    # 1. Start Attention Task (generates 4x4 grid)
    start_resp = client.post(
        "/api/v1/cognitive/games/attention/start",
        headers=user_auth_headers,
        json={
            "session_id": session_id,
            "difficulty": 1,
            "grid_rows": 4,
            "grid_cols": 4,
        },
    )
    assert start_resp.status_code == status.HTTP_201_CREATED
    start_data = start_resp.json()
    task_id = start_data["task_id"]
    items = start_data["items"]
    assert len(items) == 16

    # Identify circles and non-circles from display
    circles = [item["id"] for item in items if item["shape_type"] == "circle"]
    non_circles = [item["id"] for item in items if item["shape_type"] != "circle"]
    assert len(circles) > 0
    assert len(non_circles) > 0

    # User selects all actual circles + 1 accidental distractor click
    selected_ids = circles + [non_circles[0]]

    # 2. Submit cancellation selections
    submit_resp = client.post(
        "/api/v1/cognitive/games/attention/submit",
        headers=user_auth_headers,
        json={
            "task_id": task_id,
            "session_id": session_id,
            "selected_ids": selected_ids,
            "response_time_ms": 7800,
        },
    )
    assert submit_resp.status_code == status.HTTP_200_OK
    res_data = submit_resp.json()
    assert res_data["total_targets"] == len(circles)
    assert res_data["correct_selections"] == len(circles)
    assert res_data["missed_targets"] == 0
    assert res_data["distractor_selections"] == 1
    assert res_data["recall"] == 1.0
    assert res_data["precision"] < 1.0
    assert res_data["attention_score"] > 80.0
    assert res_data["response_time_seconds"] == 7.8


def test_game_3_personalized_recognition(client, user_auth_headers):
    """Test Game 3: Personalized Memory cue task flow."""
    # Create a personalized item
    item_resp = client.post(
        "/api/v1/personalized/items",
        headers=user_auth_headers,
        json={
            "category": "familiar_person",
            "display_name": "Grandson Aarav",
            "description": "7-year-old grandson, plays cricket",
        },
    )
    item_id = item_resp.json()["id"]

    # Create Session
    sess_resp = client.post(
        "/api/v1/cognitive/sessions",
        headers=user_auth_headers,
        json={
            "client_session_id": f"sess-pers-{uuid.uuid4().hex}",
            "activity_type": "personalized_activity",
        },
    )
    session_id = sess_resp.json()["id"]

    # Start Task
    start_resp = client.post(
        "/api/v1/cognitive/games/personalized/start",
        headers=user_auth_headers,
        json={"session_id": session_id, "item_id": item_id},
    )
    assert start_resp.status_code == status.HTTP_201_CREATED
    task_id = start_resp.json()["task_id"]
    options = start_resp.json()["options"]
    assert "Grandson Aarav" in options

    # Submit Correct Answer
    submit_resp = client.post(
        "/api/v1/cognitive/games/personalized/submit",
        headers=user_auth_headers,
        json={
            "task_id": task_id,
            "session_id": session_id,
            "item_id": item_id,
            "selected_answer": "Grandson Aarav",
            "response_time_ms": 2100,
        },
    )
    assert submit_resp.status_code == status.HTTP_200_OK
    assert submit_resp.json()["is_correct"] is True
    assert submit_resp.json()["score"] == 100.0


def test_final_session_assessment_report_generation(client, user_auth_headers):
    """Test generating the complete assessment report for the frontend UI with questionnaire integration."""
    # 1. Complete Questionnaire Check-in
    client.post(
        "/api/v1/questionnaires/memory-wellbeing-v1/responses",
        headers=user_auth_headers,
        json={
            "client_submission_id": f"qsub-{uuid.uuid4().hex}",
            "questionnaire_version": "1.0",
            "answers": [
                {"question_id": "recent_memory_difficulties", "answer": "sometimes"},
                {"question_id": "recent_emotional_wellbeing", "answer": "good"},
                {"question_id": "level_of_concern", "answer": "not_concerned"},
            ],
        },
    )

    # 2. Create Assessment Session
    sess_resp = client.post(
        "/api/v1/cognitive/sessions",
        headers=user_auth_headers,
        json={
            "client_session_id": f"sess-full-{uuid.uuid4().hex}",
            "activity_type": "multi_game_assessment",
        },
    )
    session_id = sess_resp.json()["id"]

    # 3. Complete Game 1: Sequence Recall
    start_seq = client.post(
        "/api/v1/cognitive/games/sequence/start",
        headers=user_auth_headers,
        json={"session_id": session_id, "sequence_length": 3},
    )
    seq = start_seq.json()["display_sequence"]
    client.post(
        "/api/v1/cognitive/games/sequence/submit",
        headers=user_auth_headers,
        json={
            "task_id": start_seq.json()["task_id"],
            "session_id": session_id,
            "submitted_sequence": seq,
            "response_time_ms": 3000,
        },
    )

    # 4. Complete Game 2: Attention Cancellation
    start_att = client.post(
        "/api/v1/cognitive/games/attention/start",
        headers=user_auth_headers,
        json={"session_id": session_id, "grid_rows": 3, "grid_cols": 3},
    )
    circles = [i["id"] for i in start_att.json()["items"] if i["shape_type"] == "circle"]
    client.post(
        "/api/v1/cognitive/games/attention/submit",
        headers=user_auth_headers,
        json={
            "task_id": start_att.json()["task_id"],
            "session_id": session_id,
            "selected_ids": circles,
            "response_time_ms": 4500,
        },
    )

    # 5. Fetch Final Report
    report_resp = client.get(
        f"/api/v1/cognitive/sessions/{session_id}/report",
        headers=user_auth_headers,
    )
    assert report_resp.status_code == status.HTTP_200_OK
    report = report_resp.json()

    assert report["session_id"] == session_id
    assert report["overall_score"] >= 80.0
    assert "Active" in report["performance_rating"] or "Focus" in report["performance_rating"] or "Engagement" in report["performance_rating"]

    # Verify domain breakdown
    domains_map = {d["domain"]: d for d in report["domains"]}
    assert "Working Memory" in domains_map
    assert "Selective Attention" in domains_map
    assert domains_map["Working Memory"]["tasks_completed"] == 1
    assert domains_map["Selective Attention"]["tasks_completed"] == 1

    # Verify game results list
    assert len(report["game_results"]) == 2

    # Verify questionnaire correlation
    assert report["questionnaire_summary"]["completed"] is True
    assert report["questionnaire_summary"]["emotional_wellbeing"] == "good"
    assert report["questionnaire_summary"]["level_of_concern"] == "not_concerned"

    # Verify non-diagnostic clinical disclaimer
    assert "does not constitute a medical diagnosis" in report["clinical_disclaimer"]
