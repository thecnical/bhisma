"""
Auto Trainer
============
Automated ML model training pipeline for Bhisma.

Trains device fingerprinting, anomaly detection, and timing
prediction models from collected WiFi traffic data.
"""

import os
import json
import time
from typing import Dict, List, Any, Optional
from bhisma.ml.device_fingerprint import DeviceFingerprinter
from bhisma.ml.anomaly_detector import AnomalyDetector
from bhisma.ml.timing_predictor import TimingPredictor


class ModelTrainer:
    """Automated ML model training pipeline."""

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = data_dir or os.path.expanduser("~/.bhisma/data")
        self.models_dir = os.path.expanduser("~/.bhisma/models")
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.models_dir, exist_ok=True)

        self.fingerprinter = DeviceFingerprinter()
        self.anomaly_detector = AnomalyDetector()
        self.timing_predictor = TimingPredictor()

        self.stats = {
            "models_trained": 0,
            "samples_processed": 0,
            "training_time": 0.0,
        }

    def train_all(self, dataset: Optional[str] = None) -> Dict[str, Any]:
        """
        Train all ML models on available data.

        Args:
            dataset: Path to dataset file (auto-discover if None)

        Returns:
            Training results summary
        """
        start_time = time.time()
        results = {}

        # Load or generate training data
        data = self._load_or_generate_data(dataset)

        # Train device fingerprinter
        if "fingerprint_samples" in data:
            fp_result = self.fingerprinter.train(
                data["fingerprint_samples"],
                data["fingerprint_labels"],
            )
            results["fingerprinter"] = fp_result
            self.stats["models_trained"] += 1
            self.stats["samples_processed"] += len(data["fingerprint_samples"])

        # Train anomaly detector
        if "anomaly_windows" in data:
            ad_result = self.anomaly_detector.train(
                data["anomaly_windows"],
                data.get("anomaly_labels"),
            )
            results["anomaly_detector"] = ad_result
            self.stats["models_trained"] += 1
            self.stats["samples_processed"] += len(data["anomaly_windows"])

        # Train timing predictor
        if "timing_samples" in data and "timing_labels" in data:
            tp_result = self.timing_predictor.train(
                data["timing_samples"],
                data["timing_labels"],
            )
            results["timing_predictor"] = tp_result
            self.stats["models_trained"] += 1
            self.stats["samples_processed"] += len(data["timing_samples"])

        self.stats["training_time"] = time.time() - start_time
        results["summary"] = self.stats

        return results

    def _load_or_generate_data(self, dataset: Optional[str]) -> Dict[str, Any]:
        """Load training data from file or generate synthetic data."""
        if dataset and os.path.exists(dataset):
            with open(dataset, "r") as f:
                return json.load(f)

        # Generate synthetic training data for demonstration
        return self._generate_synthetic_data()

    def _generate_synthetic_data(self) -> Dict[str, Any]:
        """Generate synthetic training data."""
        import numpy as np

        # Fingerprint samples
        fp_samples = []
        fp_labels = []
        for _ in range(100):
            sample = {
                "mac": ":".join(f"{np.random.randint(0, 256):02x}" for _ in range(6)),
                "frame_types": [np.random.randint(0, 10) for _ in range(5)],
                "channel": np.random.randint(1, 14),
                "signal": np.random.randint(-90, -30),
                "data_rate": np.random.randint(1, 54),
            }
            fp_samples.append(sample)
            fp_labels.append(np.random.choice(["phone", "laptop", "iot", "tablet"]))

        # Anomaly windows
        anomaly_windows = []
        for _ in range(50):
            window = [
                {
                    "addr1": ":".join(f"{np.random.randint(0, 256):02x}" for _ in range(6)),
                    "subtype": np.random.choice(["beacon", "data", "deauth", "probe_req"]),
                    "signal": np.random.randint(-90, -30),
                    "channel": np.random.randint(1, 14),
                }
                for _ in range(10)
            ]
            anomaly_windows.append(window)

        # Timing samples
        timing_samples = []
        timing_labels = []
        for _ in range(50):
            sample = {
                "hour_of_day": np.random.randint(0, 24),
                "day_of_week": np.random.randint(0, 7),
                "client_count": np.random.randint(0, 20),
                "packet_rate": np.random.randint(0, 1000),
                "avg_signal": np.random.randint(-90, -30),
                "channel_utilization": np.random.random(),
                "beacon_rate": np.random.randint(0, 100),
                "noise_floor": np.random.randint(-95, -85),
            }
            timing_samples.append(sample)
            timing_labels.append(np.random.random())

        return {
            "fingerprint_samples": fp_samples,
            "fingerprint_labels": fp_labels,
            "anomaly_windows": anomaly_windows,
            "timing_samples": timing_samples,
            "timing_labels": timing_labels,
        }

    def export_results(self, results: Dict[str, Any], filepath: str) -> bool:
        """Export training results to JSON file."""
        try:
            with open(filepath, "w") as f:
                json.dump(results, f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"[Trainer] Export error: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Return training statistics."""
        return {**self.stats}
