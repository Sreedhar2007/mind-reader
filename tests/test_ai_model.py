"""
Unit tests for ai_model.py module.
Tests feature extraction, synthetic dataset generation,
model predictions, confidence bounds, and explanation logic.
"""

import unittest
import pandas as pd
from ai_model import (
    MindReaderAI,
    extract_features_from_history,
    generate_synthetic_player_dataset,
    FEATURE_COLUMNS,
    ai_service,
)


class TestAIModelModule(unittest.TestCase):
    def test_feature_extraction_empty_history(self):
        """Verify feature extraction with empty history returns numeric defaults."""
        feats = extract_features_from_history([], round_num=1, max_range=10)
        self.assertIsInstance(feats, dict)
        for col in FEATURE_COLUMNS:
            self.assertIn(col, feats)
            self.assertIsInstance(feats[col], (int, float))

    def test_feature_extraction_with_history(self):
        """Verify feature calculations with established history."""
        history = [2, 4, 6]
        feats = extract_features_from_history(history, round_num=4, max_range=10)
        self.assertEqual(feats["prev_1"], 6.0)
        self.assertEqual(feats["prev_2"], 4.0)
        self.assertEqual(feats["prev_3"], 2.0)
        self.assertEqual(feats["diff_1_2"], 2.0)
        self.assertEqual(feats["diff_2_3"], 2.0)
        self.assertEqual(feats["last_is_odd"], 0.0)
        self.assertEqual(feats["recent_mean"], 4.0)

    def test_synthetic_dataset_generation(self):
        """Verify synthetic data generator produces valid rows and columns."""
        df = generate_synthetic_player_dataset(num_sessions=10, rounds_per_session=5, max_range=10)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 20)
        for col in FEATURE_COLUMNS + ["target"]:
            self.assertIn(col, df.columns)
        self.assertTrue((df["target"] >= 1).all() and (df["target"] <= 10).all())

    def test_predict_returns_valid_structure(self):
        """Verify predict returns integer choice, valid confidence, and explanation."""
        pred = ai_service.predict(history=[3, 5, 7], round_num=4, max_range=10)
        self.assertIn("predicted_choice", pred)
        self.assertIn("confidence", pred)
        self.assertIn("confidence_percent", pred)
        self.assertIn("explanation", pred)
        self.assertIn("pattern_detected", pred)

        self.assertIsInstance(pred["predicted_choice"], int)
        self.assertTrue(1 <= pred["predicted_choice"] <= 10)
        self.assertGreaterEqual(pred["confidence"], 0.10)
        self.assertLessEqual(pred["confidence"], 1.0)
        self.assertGreater(len(pred["explanation"]), 10)

    def test_benchmark_metrics(self):
        """Verify benchmark info provides realistic model evaluation results."""
        bench = ai_service.get_benchmark_info()
        self.assertIn("model_type", bench)
        self.assertIn("baseline_type", bench)
        self.assertIn("test_accuracy_percentage", bench)
        self.assertIn("baseline_accuracy_percentage", bench)
        self.assertIn("feature_importances", bench)
        # Accuracy should be positive and reasonable
        self.assertGreater(bench["test_accuracy_percentage"], 0)
        self.assertGreater(bench["baseline_accuracy_percentage"], 0)


if __name__ == "__main__":
    unittest.main()
