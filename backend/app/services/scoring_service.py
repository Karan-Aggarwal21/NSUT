from typing import Dict, Any, List
from fastapi import HTTPException


class ScoringService:
    @staticmethod
    def score_object_memory(
        server_data: Dict[str, Any],
        selected_sequence: List[str],
        response_time_ms: int = None
    ) -> Dict[str, Any]:
        """
        Calculates authoritative metrics for Object Sequence Memory.
        """
        correct_sequence = server_data.get("correct_sequence", [])
        total_objects = len(correct_sequence)

        # Validation: Check for duplicates or invalid items
        if len(selected_sequence) != len(set(selected_sequence)):
            raise HTTPException(status_code=400, detail="Duplicate object IDs are not allowed in the sequence.")

        # Check that submitted items are valid objects
        for item_id in selected_sequence:
            if item_id not in correct_sequence:
                raise HTTPException(status_code=400, detail=f"Invalid object ID '{item_id}' not found in task.")

        # Calculate position matches
        correct_positions = 0
        for idx in range(min(len(selected_sequence), total_objects)):
            if selected_sequence[idx] == correct_sequence[idx]:
                correct_positions += 1

        correct_identified = len([item for item in selected_sequence if item in correct_sequence])
        exact_sequence = (selected_sequence == correct_sequence)

        position_accuracy = round((correct_positions / total_objects) * 100.0, 2) if total_objects > 0 else 0.0

        return {
            "correct_positions": correct_positions,
            "total_objects": total_objects,
            "position_accuracy": position_accuracy,
            "exact_sequence": exact_sequence,
            "correct_identified": correct_identified,
            "response_time_ms": response_time_ms,
            "difficulty": server_data.get("difficulty", "medium"),
            "task_version": "v1.0"
        }

    @staticmethod
    def score_circle_search(
        server_data: Dict[str, Any],
        selected_ids: List[str],
        completion_time_ms: int = None
    ) -> Dict[str, Any]:
        """
        Calculates target detection and false selection rates for Circle Search.
        """
        circle_ids = set(server_data.get("circle_ids", []))
        non_circle_ids = set(server_data.get("non_circle_ids", []))
        all_valid_ids = circle_ids.union(non_circle_ids)

        # Deduplicate selections to prevent score inflation
        unique_selections = set(selected_ids)

        for s_id in unique_selections:
            if s_id not in all_valid_ids:
                raise HTTPException(status_code=400, detail=f"Invalid shape ID '{s_id}' does not belong to the grid.")

        correct_circles_selected = len(unique_selections.intersection(circle_ids))
        incorrect_non_circle_selections = len(unique_selections.intersection(non_circle_ids))
        total_circles = len(circle_ids)
        total_non_circles = len(non_circle_ids)
        circles_missed = total_circles - correct_circles_selected

        target_detection_rate = round((correct_circles_selected / total_circles) * 100.0, 2) if total_circles > 0 else 0.0
        false_selection_rate = round((incorrect_non_circle_selections / total_non_circles) * 100.0, 2) if total_non_circles > 0 else 0.0

        return {
            "correct_circles_selected": correct_circles_selected,
            "circles_missed": circles_missed,
            "incorrect_non_circle_selections": incorrect_non_circle_selections,
            "total_circles": total_circles,
            "total_non_circles": total_non_circles,
            "target_detection_rate": target_detection_rate,
            "false_selection_rate": false_selection_rate,
            "completion_time_ms": completion_time_ms,
            "difficulty": server_data.get("difficulty", "medium"),
            "task_version": "v1.0"
        }

    @staticmethod
    def score_calculation_recall(
        server_data: Dict[str, Any],
        calculation_answers: List[Any],
        recalled_words: List[str],
        calculation_time_ms: int = None,
        word_recall_delay_seconds: float = None,
        total_time_ms: int = None
    ) -> Dict[str, Any]:
        """
        Calculates independent scores for:
        Part A: Arithmetic accuracy
        Part B: Delayed word recognition
        """
        calc_answer_key = server_data.get("calculation_answer_key", {})
        target_words = set(server_data.get("target_words", []))
        recall_pool = set(server_data.get("recall_word_choices", []))

        # Part A: Calculation
        questions_attempted = len(calculation_answers)
        correct_calc_answers = 0

        for ans in calculation_answers:
            q_id = getattr(ans, "question_id", None) or ans.get("question_id")
            val = getattr(ans, "selected_answer", None) if hasattr(ans, "selected_answer") else ans.get("selected_answer")

            if q_id not in calc_answer_key:
                raise HTTPException(status_code=400, detail=f"Question ID '{q_id}' does not belong to this attempt.")

            if val == calc_answer_key[q_id]:
                correct_calc_answers += 1

        calculation_accuracy = (
            round((correct_calc_answers / questions_attempted) * 100.0, 2)
            if questions_attempted > 0 else 0.0
        )

        # Part B: Word Recall
        unique_recalled = set(recalled_words)
        for w in unique_recalled:
            if w not in recall_pool:
                raise HTTPException(status_code=400, detail=f"Recalled word '{w}' was not in the provided choice pool.")

        correct_original_words = len(unique_recalled.intersection(target_words))
        total_original_words = len(target_words)
        missed_words = total_original_words - correct_original_words
        false_positive_selections = len(unique_recalled - target_words)

        word_recall_accuracy = (
            round((correct_original_words / total_original_words) * 100.0, 2)
            if total_original_words > 0 else 0.0
        )

        return {
            "calculation": {
                "correct_answers": correct_calc_answers,
                "incorrect_answers": questions_attempted - correct_calc_answers,
                "questions_attempted": questions_attempted,
                "calculation_accuracy": calculation_accuracy,
                "completion_time_ms": calculation_time_ms,
            },
            "word_recall": {
                "task_name": "delayed_word_recognition",
                "correct_words": correct_original_words,
                "total_words": total_original_words,
                "missed_words": missed_words,
                "false_positive_selections": false_positive_selections,
                "word_recall_accuracy": word_recall_accuracy,
                "actual_delay_seconds": word_recall_delay_seconds,
            },
            "total_completion_time_ms": total_time_ms,
            "difficulty": server_data.get("difficulty", "medium"),
            "task_version": "v1.0"
        }

    @staticmethod
    def score_shape_recognition(
        server_data: Dict[str, Any],
        answers: List[Any],
        completion_time_ms: int = None
    ) -> Dict[str, Any]:
        """
        Calculates accuracy for Shape Recognition and Spatial Reasoning.
        """
        answer_key = server_data.get("answer_key", {})
        total_questions = len(answer_key)
        correct_answers = 0

        for ans in answers:
            q_id = getattr(ans, "question_id", None) or ans.get("question_id")
            selected_opt = getattr(ans, "selected_option_id", None) if hasattr(ans, "selected_option_id") else ans.get("selected_option_id")

            if q_id not in answer_key:
                raise HTTPException(status_code=400, detail=f"Question ID '{q_id}' does not belong to this attempt.")

            if selected_opt == answer_key[q_id]:
                correct_answers += 1

        incorrect_answers = total_questions - correct_answers
        shape_accuracy = (
            round((correct_answers / total_questions) * 100.0, 2)
            if total_questions > 0 else 0.0
        )

        return {
            "correct_answers": correct_answers,
            "incorrect_answers": incorrect_answers,
            "total_questions": total_questions,
            "shape_accuracy": shape_accuracy,
            "completion_time_ms": completion_time_ms,
            "difficulty": server_data.get("difficulty", "medium"),
            "task_version": "v1.0"
        }
