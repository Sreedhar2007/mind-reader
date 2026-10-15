"""
Integration tests for app.py routes and API endpoints.
Tests page rendering and API workflows using Flask's test client.
"""

import unittest
from app import app
import database


class TestAppRoutes(unittest.TestCase):
    def setUp(self):
        """Set up Flask test client with testing mode."""
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_pages_render_successfully(self):
        """Verify all HTML template pages return HTTP 200 OK."""
        for path in ["/", "/game", "/statistics", "/about"]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, f"Failed for path {path}")
            self.assertIn(b"Mind Reader", response.data)

    def test_full_game_api_flow(self):
        """Test complete session, predict, and submit round flow."""
        # 1. Start Session
        start_res = self.client.post("/api/start-session", json={"player_name": "TestUser", "game_mode": "classic"})
        self.assertEqual(start_res.status_code, 200)
        start_data = start_res.get_json()
        self.assertTrue(start_data["success"])
        session_id = start_data["session_id"]

        # 2. Request Prediction (Fair protocol - no actual choice sent)
        pred_res = self.client.post("/api/predict", json={"session_id": session_id})
        self.assertEqual(pred_res.status_code, 200)
        pred_data = pred_res.get_json()
        self.assertTrue(pred_data["success"])
        predicted = pred_data["predicted_choice"]
        self.assertIn("confidence_percent", pred_data)
        self.assertIn("explanation", pred_data)

        # 3. Submit Round
        submit_res = self.client.post("/api/submit-round", json={"session_id": session_id, "actual_choice": predicted})
        self.assertEqual(submit_res.status_code, 200)
        submit_data = submit_res.get_json()
        self.assertTrue(submit_data["success"])
        self.assertTrue(submit_data["is_correct"])
        self.assertEqual(submit_data["total_score"], 10)

        # 4. Fetch Statistics
        stats_res = self.client.get("/api/statistics")
        self.assertEqual(stats_res.status_code, 200)
        stats_data = stats_res.get_json()
        self.assertTrue(stats_data["success"])
        self.assertIn("statistics", stats_data)
        self.assertIn("benchmark", stats_data)

        # 5. Math Trick Endpoint
        math_res = self.client.post("/api/math-trick", json={"secret_number": 42})
        self.assertEqual(math_res.status_code, 200)
        math_data = math_res.get_json()
        self.assertTrue(math_data["success"])
        self.assertEqual(math_data["final_result"], 7)

    def test_invalid_requests_handled(self):
        """Verify invalid requests return appropriate client errors."""
        # Missing session_id on predict
        res = self.client.post("/api/predict", json={})
        self.assertEqual(res.status_code, 400)

        # Submitting round with non-existent session
        res = self.client.post("/api/submit-round", json={"session_id": 999999, "actual_choice": 5})
        self.assertEqual(res.status_code, 400)

    def test_interrogator_api_flow(self):
        """Verify Mode E Interrogator start and answer endpoints."""
        start_res = self.client.post("/api/interrogator/start", json={"min_val": 1, "max_val": 30})
        self.assertEqual(start_res.status_code, 200)
        data = start_res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["candidates"]), 30)
        self.assertIn("current_question", data)

        # Answer question
        q_key = data["current_question"]["key"]
        ans_res = self.client.post(
            "/api/interrogator/answer",
            json={
                "candidates": data["candidates"],
                "question_key": q_key,
                "answer_yes": True,
                "history": [],
            },
        )
        self.assertEqual(ans_res.status_code, 200)
        ans_data = ans_res.get_json()
        self.assertTrue(ans_data["success"])
        self.assertLess(len(ans_data["candidates"]), 30)


if __name__ == "__main__":
    unittest.main()
