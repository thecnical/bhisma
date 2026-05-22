"""
Device Fingerprinting Model
=============================
Machine learning-based WiFi device identification from traffic patterns.

Uses features extracted from 802.11 frames (frame sizes, inter-arrival times,
IE fields, probe patterns) to classify device type, OS, and vendor.
"""

import os
import pickle
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split


@dataclass
class FingerprintResult:
    """Device fingerprint classification result."""
    device_type: str
    confidence: float
    vendor: str
    os_family: str
    features: Dict[str, float]


class DeviceFingerprinter:
    """ML-based device fingerprinting engine."""

    MODEL_PATH = os.path.expanduser("~/.bhisma/models/device_fingerprint.pkl")

    def __init__(self):
        self.model: Optional[RandomForestClassifier] = None
        self.scaler: Optional[StandardScaler] = None
        self._feature_names: List[str] = [
            "avg_frame_size",
            "frame_size_std",
            "probe_count_10s",
            "unique_ssids_probed",
            "ie_length_mean",
            "ie_count",
            "ht_capable",
            "vht_capable",
            "he_capable",
            "max_rate",
            "power_save_ratio",
            "reassoc_count",
            "disassoc_count",
            "auth_count",
            "avg_inter_arrival_ms",
        ]
        self._load_model()

    def _load_model(self) -> None:
        """Load pre-trained model from disk or initialize new one."""
        if os.path.exists(self.MODEL_PATH):
            try:
                with open(self.MODEL_PATH, "rb") as f:
                    data = pickle.load(f)
                self.model = data.get("model")
                self.scaler = data.get("scaler")
            except Exception:
                pass

        if self.model is None:
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=20,
                random_state=42,
                n_jobs=-1,
            )
            self.scaler = StandardScaler()

    def _extract_features(self, frames: List[Dict[str, Any]]) -> np.ndarray:
        """Extract numerical features from a list of 802.11 frames."""
        features = {
            "avg_frame_size": 0.0,
            "frame_size_std": 0.0,
            "probe_count_10s": 0.0,
            "unique_ssids_probed": 0.0,
            "ie_length_mean": 0.0,
            "ie_count": 0.0,
            "ht_capable": 0.0,
            "vht_capable": 0.0,
            "he_capable": 0.0,
            "max_rate": 0.0,
            "power_save_ratio": 0.0,
            "reassoc_count": 0.0,
            "disassoc_count": 0.0,
            "auth_count": 0.0,
            "avg_inter_arrival_ms": 0.0,
        }

        if not frames:
            return np.array([features[name] for name in self._feature_names])

        sizes = [f.get("size", 0) for f in frames]
        features["avg_frame_size"] = float(np.mean(sizes))
        features["frame_size_std"] = float(np.std(sizes)) if len(sizes) > 1 else 0.0

        probe_frames = [f for f in frames if f.get("subtype") == "probe_req"]
        features["probe_count_10s"] = len(probe_frames)
        features["unique_ssids_probed"] = len(
            {f.get("ssid", "") for f in probe_frames if f.get("ssid")}
        )

        ie_lengths = [f.get("ie_length", 0) for f in frames if f.get("ie_length")]
        features["ie_length_mean"] = float(np.mean(ie_lengths)) if ie_lengths else 0.0
        features["ie_count"] = float(sum(1 for f in frames if f.get("ie_length", 0) > 0))

        caps = frames[0].get("capabilities", {}) if frames else {}
        features["ht_capable"] = 1.0 if caps.get("ht", False) else 0.0
        features["vht_capable"] = 1.0 if caps.get("vht", False) else 0.0
        features["he_capable"] = 1.0 if caps.get("he", False) else 0.0
        features["max_rate"] = float(caps.get("max_rate", 0))

        power_save = sum(1 for f in frames if f.get("power_management", False))
        features["power_save_ratio"] = power_save / len(frames) if frames else 0.0

        features["reassoc_count"] = float(
            sum(1 for f in frames if f.get("subtype") == "reassoc")
        )
        features["disassoc_count"] = float(
            sum(1 for f in frames if f.get("subtype") == "disassoc")
        )
        features["auth_count"] = float(
            sum(1 for f in frames if f.get("subtype") == "auth")
        )

        timestamps = sorted([f.get("timestamp", 0) for f in frames])
        if len(timestamps) > 1:
            diffs = np.diff(timestamps)
            features["avg_inter_arrival_ms"] = float(np.mean(diffs))

        return np.array([features[name] for name in self._feature_names])

    def predict(self, frames: List[Dict[str, Any]]) -> FingerprintResult:
        """
        Predict device fingerprint from captured frames.

        Args:
            frames: List of 802.11 frame metadata dictionaries

        Returns:
            FingerprintResult with device classification
        """
        features = self._extract_features(frames)
        features_2d = features.reshape(1, -1)

        if hasattr(self.model, "classes_") and len(self.model.classes_) > 0:
            try:
                pred = self.model.predict(features_2d)[0]
                proba = self.model.predict_proba(features_2d)[0]
                confidence = float(np.max(proba))
            except Exception:
                pred = "unknown"
                confidence = 0.0
        else:
            pred = "unknown"
            confidence = 0.0

        # Map prediction to metadata
        device_type, vendor, os_family = self._lookup_device_info(pred)

        feature_dict = {
            name: float(val) for name, val in zip(self._feature_names, features)
        }

        return FingerprintResult(
            device_type=device_type,
            confidence=confidence,
            vendor=vendor,
            os_family=os_family,
            features=feature_dict,
        )

    def _lookup_device_info(self, pred: str) -> Tuple[str, str, str]:
        """Map model prediction to device metadata."""
        lookup = {
            "iphone": ("Smartphone", "Apple", "iOS"),
            "android": ("Smartphone", "Various", "Android"),
            "laptop": ("Computer", "Various", "Various"),
            "iot": ("IoT Device", "Various", "Embedded"),
            "router": ("Network Equipment", "Various", "Embedded"),
        }
        return lookup.get(pred.lower(), ("Unknown", "Unknown", "Unknown"))

    def train(self, frames: List[List[Dict[str, Any]]],
              labels: List[str]) -> Dict[str, float]:
        """
        Train the fingerprinting model on labeled data.

        Args:
            frames: List of frame sequences (one per device)
            labels: Device type labels

        Returns:
            Training metrics dictionary
        """
        X = np.array([self._extract_features(f) for f in frames])
        y = np.array(labels)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        self.scaler.fit(X_train)
        X_train_s = self.scaler.transform(X_train)
        X_test_s = self.scaler.transform(X_test)

        self.model.fit(X_train_s, y_train)
        score = self.model.score(X_test_s, y_test)

        self._save_model()

        return {"accuracy": round(score, 4), "samples": len(y)}

    def _save_model(self) -> None:
        """Persist trained model to disk."""
        os.makedirs(os.path.dirname(self.MODEL_PATH), exist_ok=True)
        with open(self.MODEL_PATH, "wb") as f:
            pickle.dump({"model": self.model, "scaler": self.scaler}, f)

    def get_feature_importance(self) -> Dict[str, float]:
        """Return feature importance scores from the model."""
        if hasattr(self.model, "feature_importances_"):
            return {
                name: float(imp)
                for name, imp in zip(
                    self._feature_names, self.model.feature_importances_
                )
            }
        return {}
