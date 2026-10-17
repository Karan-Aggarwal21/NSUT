import pytest


def test_end_to_end_assessment_workflow(client):
    # 1. Create a user and start an assessment session
    create_session_res = client.post("/api/v1/sessions", json={
        "age_group": "75-84",
        "preferred_language": "en"
    })
    assert create_session_res.status_code == 200
    session_data = create_session_res.json()
    session_id = session_data["id"]
    user_id = session_data["user_id"]
    assert session_data["status"] == "in_progress"

    # Verify session is listed as in_progress
    status_res = client.get(f"/api/v1/sessions/{session_id}")
    assert status_res.json()["status"] == "in_progress"

    # --- ACTIVITY 1: Object Memory ---
    start_act1 = client.post(f"/api/v1/sessions/{session_id}/object-memory/start", json={"difficulty": "medium"})
    assert start_act1.status_code == 200
    att1_id = start_act1.json()["attempt_id"]
    items1 = start_act1.json()["task_data"]["presentation_items"]
    seq1 = [it["id"] for it in items1]

    sub_act1 = client.post(f"/api/v1/activities/{att1_id}/submit", json={
        "selected_sequence": seq1,
        "response_time_ms": 4000
    })
    assert sub_act1.status_code == 200
    assert sub_act1.json()["metrics"]["position_accuracy"] == 100.0

    # --- ACTIVITY 2: Circle Search ---
    start_act2 = client.post(f"/api/v1/sessions/{session_id}/circle-search/start", json={"difficulty": "easy"})
    assert start_act2.status_code == 200
    att2_id = start_act2.json()["attempt_id"]
    grid_items = start_act2.json()["task_data"]["grid_items"]
    # Find all circle IDs in the grid from client data
    circle_ids = [cell["id"] for cell in grid_items if cell["shape"] == "circle"]

    sub_act2 = client.post(f"/api/v1/activities/{att2_id}/submit", json={
        "selected_ids": circle_ids,
        "completion_time_ms": 15000
    })
    assert sub_act2.status_code == 200
    assert sub_act2.json()["metrics"]["target_detection_rate"] == 100.0
    assert sub_act2.json()["metrics"]["false_selection_rate"] == 0.0

    # --- ACTIVITY 3: Calculation & Delayed Word Recall ---
    start_act3 = client.post(f"/api/v1/sessions/{session_id}/calculation-recall/start", json={"difficulty": "easy"})
    assert start_act3.status_code == 200
    att3_id = start_act3.json()["attempt_id"]
    words_presented = start_act3.json()["task_data"]["words_to_present"]
    calc_questions = start_act3.json()["task_data"]["calculation_questions"]

    # Provide answers for calculation (choose first option)
    calc_answers = [
        {"question_id": q["id"], "selected_answer": q["options"][0]}
        for q in calc_questions
    ]

    sub_act3 = client.post(f"/api/v1/activities/{att3_id}/submit", json={
        "calculation_answers": calc_answers,
        "recalled_words": words_presented,  # Perfectly recalled original words
        "calculation_time_ms": 20000,
        "word_recall_delay_seconds": 45.0,
        "total_time_ms": 65000
    })
    assert sub_act3.status_code == 200
    assert sub_act3.json()["metrics"]["word_recall"]["word_recall_accuracy"] == 100.0

    # --- ACTIVITY 4: Shape Recognition ---
    start_act4 = client.post(f"/api/v1/sessions/{session_id}/shape-recognition/start", json={"difficulty": "easy"})
    assert start_act4.status_code == 200
    att4_id = start_act4.json()["attempt_id"]
    shape_questions = start_act4.json()["task_data"]["questions"]

    shape_answers = [
        {"question_id": q["id"], "selected_option_id": q["options"][0]["id"]}
        for q in shape_questions
    ]
    sub_act4 = client.post(f"/api/v1/activities/{att4_id}/submit", json={
        "answers": shape_answers,
        "completion_time_ms": 14000
    })
    assert sub_act4.status_code == 200

    # Complete the session
    complete_res = client.post(f"/api/v1/sessions/{session_id}/complete")
    assert complete_res.status_code == 200
    assert complete_res.json()["status"] == "completed"

    # Verify session report contains all 4 activities
    report_res = client.get(f"/api/v1/sessions/{session_id}/report")
    assert report_res.status_code == 200
    report = report_res.json()
    assert report["status"] == "completed"
    assert "object_memory" in report["activities"]
    assert "circle_search" in report["activities"]
    assert "calculation_recall" in report["activities"]
    assert "shape_recognition" in report["activities"]
    assert "experimental cognitive games" in report["disclaimer"]

    # Verify user longitudinal progress endpoint
    prog_res = client.get(f"/api/v1/users/{user_id}/progress")
    assert prog_res.status_code == 200
    prog = prog_res.json()
    assert prog["total_sessions"] == 1
    assert len(prog["sessions"]) == 1
    assert prog["sessions"][0]["status"] == "completed"
    assert prog["sessions"][0]["activities_completed"] == 4
