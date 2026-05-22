"""
Timing Predictor
================
ML-based timing analysis for attack window prediction.

Predicts optimal timing for attacks based on network traffic
patterns, client activity, and time-of-day analysis.
"""

import os
import pickle
import time
from typing import Dict, List, Any, Optional
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler


class TimingPredictor:
    """Timing prediction engine for attack optimization."""

    MODEL_PATH = os.path.expanduser("~/.bhisma/models/timing_predictor.pkl")

    def __init__(self):
        self.model: Optional[RandomForestRegressor] = None
        self.scaler = StandardScaler()
        self._load_model()
        self.stats = {
            "predictions": 0,
            "optimal_windows_found": 0,
        }

    def _load_model(self) -> None:
        """Load pre-trained model or initialize new one."""
        if os.path.exists(self.MODEL_PATH):
            try:
                with open(self.MODEL_PATH, "rb") as f:
                    data = pickle.load(f)
                self.model = data.get("model")
                self.scaler = data.get("scaler", StandardScaler())
            except Exception:
                pass

        if self.model is None:
            self.model = RandomForestRegressor(
                n_estimators=50,
                random_state=42,
                n_jobs=-1,
            )

    def _extract_features(self, traffic_data: Dict[str, Any]) -> np.ndarray:
        """Extract timing features from traffic data."""
        features = [
            traffic_data.get("hour_of_day", 12) / 24.0,
            traffic_data.get("day_of_week", 0) / 7.0,
            traffic_data.get("client_count", 0) / 50.0,
            traffic_data.get("packet_rate", 0) / 1000.0,
            traffic_data.get("avg_signal", -50) / -100.0,
            traffic_data.get("channel_utilization", 0.5),
            traffic_data.get("beacon_rate", 0) / 100.0,
            traffic_data.get("noise_floor", -90) / -100.0,
        ]
        return np.array(features)

    def predict_success_probability(self, traffic_data: Dict[str, Any]) -> float:
        """
        Predict attack success probability based on timing.

        Args:
            traffic_data: Current network traffic metrics

        Returns:
            Success probability (0.0 to 1.0)
        """
        self.stats["predictions"] += 1

        if not hasattr(self.model, "n_features_"):
            # Return heuristic if model not trained
            return self._heuristic_score(traffic_data)

        features = self._extract_features(traffic_data)
        features_2d = features.reshape(1, -1)

        try:
            prediction = self.model.predict(features_2d)[0]
            return float(np.clip(prediction, 0.0, 1.0))
        except Exception:
            return self._heuristic_score(traffic_data)

    def _heuristic_score(self, traffic_data: Dict[str, Any]) -> float:
        """Fallback heuristic scoring."""
        score = 0.5

        # Prefer off-peak hours
        hour = traffic_data.get("hour_of_day", 12)
        if 2 <= hour <= 5:
            score += 0.3

        # Prefer low client count
        clients = traffic_data.get("client_count", 0)
        if clients < 5:
            score += 0.2

        return min(1.0, score)

    def find_optimal_window(self, traffic_history: List[Dict[str, Any]],
                           window_minutes: int = 30) -> Optional[Dict[str, Any]]:
        """
        Find optimal attack window from historical traffic.

        Args:
            traffic_history: List of traffic snapshots
            window_minutes: Minimum window duration in minutes

        Returns:
            Optimal window details or None
        """
        if not traffic_history:
            return None

        best_window = None
        best_score = 0.0

        for i, snapshot in enumerate(traffic_history):
            score = self.predict_success_probability(snapshot)
            if score > best_score:
                best_score = score
                best_window = {
                    "timestamp": snapshot.get("timestamp", time.time()),
                    "score": score,
                    "hour": snapshot.get("hour_of_day", 12),
                    "clients": snapshot.get("client_count", 0),
                }

        if best_score > 0.7:
            self.stats["optimal_windows_found"] += 1

        return best_window

    def train(self, samples: List[Dict[str, Any]],
              labels: List[float]) -> Dict[str, float]:
        """
        Train timing predictor on labeled data.

        Args:
            samples: Traffic data samples
            labels: Success probability labels

        Returns:
            Training metrics
        """
        X = np.array([self._extract_features(s) for s in samples])
        y = np.array(labels)

        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)
        self.model.fit(X_scaled, y)

        self._save_model()

        return {
            "samples": len(samples),
            "mean_score": float(np.mean(y)),
            "model_score": float(self.model.score(X_scaled, y)),
        }

    def _save_model(self) -> None:
        """Persist model to disk."""
        os.makedirs(os.path.dirname(self.MODEL_PATH), exist_ok=True)
        with open(self.MODEL_PATH, "wb") as f:
            pickle.dump({"model": self.model, "scaler": self.scaler}, f)

    def get_stats(self) -> Dict[str, int]:
        """Return predictor statistics."""
        return {**self.stats}
