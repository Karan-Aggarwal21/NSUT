import random
import uuid
from typing import Dict, Any, List

OBJECT_POOL = [
    {"id": "apple", "name": "Apple", "icon": "apple"},
    {"id": "book", "name": "Book", "icon": "book"},
    {"id": "key", "name": "Key", "icon": "key"},
    {"id": "cup", "name": "Cup", "icon": "cup"},
    {"id": "ball", "name": "Ball", "icon": "ball"},
    {"id": "spoon", "name": "Spoon", "icon": "spoon"},
    {"id": "clock", "name": "Clock", "icon": "clock"},
    {"id": "shoe", "name": "Shoe", "icon": "shoe"},
    {"id": "flower", "name": "Flower", "icon": "flower"},
    {"id": "comb", "name": "Comb", "icon": "comb"},
]

WORD_POOL = [
    "Apple", "House", "River", "Chair", "Flower", "Key",
    "Window", "Table", "Bread", "Garden", "Clock", "Book"
]

SHAPES_POOL = ["circle", "square", "triangle", "rectangle"]


class TaskGenerator:
    @staticmethod
    def generate_object_memory_task(difficulty: str = "medium") -> Dict[str, Any]:
        """
        Generates Object Sequence Memory Task.
        Easy: 3 objects, 2500ms duration per object
        Medium: 4 objects, 2000ms duration per object
        Advanced: 5 objects, 2000ms duration per object
        """
        count_map = {"easy": 3, "medium": 4, "advanced": 5}
        duration_map = {"easy": 2500, "medium": 2000, "advanced": 2000}

        num_objects = count_map.get(difficulty, 4)
        duration_ms = duration_map.get(difficulty, 2000)

        # Select distinct objects
        selected = random.sample(OBJECT_POOL, num_objects)
        sequence_ids = [obj["id"] for obj in selected]

        # Shuffled objects for reconstruction screen
        shuffled = list(selected)
        while shuffled == selected and len(selected) > 1:
            random.shuffle(shuffled)

        client_data = {
            "presentation_items": selected,
            "shuffled_choices": shuffled,
            "presentation_duration_ms": duration_ms,
            "num_objects": num_objects,
        }

        server_data = {
            "correct_sequence": sequence_ids,
            "difficulty": difficulty,
            "num_objects": num_objects,
            "presentation_duration_ms": duration_ms,
        }

        return {"client_data": client_data, "server_data": server_data}

    @staticmethod
    def generate_circle_search_task(difficulty: str = "medium") -> Dict[str, Any]:
        """
        Generates Circle Search grid.
        Easy: 3x3 (9 cells), 3-4 circles
        Medium: 4x4 (16 cells), 5-7 circles
        Advanced: 5x5 (25 cells), 7-10 circles
        """
        grid_config = {
            "easy": {"size": 3, "circles": random.randint(3, 4)},
            "medium": {"size": 4, "circles": random.randint(5, 7)},
            "advanced": {"size": 5, "circles": random.randint(7, 10)},
        }
        cfg = grid_config.get(difficulty, grid_config["medium"])
        size = cfg["size"]
        num_circles = cfg["circles"]
        total_cells = size * size

        cell_indices = list(range(total_cells))
        circle_indices = set(random.sample(cell_indices, num_circles))

        distractors = ["square", "triangle", "rectangle"]
        grid_items = []
        circle_ids = []
        non_circle_ids = []

        for idx in range(total_cells):
            row = idx // size
            col = idx % size
            cell_id = f"cell_{row}_{col}"

            if idx in circle_indices:
                shape = "circle"
                circle_ids.append(cell_id)
            else:
                shape = random.choice(distractors)
                non_circle_ids.append(cell_id)

            grid_items.append({
                "id": cell_id,
                "shape": shape,
                "row": row,
                "col": col,
            })

        client_data = {
            "grid_size": size,
            "grid_items": grid_items,
            "total_items": total_cells,
        }

        server_data = {
            "circle_ids": circle_ids,
            "non_circle_ids": non_circle_ids,
            "total_circles": len(circle_ids),
            "total_non_circles": len(non_circle_ids),
            "difficulty": difficulty,
        }

        return {"client_data": client_data, "server_data": server_data}

    @staticmethod
    def generate_calculation_recall_task(difficulty: str = "medium") -> Dict[str, Any]:
        """
        Part A: 6 simple arithmetic questions
        Part B: 3 target words presented first, 6 word cards for delayed recognition
        """
        # Word Recall task setup
        sample_words = random.sample(WORD_POOL, 6)
        target_words = sample_words[:3]
        recall_pool = list(sample_words)
        random.shuffle(recall_pool)

        # 6 Arithmetic questions
        questions = []
        answer_key = {}

        operations = ["+", "-"]
        for i in range(6):
            q_id = f"calc_q_{i + 1}"
            op = random.choice(operations)
            if difficulty == "easy":
                if op == "+":
                    a = random.randint(1, 4)
                    b = random.randint(1, 3)
                    ans = a + b
                else:
                    ans = random.randint(1, 3)
                    b = random.randint(1, 3)
                    a = ans + b
            else:
                if op == "+":
                    a = random.randint(2, 6)
                    b = random.randint(2, 5)
                    ans = a + b
                else:
                    ans = random.randint(2, 5)
                    b = random.randint(2, 5)
                    a = ans + b

            # Generate 3 multiple choice options
            options = {ans}
            while len(options) < 3:
                offset = random.choice([-2, -1, 1, 2, 3])
                candidate = ans + offset
                if candidate >= 0:
                    options.add(candidate)
            options_list = sorted(list(options))

            questions.append({
                "id": q_id,
                "text": f"{a} {op} {b} = ?",
                "options": options_list
            })
            answer_key[q_id] = ans

        client_data = {
            "words_to_present": target_words,
            "calculation_questions": questions,
            "recall_word_choices": recall_pool,
            "presentation_duration_ms": 3000,
        }

        server_data = {
            "target_words": target_words,
            "calculation_answer_key": answer_key,
            "recall_word_choices": recall_pool,
            "difficulty": difficulty,
        }

        return {"client_data": client_data, "server_data": server_data}

    @staticmethod
    def generate_shape_recognition_task(difficulty: str = "medium") -> Dict[str, Any]:
        """
        Mode A: Match single shape
        Mode B: Match pattern sequence
        Easy: 4 questions (Mode A)
        Medium: 5 questions (2 Mode A, 3 Mode B)
        Advanced: 5 questions (Mode B with 3-4 shape sequence)
        """
        questions = []
        answer_key = {}

        if difficulty == "easy":
            modes = ["A", "A", "A", "A"]
        elif difficulty == "medium":
            modes = ["A", "A", "B", "B", "B"]
        else:
            modes = ["B", "B", "B", "B", "B"]

        for idx, mode in enumerate(modes):
            q_id = f"shape_q_{idx + 1}"
            if mode == "A":
                # Single shape match
                target_shape = random.choice(SHAPES_POOL)
                other_shapes = [s for s in SHAPES_POOL if s != target_shape]
                distractor_shapes = random.sample(other_shapes, 2)
                options = [
                    {"id": "opt_correct", "shape": target_shape},
                    {"id": "opt_distract_1", "shape": distractor_shapes[0]},
                    {"id": "opt_distract_2", "shape": distractor_shapes[1]},
                ]
                random.shuffle(options)
                correct_opt_id = next(opt["id"] for opt in options if opt["shape"] == target_shape)

                questions.append({
                    "id": q_id,
                    "mode": "shape_match",
                    "instruction": "Look at the target shape. Choose the matching shape below:",
                    "target": target_shape,
                    "options": options,
                })
                answer_key[q_id] = correct_opt_id
            else:
                # Pattern match
                target_seq = random.sample(SHAPES_POOL, 3)
                # Create permutations for distractors
                distractor_seq_1 = [target_seq[0], target_seq[2], target_seq[1]]
                distractor_seq_2 = [target_seq[1], target_seq[0], target_seq[2]]

                options = [
                    {"id": "opt_correct", "pattern": target_seq},
                    {"id": "opt_distract_1", "pattern": distractor_seq_1},
                    {"id": "opt_distract_2", "pattern": distractor_seq_2},
                ]
                random.shuffle(options)
                correct_opt_id = next(opt["id"] for opt in options if opt["pattern"] == target_seq)

                questions.append({
                    "id": q_id,
                    "mode": "pattern_match",
                    "instruction": "Look at the target pattern. Choose the matching row below:",
                    "target_pattern": target_seq,
                    "options": options,
                })
                answer_key[q_id] = correct_opt_id

        client_data = {
            "questions": questions,
            "total_questions": len(questions),
        }

        server_data = {
            "answer_key": answer_key,
            "difficulty": difficulty,
            "total_questions": len(questions),
        }

        return {"client_data": client_data, "server_data": server_data}
