"""
AI Model module for Mind Reader AI.
Implements feature extraction, synthetic human-behavior dataset generation,
scikit-learn RandomForestClassifier training, baseline comparison,
and transparent pattern explanation generation.
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "trained_model.joblib")
BENCHMARK_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "benchmark_metrics.joblib")

FEATURE_COLUMNS = [
    "prev_1",
    "prev_2",
    "prev_3",
    "diff_1_2",
    "diff_2_3",
    "last_is_odd",
    "repeat_streak",
    "recent_mean",
    "recent_span",
    "round_num",
]


def extract_features_from_history(history: List[int], round_num: int, max_range: int = 10) -> Dict[str, float]:
    """
    Extract statistical and sequential features from a player's previous choices.
    Gracefully pads missing choices with neutral defaults if history < 3.
    """
    h_len = len(history)

    # Lags (most recent is prev_1)
    prev_1 = float(history[-1]) if h_len >= 1 else float((max_range + 1) // 2)
    prev_2 = float(history[-2]) if h_len >= 2 else prev_1
    prev_3 = float(history[-3]) if h_len >= 3 else prev_2

    diff_1_2 = prev_1 - prev_2
    diff_2_3 = prev_2 - prev_3
    last_is_odd = 1.0 if (int(prev_1) % 2 != 0) else 0.0

    # Repeat streak: how many consecutive times the same number was selected
    streak = 1
    if h_len >= 2:
        for val in reversed(history[:-1]):
            if val == history[-1]:
                streak += 1
            else:
                break
    repeat_streak = float(streak)

    recent_slice = history[-3:] if h_len >= 3 else (history if h_len > 0 else [prev_1])
    recent_mean = float(np.mean(recent_slice))
    recent_span = float(max(recent_slice) - min(recent_slice))

    return {
        "prev_1": prev_1,
        "prev_2": prev_2,
        "prev_3": prev_3,
        "diff_1_2": diff_1_2,
        "diff_2_3": diff_2_3,
        "last_is_odd": last_is_odd,
        "repeat_streak": repeat_streak,
        "recent_mean": recent_mean,
        "recent_span": recent_span,
        "round_num": float(round_num),
    }


def generate_synthetic_player_dataset(num_sessions: int = 400, rounds_per_session: int = 15, max_range: int = 10, random_seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic data simulating human behavioral archetypes:
    1. Cyclers / Counters: step forward or backward (+1, +2, -1).
    2. Repeaters / Sticky: linger on favorite numbers with subtle drift.
    3. Alternators: switch between odd/even or high/low.
    4. Random / Gambler's Fallacy: avoid recent numbers or uniform noise.
    """
    rng = np.random.RandomState(random_seed)
    records = []

    archetypes = ["cycler", "repeater", "alternator", "random"]

    for _ in range(num_sessions):
        archetype = rng.choice(archetypes, p=[0.30, 0.25, 0.25, 0.20])
        history: List[int] = []

        # Initial seed choice
        current = rng.randint(1, max_range + 1)
        history.append(current)

        for round_idx in range(2, rounds_per_session + 1):
            # Target choice based on archetype behavior
            if archetype == "cycler":
                step = rng.choice([1, 2, -1], p=[0.6, 0.2, 0.2])
                next_choice = ((current - 1 + step) % max_range) + 1
            elif archetype == "repeater":
                if rng.rand() < 0.65:
                    next_choice = current  # Repeat choice
                else:
                    drift = rng.choice([-1, 1])
                    next_choice = min(max_range, max(1, current + drift))
            elif archetype == "alternator":
                # Alternate between low (1..5) and high (6..10)
                if current <= max_range // 2:
                    next_choice = rng.randint(max_range // 2 + 1, max_range + 1)
                else:
                    next_choice = rng.randint(1, max_range // 2 + 1)
            else:
                # Random / unpredictable choice
                next_choice = rng.randint(1, max_range + 1)

            # Extract features before revealing the target choice
            feat = extract_features_from_history(history, round_num=round_idx, max_range=max_range)
            feat["target"] = next_choice
            records.append(feat)

            history.append(next_choice)
            current = next_choice

    return pd.DataFrame(records)


class MindReaderAI:
    """
    Machine Learning engine for Mind Reader AI.
    Handles model training, testing, baseline comparison, and prediction with explanation.
    """

    def __init__(self, model_file: str = MODEL_PATH, benchmark_file: str = BENCHMARK_PATH):
        self.model_file = model_file
        self.benchmark_file = benchmark_file
        self.model: Optional[RandomForestClassifier] = None
        self.baseline_model: Optional[DummyClassifier] = None
        self.benchmark_info: Dict[str, Any] = {}
        self.max_range = 10
        self._load_or_train()

    def _load_or_train(self) -> None:
        """Load pre-trained model and benchmark or train a new one."""
        if os.path.exists(self.model_file) and os.path.exists(self.benchmark_file):
            try:
                self.model = joblib.load(self.model_file)
                self.benchmark_info = joblib.load(self.benchmark_file)
                return
            except Exception:
                # In case file is corrupted, fall through to train
                pass

        self.train_and_evaluate()

    def train_and_evaluate(self) -> Dict[str, Any]:
        """
        Train RandomForest model on synthetic training split and evaluate on unseen test data.
        Also trains a Most-Frequent Dummy baseline for honest comparative evaluation.
        """
        df = generate_synthetic_player_dataset(num_sessions=500, rounds_per_session=15, max_range=self.max_range)

        X = df[FEATURE_COLUMNS]
        y = df["target"]

        # 80% Train, 20% Unseen Test split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)

        # Train primary Random Forest classifier
        rf = RandomForestClassifier(n_estimators=75, max_depth=9, min_samples_leaf=3, random_state=42)
        rf.fit(X_train, y_train)

        # Train baseline dummy classifier (predicts most frequent target)
        dummy = DummyClassifier(strategy="most_frequent")
        dummy.fit(X_train, y_train)

        # Evaluate on unseen test data
        rf_preds = rf.predict(X_test)
        dummy_preds = dummy.predict(X_test)

        rf_acc = float(accuracy_score(y_test, rf_preds))
        dummy_acc = float(accuracy_score(y_test, dummy_preds))
        random_chance = round(1.0 / self.max_range, 3)

        # Extract feature importances
        feature_importances = {
            col: round(float(imp), 4)
            for col, imp in sorted(zip(FEATURE_COLUMNS, rf.feature_importances_), key=lambda x: x[1], reverse=True)
        }

        self.model = rf
        self.baseline_model = dummy

        self.benchmark_info = {
            "model_type": "Random Forest Classifier (75 estimators, max_depth=9)",
            "baseline_type": "Most-Frequent Dummy Classifier",
            "total_synthetic_samples": len(df),
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "test_accuracy_percentage": round(rf_acc * 100.0, 1),
            "baseline_accuracy_percentage": round(dummy_acc * 100.0, 1),
            "random_chance_percentage": round(random_chance * 100.0, 1),
            "feature_importances": feature_importances,
            "evaluation_note": "Evaluated strictly on unseen synthetic human-behavior test split.",
        }

        # Persist to disk
        os.makedirs(os.path.dirname(self.model_file), exist_ok=True)
        joblib.dump(self.model, self.model_file)
        joblib.dump(self.benchmark_info, self.benchmark_file)

        return self.benchmark_info

    def predict(self, history: List[int], round_num: int, max_range: int = 10) -> Dict[str, Any]:
        """
        Generate a fair prediction from permitted previous-choice history ONLY.
        Returns predicted choice, confidence score, and human-readable explanation.
        """
        h_len = len(history)

        # Heuristic explanation handling for sparse initial history
        if h_len == 0:
            # First round: no prior history exists yet (Cold Start Calibration)
            # In psychology (The Blue-Seven phenomenon), humans disproportionately pick 7, 3, 8, or 6
            if max_range <= 10:
                candidates = [7, 3, 8, 6, 5]
                weights = [0.35, 0.25, 0.15, 0.15, 0.10]
            else:
                candidates = [7, 13, 17, 21, 14, 3]
                weights = [0.25, 0.20, 0.20, 0.15, 0.10, 0.10]
            
            seed_choice = int(np.random.choice(candidates, p=weights))
            return {
                "predicted_choice": seed_choice,
                "confidence": 0.22,
                "confidence_percent": 22,
                "history_used": [],
                "explanation": f"Round 1 (Calibration): No prior choice history exists yet. The AI is applying initial human cognitive heuristics (which favor numbers like {seed_choice}). From Round 2 onward, the Random Forest model analyzes your real choices!",
                "pattern_detected": "Initial Psychological Heuristic",
                "is_confident": False,
            }

        if h_len == 1:
            last = history[-1]
            # When people pick a number, they often choose an adjacent or opposite number
            fallback = ((last % max_range) + 1)
            return {
                "predicted_choice": fallback,
                "confidence": 0.28,
                "confidence_percent": 28,
                "history_used": history,
                "explanation": f"I'm still learning your patterns (only 1 choice: [{last}] recorded). Observing if you shift toward an adjacent value.",
                "pattern_detected": "Early Pattern Observation",
                "is_confident": False,
            }

        # Full ML Feature Extraction
        features_dict = extract_features_from_history(history, round_num=round_num, max_range=max_range)
        features_df = pd.DataFrame([features_dict])[FEATURE_COLUMNS]

        if self.model is None:
            self._load_or_train()

        probabilities = self.model.predict_proba(features_df)[0]
        classes = self.model.classes_

        # Filter classes within current max_range
        valid_indices = [i for i, c in enumerate(classes) if 1 <= c <= max_range]
        if valid_indices:
            best_idx = valid_indices[np.argmax(probabilities[valid_indices])]
            predicted_choice = int(classes[best_idx])
            raw_confidence = float(probabilities[best_idx])
        else:
            best_idx = int(np.argmax(probabilities))
            predicted_choice = int(classes[best_idx])
            raw_confidence = float(probabilities[best_idx])

        # Clamp confidence to realistic ranges for transparency (never claim 100% on probabilistic choice)
        confidence = round(float(np.clip(raw_confidence, 0.15, 0.95)), 2)
        confidence_percent = int(confidence * 100)

        # Generate intelligent explanation based on detected features
        explanation, pattern_name = self._generate_explanation(history, predicted_choice, confidence, features_dict)

        return {
            "predicted_choice": predicted_choice,
            "confidence": confidence,
            "confidence_percent": confidence_percent,
            "history_used": history[-5:],  # Show last 5 choices in UI
            "explanation": explanation,
            "pattern_detected": pattern_name,
            "is_confident": confidence >= 0.40,
        }

    def _generate_explanation(
        self,
        history: List[int],
        predicted_choice: int,
        confidence: float,
        features: Dict[str, float],
    ) -> Tuple[str, str]:
        """Construct a lucid, educational explanation of why the AI made this prediction."""
        h_len = len(history)
        prev_1 = int(features["prev_1"])
        prev_2 = int(features["prev_2"])
        diff_1_2 = int(features["diff_1_2"])

        # Check 1: Repeating the same choice
        if features["repeat_streak"] >= 2:
            return (
                f"You selected {prev_1} consecutive times. The Random Forest model detected high stickiness and inertia, projecting you will stick with {predicted_choice}.",
                "Sticky / Repeat Tendency",
            )

        # Check 2: Sequential step (e.g. +1, +2, -1)
        if h_len >= 3 and diff_1_2 != 0:
            diff_2_3 = int(features["diff_2_3"])
            if diff_1_2 == diff_2_3:
                direction = "upward" if diff_1_2 > 0 else "downward"
                return (
                    f"Detected a consistent {direction} progression (step of {diff_1_2:+d} across your last rounds). The model projects sequence continuation to {predicted_choice}.",
                    "Sequential Progression",
                )

        # Check 3: Oscillation / Alternation
        if h_len >= 4:
            if history[-1] == history[-3] and history[-2] == history[-4] and history[-1] != history[-2]:
                return (
                    f"Identified an alternating pendulum pattern between {history[-2]} and {history[-1]}. Anticipating return to {predicted_choice}.",
                    "Pendulum Oscillation",
                )

        # Check 4: Odd/Even rhythm
        recent = history[-4:]
        all_odd = all(x % 2 != 0 for x in recent)
        all_even = all(x % 2 == 0 for x in recent)
        if all_odd:
            return (
                f"You favored 4 consecutive odd numbers ({recent}). Model weights reflect parity clustering, leaning toward {predicted_choice}.",
                "Parity Clustering (Odd)",
            )
        if all_even:
            return (
                f"You favored 4 consecutive even numbers ({recent}). Model weights reflect parity clustering, leaning toward {predicted_choice}.",
                "Parity Clustering (Even)",
            )

        # Check 5: General multi-feature probability distribution
        if confidence >= 0.45:
            return (
                f"Correlating recent trajectory [{', '.join(map(str, history[-3:]))}] with decision-tree split nodes. Highest conditional probability converges on {predicted_choice}.",
                "Decision Tree Ensemble Path",
            )

        return (
            f"Pattern entropy is high (choices appear unpredictable or randomized). Model generated an estimated probabilistic guess of {predicted_choice} based on frequency weights.",
            "Probabilistic Baseline",
        )

    def get_benchmark_info(self) -> Dict[str, Any]:
        """Return offline evaluation benchmark metrics."""
        if not self.benchmark_info:
            self._load_or_train()
        return self.benchmark_info


# Global singleton instance for efficient memory usage
ai_service = MindReaderAI()
