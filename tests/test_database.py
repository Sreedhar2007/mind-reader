"""
Unit tests for database.py module.
Verifies table creation, player CRUD, session tracking, round recording,
and accurate statistic calculations without division by zero.
"""

import os
import tempfile
import unittest
import database


class TestDatabaseModule(unittest.TestCase):
    def setUp(self):
        """Create a temporary SQLite database for test isolation."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_mind_reader.db")
        database.init_db(self.db_path)

    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()

    def test_init_db_creates_tables(self):
        """Verify database tables and indexes exist."""
        with database.get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row["name"] for row in cursor.fetchall()]
            self.assertIn("players", tables)
            self.assertIn("game_sessions", tables)
            self.assertIn("game_rounds", tables)

    def test_get_or_create_player(self):
        """Verify player creation and retrieval."""
        player1 = database.get_or_create_player("Alice", db_path=self.db_path)
        self.assertIsNotNone(player1["id"])
        self.assertEqual(player1["display_name"], "Alice")

        # Second call with same name should return existing player
        player2 = database.get_or_create_player("Alice", db_path=self.db_path)
        self.assertEqual(player1["id"], player2["id"])

    def test_create_and_update_session(self):
        """Verify session creation and score updates."""
        player = database.get_or_create_player("Bob", db_path=self.db_path)
        session_id = database.create_session(player["id"], "classic", db_path=self.db_path)
        self.assertIsInstance(session_id, int)

        session = database.get_session(session_id, db_path=self.db_path)
        self.assertEqual(session["score"], 0)
        self.assertEqual(session["current_streak"], 0)

        # Update session
        updated = database.update_session(session_id, score=25, current_streak=2, max_streak=2, ended=False, db_path=self.db_path)
        self.assertTrue(updated)

        updated_session = database.get_session(session_id, db_path=self.db_path)
        self.assertEqual(updated_session["score"], 25)
        self.assertEqual(updated_session["current_streak"], 2)

    def test_record_and_retrieve_rounds(self):
        """Verify recording rounds and retrieving session history."""
        player = database.get_or_create_player("Charlie", db_path=self.db_path)
        session_id = database.create_session(player["id"], "pattern", db_path=self.db_path)

        round_id = database.record_round(
            session_id=session_id,
            round_number=1,
            previous_choices="[3, 4]",
            predicted_choice=5,
            actual_choice=5,
            prediction_correct=True,
            confidence=0.65,
            explanation="Test sequential pattern",
            db_path=self.db_path,
        )
        self.assertIsInstance(round_id, int)

        rounds = database.get_session_rounds(session_id, db_path=self.db_path)
        self.assertEqual(len(rounds), 1)
        self.assertEqual(rounds[0]["predicted_choice"], 5)
        self.assertEqual(rounds[0]["actual_choice"], 5)
        self.assertEqual(rounds[0]["prediction_correct"], 1)

    def test_empty_statistics_handles_zero_gracefully(self):
        """Verify statistics calculation does not fail or divide by zero when empty."""
        stats = database.get_overall_statistics(db_path=self.db_path)
        self.assertEqual(stats["total_rounds"], 0)
        self.assertEqual(stats["correct_predictions"], 0)
        self.assertEqual(stats["incorrect_predictions"], 0)
        self.assertIsNone(stats["accuracy_rate"])

    def test_accuracy_calculation(self):
        """Verify accuracy percentage is accurately calculated."""
        player = database.get_or_create_player("Diana", db_path=self.db_path)
        session_id = database.create_session(player["id"], "classic", db_path=self.db_path)

        # Record 3 correct and 1 incorrect rounds
        database.record_round(session_id, 1, "[]", 7, 7, True, 0.5, "corr", db_path=self.db_path)
        database.record_round(session_id, 2, "[7]", 8, 8, True, 0.6, "corr", db_path=self.db_path)
        database.record_round(session_id, 3, "[7, 8]", 9, 9, True, 0.7, "corr", db_path=self.db_path)
        database.record_round(session_id, 4, "[7, 8, 9]", 10, 1, False, 0.4, "incorr", db_path=self.db_path)

        stats = database.get_overall_statistics(db_path=self.db_path)
        self.assertEqual(stats["total_rounds"], 4)
        self.assertEqual(stats["correct_predictions"], 3)
        self.assertEqual(stats["incorrect_predictions"], 1)
        self.assertEqual(stats["accuracy_rate"], 75.0)


if __name__ == "__main__":
    unittest.main()
