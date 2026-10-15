"""
Unit tests for game_logic.py module.
Tests session creation, fair prediction lifecycle, scoring rules,
streak calculation, input validation, and mathematical mind trick algebra.
"""

import os
import tempfile
import unittest
import database
from game_logic import GameEngine


class TestGameLogicModule(unittest.TestCase):
    def setUp(self):
        """Create an isolated test database for session operations."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_game_engine.db")
        database.init_db(self.db_path)

    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()

    def test_start_session(self):
        """Verify starting session creates player and session record."""
        session_info = GameEngine.start_session("Player1", "classic", db_path=self.db_path)
        self.assertIn("session_id", session_info)
        self.assertEqual(session_info["score"], 0)
        self.assertEqual(session_info["game_mode"], "classic")

    def test_fair_prediction_lifecycle(self):
        """Verify fair two-phase protocol: predict first, then submit actual choice."""
        session_info = GameEngine.start_session("Player2", "classic", db_path=self.db_path)
        session_id = session_info["session_id"]

        # Step 1: AI generates prediction prior to player revealing choice
        pred = GameEngine.generate_prediction(session_id, db_path=self.db_path)
        self.assertIn("predicted_choice", pred)
        self.assertTrue(pred["prediction_locked"])
        predicted = pred["predicted_choice"]

        # Step 2: Player reveals choice (matching the prediction)
        round_res = GameEngine.submit_round(session_id, actual_choice=predicted, db_path=self.db_path)
        self.assertTrue(round_res["is_correct"])
        self.assertEqual(round_res["points_earned"], 10)
        self.assertEqual(round_res["total_score"], 10)
        self.assertEqual(round_res["current_streak"], 1)

    def test_cannot_submit_without_pending_prediction(self):
        """Verify submission fails if no prediction was generated first."""
        session_info = GameEngine.start_session("Player3", "classic", db_path=self.db_path)
        session_id = session_info["session_id"]

        with self.assertRaises(ValueError):
            GameEngine.submit_round(session_id, actual_choice=5, db_path=self.db_path)

    def test_invalid_choice_range_rejected(self):
        """Verify choices outside mode bounds are rejected with ValueError."""
        session_info = GameEngine.start_session("Player4", "classic", db_path=self.db_path)
        session_id = session_info["session_id"]

        GameEngine.generate_prediction(session_id, db_path=self.db_path)

        with self.assertRaises(ValueError):
            GameEngine.submit_round(session_id, actual_choice=999, db_path=self.db_path)

    def test_math_trick_invariant(self):
        """Verify mathematical mind trick always yields 7 regardless of chosen input."""
        for num in [1, 23, 77, 100, 999]:
            trick = GameEngine.solve_math_trick(num)
            self.assertEqual(trick["final_result"], 7)
            self.assertIn("pedagogical_lesson", trick)
            self.assertEqual(len(trick["steps"]), 5)

    def test_interrogator_convergence(self):
        """Verify Decision Tree interrogator reliably converges to secret number."""
        from game_logic import DecisionTreeInterrogator, PRIMES_UNDER_50, SQUARES

        def evaluate_predicate_test(num: int, key: str) -> bool:
            if key == "is_even":
                return num % 2 == 0
            if key == "mult_3":
                return num % 3 == 0
            if key == "mult_5":
                return num % 5 == 0
            if key == "is_prime":
                return num in PRIMES_UNDER_50
            if key == "is_square":
                return num in SQUARES
            if key == "single_digit":
                return num < 10
            if key.startswith("gt_"):
                return num > int(key.split("_")[1])
            if key.startswith("is_"):
                return num == int(key.split("_")[1])
            return True

        for secret in [3, 14, 22, 29]:
            state = DecisionTreeInterrogator.start_game(min_val=1, max_val=30)
            candidates = state["candidates"]
            history = []

            for _ in range(7):  # At most 5-6 questions needed
                if state.get("game_over"):
                    break
                q_key = state["current_question"]["key"]
                answer = evaluate_predicate_test(secret, q_key)
                state = DecisionTreeInterrogator.answer_question(
                    candidates=candidates,
                    question_key=q_key,
                    answer_yes=answer,
                    history=history,
                )
                candidates = state["candidates"]
                history = state["history"]

            self.assertTrue(state.get("game_over"))
            self.assertEqual(state.get("secret_number"), secret)


if __name__ == "__main__":
    unittest.main()
