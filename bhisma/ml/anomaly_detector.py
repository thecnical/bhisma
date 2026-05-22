"""
Anomaly Detector
================
Real-time anomaly detection for WiFi traffic using Isolation Forest.

Detects deauth floods, beacon anomalies, rogue APs, and suspicious
client behavior from 802.11 frame metadata streams.
"""

import os
import pickle
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


@dataclass
class AnomalyAlert:
    """Detected anomaly record."""
    timestamp: float
    anomaly_type: str
    confidence: float
    source_mac: Optional[str]
    target_bssid: Optional[str]
    features: Dict[str, float]
    severity: str  # low, medium, high, critical


class AnomalyDetector:
    """WiFi traffic anomaly detection engine."""

    MODEL_PATH = os.path.expanduser("~/.bhisma/models/anomaly_detector.pkl")

    def __init__(self, contamination: float = 0.05):
        self.model: Optional[IsolationForest] = None
        self.scaler = StandardScaler()
        self.contamination = contamination
        self.alerts: List[AnomalyAlert] = []
        self._feature_names = [
            "frame_rate",
            "unique_dst_count",
            "deauth_ratio",
            "beacon_ratio",
            "avg_signal_delta",
            "reassoc_rate",
            "probe_rate",
            "auth_failure_rate",
            "channel_switch_count",
            "power_level_variance",
        ]
        self._load_model()

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
            self.model = IsolationForest(
                contamination=self.contamination,
                n_estimators=100,
                random_state=42,
                n_jobs=-1,
            )

    def _extract_features(self, window: List[Dict[str, Any]]) -> np.ndarray:
        """Extract features from a time window of frame metadata."""
        if not window:
            return np.zeros(len(self._feature_names))

        features = {
            "frame_rate": len(window) / 10.0,
            "unique_dst_count": len({f.get("addr1", "") for f in window}),
            "deauth_ratio": sum(1 for f in window if f.get("subtype") == "deauth") / len(window),
            "beacon_ratio": sum(1 for f in window if f.get("subtype") == "beacon") / len(window),
            "avg_signal_delta": 0.0,
            "reassoc_rate": sum(1 for f in window if f.get("subtype") == "reassoc") / len(window),
            "probe_rate": sum(1 for f in window if f.get("subtype") == "probe_req") / len(window),
            "auth_failure_rate": sum(1 for f in window if f.get("auth_status") == "failure") / len(window),
            "channel_switch_count": len({f.get("channel", 0) for f in window}),
            "power_level_variance": 0.0,
        }

        signals = [f.get("signal", -50) for f in window if f.get("signal") is not None]
        if len(signals) > 1:
            features["avg_signal_delta"] = float(np.mean(np.diff(signals)))
            features["power_level_variance"] = float(np.var(signals))

        return np.array([features[name] for name in self._feature_names])

    def analyze_window(self, window: List[Dict[str, Any]],
                       source_mac: Optional[str] = None,
                       target_bssid: Optional[str] = None) -> Optional[AnomalyAlert]:
        """
        Analyze a time window of frames for anomalies.

        Returns:
            AnomalyAlert if anomaly detected, else None
        """
        features = self._extract_features(window)
        features_2d = features.reshape(1, -1)

        if hasattr(self.model, "offset_"):
            try:
                prediction = self.model.predict(features_2d)[0]
                score = self.model.decision_function(features_2d)[0]
            except Exception:
                return None
        else:
            return None

        if prediction == -1:  # Anomaly
            confidence = min(1.0, max(0.0, 0.5 - score))
            anomaly_type = self._classify_anomaly(features)
            severity = self._severity(confidence, anomaly_type)

            alert = AnomalyAlert(
                timestamp=time.time(),
                anomaly_type=anomaly_type,
                confidence=round(confidence, 3),
                source_mac=source_mac,
                target_bssid=target_bssid,
                features={
                    name: float(val)
                    for name, val in zip(self._feature_names, features)
                },
                severity=severity,
            )
            self.alerts.append(alert)
            return alert
        return None

    def _classify_anomaly(self, features: np.ndarray) -> str:
        """Map feature vector to anomaly type label."""
        idx_map = {name: i for i, name in enumerate(self._feature_names)}
        if features[idx_map["deauth_ratio"]] > 0.3:
            return "deauth_flood"
        if features[idx_map["beacon_ratio"]] > 0.4:
            return "beacon_anomaly"
        if features[idx_map["reassoc_rate"]] > 0.2:
            return "reassoc_storm"
        if features[idx_map["probe_rate"]] > 0.3:
            return "probe_flood"
        if features[idx_map["auth_failure_rate"]] > 0.3:
            return "auth_bruteforce"
        if features[idx_map["channel_switch_count"]] > 3:
            return "channel_hop"
        return "general_anomaly"

    def _severity(self, confidence: float, anomaly_type: str) -> str:
        """Determine alert severity."""
        if confidence > 0.8 or anomaly_type == "deauth_flood":
            return "critical"
        if confidence > 0.6:
            return "high"
        if confidence > 0.4:
            return "medium"
        return "low"

    def train(self, windows: List[List[Dict[str, Any]]],
              labels: Optional[List[int]] = None) -> Dict[str, float]:
        """
        Train anomaly detector on labeled data.

        Args:
            windows: List of frame windows
            labels: 1 for normal, -1 for anomaly (None for unsupervised)

        Returns:
            Training metrics
        """
        X = np.array([self._extract_features(w) for w in windows])
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)
        self.model.fit(X_scaled)

        self._save_model()

        predictions = self.model.predict(X_scaled)
        anomaly_count = int(np.sum(predictions == -1))

        return {
            "samples": len(windows),
            "anomalies_detected": anomaly_count,
            "anomaly_ratio": round(anomaly_count / len(windows), 4) if windows else 0.0,
        }

    def _save_model(self) -> None:
        """Persist model to disk."""
        os.makedirs(os.path.dirname(self.MODEL_PATH), exist_ok=True)
        with open(self.MODEL_PATH, "wb") as f:
            pickle.dump({"model": self.model, "scaler": self.scaler}, f)

    def get_alerts(self, severity_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get anomaly alerts with optional severity filtering."""
        results = []
        for alert in self.alerts:
            if severity_filter and alert.severity != severity_filter:
                continue
            results.append({
                "timestamp": alert.timestamp,
                "type": alert.anomaly_type,
                "confidence": alert.confidence,
                "source_mac": alert.source_mac,
                "target_bssid": alert.target_bssid,
                "severity": alert.severity,
            })
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Return detector statistics."""
        return {
            "total_alerts": len(self.alerts),
            "critical": sum(1 for a in self.alerts if a.severity == "critical"),
            "high": sum(1 for a in self.alerts if a.severity == "high"),
            "medium": sum(1 for a in self.alerts if a.severity == "medium"),
            "low": sum(1 for a in self.alerts if a.severity == "low"),
        }
