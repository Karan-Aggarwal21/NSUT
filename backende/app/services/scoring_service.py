"""Scoring engine for cognitive games.

Provides robust, consistent scoring algorithms for:
1. Object Sequence Memory (Working Memory & Ordering)
2. Circle Identification and Attention (Shape Cancellation & Selective Attention)
3. Personalized Memory Recognition (Episodic Recall)
4. Visual Pattern / Matching (Processing Speed & Recognition)
"""

from __future__ import annotations

from typing import Any


# ============================================================================
# Game 1: Object Sequence Memory Scoring
# ============================================================================

def score_sequence_memory(
    target_sequence: list[str],
    submitted_sequence: list[str],
    response_time_ms: int | None = None,
    attempts: int = 1,
) -> dict[str, Any]:
    """Score Object Sequence Memory.

    Compares user's submitted sequence against target sequence.
    Handles:
    - Position-by-position exact placement.
    - Recall regardless of position (items recalled from target pool).
    - Duplicate entries, omissions, and extra selections.

    Metrics:
    - total_positions: int
    - correct_positions: int
    - items_recalled: int (count of unique target items present in submission)
    - position_accuracy: float [0.0 - 1.0]
    - recall_accuracy: float [0.0 - 1.0]
    - exact_sequence_match: bool
    - score: float [0.0 - 100.0]
    - response_time_seconds: float | None
    - attempts: int
    """
    total_positions = len(target_sequence)
    if total_positions == 0:
        return {
            "total_positions": 0,
            "correct_positions": 0,
            "items_recalled": 0,
            "position_accuracy": 0.0,
            "recall_accuracy": 0.0,
            "exact_sequence_match": False,
            "score": 0.0,
            "response_time_seconds": (response_time_ms / 1000.0) if response_time_ms is not None else None,
            "attempts": attempts,
        }

    # Normalize to lowercase strings
    norm_target = [str(x).strip().lower() for x in target_sequence]
    norm_sub = [str(x).strip().lower() for x in submitted_sequence]

    # 1. Position-by-position comparison
    min_len = min(len(norm_target), len(norm_sub))
    correct_positions = 0
    for i in range(min_len):
        if norm_sub[i] == norm_target[i]:
            correct_positions += 1

    exact_sequence_match = (norm_sub == norm_target)

    # 2. Item recall regardless of order (multiset / frequency comparison to handle duplicates)
    target_counts: dict[str, int] = {}
    for item in norm_target:
        target_counts[item] = target_counts.get(item, 0) + 1

    sub_counts: dict[str, int] = {}
    for item in norm_sub:
        sub_counts[item] = sub_counts.get(item, 0) + 1

    items_recalled = 0
    for item, count in sub_counts.items():
        if item in target_counts:
            items_recalled += min(count, target_counts[item])

    position_accuracy = round(correct_positions / total_positions, 4)
    recall_accuracy = round(items_recalled / total_positions, 4)

    # Overall score: 60% position accuracy + 40% item recall accuracy
    # With a small bonus for exact first-attempt match
    base_score = (0.6 * position_accuracy + 0.4 * recall_accuracy) * 100.0
    if exact_sequence_match and attempts == 1:
        base_score = 100.0

    score = round(max(0.0, min(100.0, base_score)), 1)
    response_time_sec = round(response_time_ms / 1000.0, 2) if response_time_ms is not None else None

    return {
        "total_positions": total_positions,
        "submitted_length": len(norm_sub),
        "correct_positions": correct_positions,
        "items_recalled": items_recalled,
        "position_accuracy": position_accuracy,
        "recall_accuracy": recall_accuracy,
        "exact_sequence_match": exact_sequence_match,
        "score": score,
        "response_time_seconds": response_time_sec,
        "attempts": attempts,
    }


# ============================================================================
# Game 2: Circle Identification and Attention (Shape Cancellation)
# ============================================================================

def score_attention_cancellation(
    target_ids: set[str] | list[str],
    all_grid_ids: set[str] | list[str],
    selected_ids: set[str] | list[str],
    response_time_ms: int | None = None,
) -> dict[str, Any]:
    """Score Circle Identification and Selective Attention.

    Based on Signal Detection Theory / Cancellation Task metrics:
    - True Positives (TP / Hits): Correctly selected target circles
    - False Negatives (FN / Misses): Missed target circles
    - False Positives (FP / Distractor Selections): Selected non-circle shapes
    - True Negatives (TN): Non-circle distractors correctly avoided

    Metrics:
    - total_targets: int
    - total_distractors: int
    - correct_selections: int (TP)
    - missed_targets: int (FN)
    - distractor_selections: int (FP)
    - precision: float [0.0 - 1.0] (TP / (TP + FP))
    - recall: float [0.0 - 1.0] (TP / total_targets)
    - f1_score: float [0.0 - 1.0]
    - attention_score: float [0.0 - 100.0]
    - response_time_seconds: float | None
    """
    targets = {str(x).strip() for x in target_ids}
    all_items = {str(x).strip() for x in all_grid_ids}
    selected = {str(x).strip() for x in selected_ids}

    # Distractors are items in grid that are NOT targets
    distractors = all_items - targets

    total_targets = len(targets)
    total_distractors = len(distractors)

    correct_selections = len(selected & targets)
    missed_targets = total_targets - correct_selections
    distractor_selections = len(selected & distractors)

    # Precision: accuracy of user's clicks
    precision = (
        round(correct_selections / len(selected), 4)
        if len(selected) > 0
        else (1.0 if total_targets == 0 else 0.0)
    )

    # Recall / Sensitivity: percentage of targets identified
    recall = (
        round(correct_selections / total_targets, 4)
        if total_targets > 0
        else 1.0
    )

    # F1 score harmonic mean
    if precision + recall > 0:
        f1 = round(2 * (precision * recall) / (precision + recall), 4)
    else:
        f1 = 0.0

    # Composite Attention Score (0 to 100):
    # Rewards finding targets (recall * 60) and penalizes false alarms (precision * 40)
    attention_score = round(f1 * 100.0, 1)

    response_time_sec = round(response_time_ms / 1000.0, 2) if response_time_ms is not None else None

    return {
        "total_targets": total_targets,
        "total_distractors": total_distractors,
        "total_selected": len(selected),
        "correct_selections": correct_selections,
        "missed_targets": missed_targets,
        "distractor_selections": distractor_selections,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "score": attention_score,
        "attention_score": attention_score,
        "response_time_seconds": response_time_sec,
    }


# ============================================================================
# Game 3: Personalized Memory Recognition
# ============================================================================

def score_personalized_recognition(
    expected_answer: str,
    user_answer: str,
    response_time_ms: int | None = None,
) -> dict[str, Any]:
    """Score Personalized Memory cue identification (e.g. name of grandchild, familiar place)."""
    is_correct = (str(expected_answer).strip().lower() == str(user_answer).strip().lower())
    score = 100.0 if is_correct else 0.0
    response_time_sec = round(response_time_ms / 1000.0, 2) if response_time_ms is not None else None

    return {
        "is_correct": is_correct,
        "score": score,
        "response_time_seconds": response_time_sec,
    }


# ============================================================================
# Game 4: Visual Matching / Rapid Recognition
# ============================================================================

def score_visual_matching(
    matched_correctly: bool,
    response_time_ms: int | None = None,
) -> dict[str, Any]:
    """Score speeded shape or pattern matching."""
    score = 100.0 if matched_correctly else 0.0
    response_time_sec = round(response_time_ms / 1000.0, 2) if response_time_ms is not None else None

    return {
        "is_correct": matched_correctly,
        "score": score,
        "response_time_seconds": response_time_sec,
    }
