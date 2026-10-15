"""
Game Logic module for Mind Reader AI.
Handles game sessions, fair prediction workflows, scoring rules, streak bonuses,
input validation, and the pedagogical Mathematical Mind Trick.
"""

import json
from typing import Any, Dict, List, Optional, Tuple
import database
from ai_model import ai_service

# Mode configurations
MODE_CONFIGS = {
    "classic": {
        "name": "Classic Number Prediction",
        "min_val": 1,
        "max_val": 10,
        "base_points": 10,
        "streak_bonus_interval": 3,
        "streak_bonus_points": 5,
        "description": "Pick a secret number from 1 to 10. AI predicts before you reveal!",
    },
    "pattern": {
        "name": "Pattern Learning Challenge",
        "min_val": 1,
        "max_val": 10,
        "base_points": 10,
        "streak_bonus_interval": 3,
        "streak_bonus_points": 5,
        "description": "Enter sequences of numbers. See how quickly the AI recognizes your habits.",
    },
    "expert": {
        "name": "Expert Challenge",
        "min_val": 1,
        "max_val": 25,
        "base_points": 25,
        "streak_bonus_interval": 2,
        "streak_bonus_points": 15,
        "description": "Expanded 1 to 25 range. Baseline chance drops to 4%, testing advanced pattern analysis.",
    },
    "math": {
        "name": "Mathematical Mind Trick",
        "description": "A guided arithmetic puzzle that reveals invariant mathematical principles vs AI.",
    },
    "interrogator": {
        "name": "Decision Tree Interrogator",
        "min_val": 1,
        "max_val": 30,
        "description": "Think of any number from 1 to 30. The AI asks Yes/No questions to deduce your number using Information Gain!",
    },
}

# In-memory storage for pending round predictions (session_id -> prediction dict)
# Ensures predictions CANNOT be altered and are made prior to choice submission
_pending_predictions: Dict[int, Dict[str, Any]] = {}


class GameEngine:
    """Manages game sessions, round transitions, and scoring."""

    @staticmethod
    def start_session(display_name: str = "Player", game_mode: str = "classic", db_path: Optional[str] = None) -> Dict[str, Any]:
        """Initialize player and game session."""
        if game_mode not in MODE_CONFIGS:
            game_mode = "classic"

        player = database.get_or_create_player(display_name, db_path=db_path)
        session_id = database.create_session(player["id"], game_mode, db_path=db_path)

        # Clear any old pending prediction for this session
        if session_id in _pending_predictions:
            del _pending_predictions[session_id]

        return {
            "session_id": session_id,
            "player_id": player["id"],
            "player_name": player["display_name"],
            "game_mode": game_mode,
            "mode_info": MODE_CONFIGS[game_mode],
            "score": 0,
            "current_streak": 0,
            "max_streak": 0,
        }

    @staticmethod
    def get_history_for_session(session_id: int, db_path: Optional[str] = None) -> List[int]:
        """Extract sequence of actual choices made so far in the session."""
        rounds = database.get_session_rounds(session_id, db_path=db_path)
        return [r["actual_choice"] for r in rounds if r["actual_choice"] is not None]

    @staticmethod
    def generate_prediction(session_id: int, db_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a fair prediction from session history before the player reveals their choice.
        The predicted choice is cached on the server to prevent tamper or retroactive guessing.
        """
        session = database.get_session(session_id, db_path=db_path)
        if not session:
            raise ValueError(f"Session {session_id} not found.")

        game_mode = session.get("game_mode", "classic")
        config = MODE_CONFIGS.get(game_mode, MODE_CONFIGS["classic"])
        max_val = config.get("max_val", 10)

        history = GameEngine.get_history_for_session(session_id, db_path=db_path)
        round_num = len(history) + 1

        prediction = ai_service.predict(history=history, round_num=round_num, max_range=max_val)

        # Cache pending prediction on server
        _pending_predictions[session_id] = {
            "round_number": round_num,
            "predicted_choice": prediction["predicted_choice"],
            "confidence": prediction["confidence"],
            "confidence_percent": prediction["confidence_percent"],
            "explanation": prediction["explanation"],
            "pattern_detected": prediction["pattern_detected"],
            "history_used": history.copy(),
        }

        # Return prediction details to frontend
        return {
            "round_number": round_num,
            "predicted_choice": prediction["predicted_choice"],
            "confidence_percent": prediction["confidence_percent"],
            "explanation": prediction["explanation"],
            "pattern_detected": prediction["pattern_detected"],
            "history_used": history[-5:],
            "is_confident": prediction["is_confident"],
            "prediction_locked": True,
        }

    @staticmethod
    def submit_round(session_id: int, actual_choice: int, db_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Evaluate player's revealed choice against the pre-locked AI prediction.
        Computes score, updates streaks, and commits to SQLite.
        """
        session = database.get_session(session_id, db_path=db_path)
        if not session:
            raise ValueError(f"Session {session_id} not found.")

        # Ensure a prediction was generated before this submission
        pending = _pending_predictions.get(session_id)
        if not pending:
            raise ValueError("No prediction is currently locked for this session. Request a prediction first.")

        game_mode = session.get("game_mode", "classic")
        config = MODE_CONFIGS.get(game_mode, MODE_CONFIGS["classic"])
        min_val = config.get("min_val", 1)
        max_val = config.get("max_val", 10)

        # Validate range
        if not (min_val <= actual_choice <= max_val):
            raise ValueError(f"Choice must be an integer between {min_val} and {max_val}.")

        predicted_choice = pending["predicted_choice"]
        is_correct = (predicted_choice == actual_choice)
        round_number = pending["round_number"]
        previous_choices_str = json.dumps(pending["history_used"])

        # Calculate scoring
        current_score = session.get("score", 0)
        current_streak = session.get("current_streak", 0)
        max_streak = session.get("max_streak", 0)

        points_earned = 0
        bonus_awarded = 0

        if is_correct:
            points_earned = config.get("base_points", 10)
            current_streak += 1
            if current_streak > max_streak:
                max_streak = current_streak

            # Streak bonus
            bonus_interval = config.get("streak_bonus_interval", 3)
            bonus_pts = config.get("streak_bonus_points", 5)
            if current_streak % bonus_interval == 0:
                bonus_awarded = bonus_pts
                points_earned += bonus_pts
        else:
            current_streak = 0

        new_total_score = current_score + points_earned

        # Persist round to database
        database.record_round(
            session_id=session_id,
            round_number=round_number,
            previous_choices=previous_choices_str,
            predicted_choice=predicted_choice,
            actual_choice=actual_choice,
            prediction_correct=is_correct,
            confidence=pending["confidence"],
            explanation=pending["explanation"],
            db_path=db_path,
        )

        # Update session state in database
        database.update_session(
            session_id=session_id,
            score=new_total_score,
            current_streak=current_streak,
            max_streak=max_streak,
            ended=False,
            db_path=db_path,
        )

        # Clear pending prediction now that round has resolved
        del _pending_predictions[session_id]

        return {
            "round_number": round_number,
            "predicted_choice": predicted_choice,
            "actual_choice": actual_choice,
            "is_correct": is_correct,
            "points_earned": points_earned,
            "bonus_awarded": bonus_awarded,
            "total_score": new_total_score,
            "current_streak": current_streak,
            "max_streak": max_streak,
            "confidence_percent": pending["confidence_percent"],
            "explanation": pending["explanation"],
            "pattern_detected": pending["pattern_detected"],
        }

    @staticmethod
    def reset_session(session_id: int, db_path: Optional[str] = None) -> Dict[str, Any]:
        """Reset score and streak for the current session."""
        session = database.get_session(session_id, db_path=db_path)
        if not session:
            raise ValueError(f"Session {session_id} not found.")

        database.update_session(session_id, score=0, current_streak=0, max_streak=session.get("max_streak", 0), db_path=db_path)
        if session_id in _pending_predictions:
            del _pending_predictions[session_id]

        return {"message": "Session reset successfully", "session_id": session_id, "score": 0, "current_streak": 0}

    @staticmethod
    def solve_math_trick(secret_number: int) -> Dict[str, Any]:
        """
        Pedagogical step-by-step solver for the Mathematical Mind Trick.
        Algebraic invariant: ((2x + 14) / 2) - x = 7.
        """
        x = int(secret_number)
        step1 = x
        step2 = x * 2
        step3 = step2 + 14
        step4 = step3 // 2
        step5 = step4 - x

        return {
            "original_number": x,
            "steps": [
                {"step": 1, "description": f"You picked secret number: {x}"},
                {"step": 2, "description": f"Multiply by 2: {x} × 2 = {step2}"},
                {"step": 3, "description": f"Add 14: {step2} + 14 = {step3}"},
                {"step": 4, "description": f"Divide by 2: {step3} ÷ 2 = {step4}"},
                {"step": 5, "description": f"Subtract your original number ({x}): {step4} - {x} = {step5}"},
            ],
            "final_result": step5,
            "algebraic_proof": "((2x + 14) / 2) - x = (2x/2 + 14/2) - x = x + 7 - x = 7",
            "pedagogical_lesson": "Why this is NOT Artificial Intelligence: This trick is a deterministic algebraic invariant that always yields 7 regardless of x. Unlike mathematics where rules guarantee an exact outcome, Machine Learning is inductive and probabilistic, making predictions based on noisy human patterns.",
        }


# =========================================================
# Mode E: Decision Tree Interrogator (20-Questions AI)
# =========================================================

PRIMES_UNDER_100 = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97}
PRIMES_UNDER_50 = PRIMES_UNDER_100
SQUARES = {1, 4, 9, 16, 25, 36, 49, 64, 81, 100}


class DecisionTreeInterrogator:
    """
    Simulates a 20-Questions Binary Decision Tree classifier.
    Calculates Shannon Entropy and Information Gain to select optimal
    questions that halve the search space at every step.
    """

    @staticmethod
    def calculate_entropy(candidate_count: int) -> float:
        """Calculate Shannon entropy for a uniform distribution over candidate_count items."""
        import math
        if candidate_count <= 1:
            return 0.0
        return round(math.log2(candidate_count), 2)

    @staticmethod
    def start_game(min_val: int = 1, max_val: int = 30) -> Dict[str, Any]:
        """Start a new interrogator session with a full candidate pool."""
        candidates = list(range(min_val, max_val + 1))
        initial_entropy = DecisionTreeInterrogator.calculate_entropy(len(candidates))

        next_q = DecisionTreeInterrogator.select_best_question(candidates, asked_keys=[])

        return {
            "min_val": min_val,
            "max_val": max_val,
            "candidates": candidates,
            "total_candidates": len(candidates),
            "remaining_count": len(candidates),
            "entropy": initial_entropy,
            "question_number": 1,
            "current_question": next_q,
            "history": [],
            "game_over": False,
        }

    @staticmethod
    def select_best_question(candidates: List[int], asked_keys: List[str]) -> Optional[Dict[str, Any]]:
        """
        Evaluate candidate questions using Information Gain / 50-50 binary split balancing.
        """
        if len(candidates) <= 1:
            return None

        # If exactly 2 candidates remain, ask direct equality question
        if len(candidates) == 2:
            c1 = candidates[0]
            return {
                "key": f"is_{c1}",
                "text": f"Is your secret number {c1}?",
                "info_gain": 1.0,
                "split_ratio": "50% / 50%",
            }

        q_pool = []

        # 1. Parity
        if "is_even" not in asked_keys:
            q_pool.append({
                "key": "is_even",
                "text": "Is your secret number an EVEN number?",
                "test": lambda x: x % 2 == 0,
                "priority": 10,
            })

        # 2. Divisibility by 3
        if "mult_3" not in asked_keys:
            q_pool.append({
                "key": "mult_3",
                "text": "Is your secret number a MULTIPLE OF 3?",
                "test": lambda x: x % 3 == 0,
                "priority": 8,
            })

        # 3. Divisibility by 5
        if "mult_5" not in asked_keys:
            q_pool.append({
                "key": "mult_5",
                "text": "Is your secret number a MULTIPLE OF 5?",
                "test": lambda x: x % 5 == 0,
                "priority": 8,
            })

        # 4. Primes
        if "is_prime" not in asked_keys:
            q_pool.append({
                "key": "is_prime",
                "text": "Is your secret number a PRIME number (e.g. 2, 3, 5, 7, 11, 13, 17, 19...)?",
                "test": lambda x: x in PRIMES_UNDER_100,
                "priority": 9,
            })

        # Divisibility by 10 (for larger domains)
        if "mult_10" not in asked_keys and max(candidates) > 30:
            q_pool.append({
                "key": "mult_10",
                "text": "Is your secret number a MULTIPLE OF 10 (e.g. 10, 20, 30, 40...)?",
                "test": lambda x: x % 10 == 0,
                "priority": 8,
            })

        # 5. Perfect Square
        if "is_square" not in asked_keys:
            q_pool.append({
                "key": "is_square",
                "text": "Is your secret number a PERFECT SQUARE (e.g. 1, 4, 9, 16, 25)?",
                "test": lambda x: x in SQUARES,
                "priority": 7,
            })

        # 6. Single digit
        if "single_digit" not in asked_keys:
            q_pool.append({
                "key": "single_digit",
                "text": "Is your secret number a SINGLE DIGIT (less than 10)?",
                "test": lambda x: x < 10,
                "priority": 8,
            })

        # 7. Range splits (median partition)
        sorted_c = sorted(candidates)
        median_val = sorted_c[len(sorted_c) // 2]
        gt_key = f"gt_{median_val}"
        if gt_key not in asked_keys:
            q_pool.append({
                "key": gt_key,
                "text": f"Is your secret number GREATER than {median_val}?",
                "test": lambda x, v=median_val: x > v,
                "priority": 6,
            })

        # Additional quartile range splits if needed
        q1_val = sorted_c[len(sorted_c) // 4]
        q1_key = f"gt_{q1_val}"
        if q1_key not in asked_keys and q1_val != median_val:
            q_pool.append({
                "key": q1_key,
                "text": f"Is your secret number GREATER than {q1_val}?",
                "test": lambda x, v=q1_val: x > v,
                "priority": 5,
            })

        q3_val = sorted_c[(3 * len(sorted_c)) // 4]
        q3_key = f"gt_{q3_val}"
        if q3_key not in asked_keys and q3_val != median_val:
            q_pool.append({
                "key": q3_key,
                "text": f"Is your secret number GREATER than {q3_val}?",
                "test": lambda x, v=q3_val: x > v,
                "priority": 5,
            })

        # Score questions based on balance (closest to 50/50 split)
        target_half = len(candidates) / 2.0
        best_q = None
        best_diff = float("inf")
        best_priority = -1

        for q in q_pool:
            yes_count = sum(1 for x in candidates if q["test"](x))
            no_count = len(candidates) - yes_count

            # Discard questions that don't partition candidates (0 information gain)
            if yes_count == 0 or no_count == 0:
                continue

            diff = abs(yes_count - target_half)
            prio = q.get("priority", 0)

            # Pick question closest to 50/50 split, breaking ties with priority
            if diff < best_diff or (diff == best_diff and prio > best_priority):
                best_diff = diff
                best_priority = prio
                yes_pct = round((yes_count / len(candidates)) * 100)
                best_q = {
                    "key": q["key"],
                    "text": q["text"],
                    "split_ratio": f"{yes_pct}% Yes / {100 - yes_pct}% No",
                    "info_gain": round(1.0 - (diff / len(candidates)), 2),
                }

        # Fallback if specific questions exhausted: range split around midpoint
        if not best_q and len(candidates) > 1:
            mid = sorted_c[len(sorted_c) // 2]
            best_q = {
                "key": f"gt_{mid}",
                "text": f"Is your secret number GREATER than {mid}?",
                "split_ratio": "50% / 50%",
                "info_gain": 0.95,
            }

        return best_q

    @staticmethod
    def answer_question(
        candidates: List[int],
        question_key: str,
        answer_yes: bool,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Filter candidates according to user's Yes/No answer and deduce next step."""
        history = history or []

        # Evaluate predicate for the question key
        def evaluate_predicate(num: int, key: str) -> bool:
            if key == "is_even":
                return num % 2 == 0
            if key == "mult_3":
                return num % 3 == 0
            if key == "mult_5":
                return num % 5 == 0
            if key == "mult_10":
                return num % 10 == 0
            if key == "is_prime":
                return num in PRIMES_UNDER_100
            if key == "is_square":
                return num in SQUARES
            if key == "single_digit":
                return num < 10
            if key.startswith("gt_"):
                threshold = int(key.split("_")[1])
                return num > threshold
            if key.startswith("is_"):
                target = int(key.split("_")[1])
                return num == target
            return True

        # Filter candidates
        new_candidates = [
            x for x in candidates
            if evaluate_predicate(x, question_key) == answer_yes
        ]

        # Record history step
        history.append({
            "question_key": question_key,
            "answer": "Yes" if answer_yes else "No",
            "candidates_left": len(new_candidates),
        })

        asked_keys = [h["question_key"] for h in history]
        new_entropy = DecisionTreeInterrogator.calculate_entropy(len(new_candidates))

        # Check if game reached conclusion
        if len(new_candidates) <= 1:
            final_num = new_candidates[0] if new_candidates else None
            return {
                "candidates": new_candidates,
                "remaining_count": len(new_candidates),
                "entropy": 0.0,
                "game_over": True,
                "secret_number": final_num,
                "history": history,
                "decision_tree_explanation": (
                    f"Through {len(history)} binary decision splits, the candidate pool converged "
                    f"from initial entropy to 0.0 bits. The AI has uniquely deduced your secret number: {final_num}!"
                ),
            }

        # Otherwise pick next question
        next_q = DecisionTreeInterrogator.select_best_question(new_candidates, asked_keys)

        return {
            "candidates": new_candidates,
            "remaining_count": len(new_candidates),
            "entropy": new_entropy,
            "game_over": False,
            "current_question": next_q,
            "history": history,
            "question_number": len(history) + 1,
        }
