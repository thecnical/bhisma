"""
Client Predictor
================
Behavior prediction for WiFi clients based on historical patterns.

Predicts client movement, connection patterns, and potential
vulnerability based on observed behavior.
"""

import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class ClientBehavior:
    """Observed client behavior pattern."""
    mac: str
    ssid_preference: List[str]
    active_hours: List[int]
    avg_session_duration: float
    channel_hopping_rate: float
    roaming_frequency: float
    timestamp: float


class ClientPredictor:
    """WiFi client behavior prediction engine."""

    def __init__(self):
        self.behaviors: Dict[str, ClientBehavior] = {}
        self.observation_window: List[Dict[str, Any]] = []
        self.stats = {
            "observations": 0,
            "predictions_made": 0,
        }

    def observe(self, mac: str, ssid: str, channel: int,
                signal: int, timestamp: Optional[float] = None) -> None:
        """
        Record client observation.

        Args:
            mac: Client MAC address
            ssid: Connected SSID
            channel: WiFi channel
            signal: Signal strength in dBm
            timestamp: Observation time
        """
        if timestamp is None:
            timestamp = time.time()

        observation = {
            "mac": mac,
            "ssid": ssid,
            "channel": channel,
            "signal": signal,
            "timestamp": timestamp,
            "hour": int(time.localtime(timestamp).tm_hour),
        }
        self.observation_window.append(observation)
        self.stats["observations"] += 1

        # Update behavior profile
        if mac not in self.behaviors:
            self.behaviors[mac] = ClientBehavior(
                mac=mac,
                ssid_preference=[],
                active_hours=[],
                avg_session_duration=0.0,
                channel_hopping_rate=0.0,
                roaming_frequency=0.0,
                timestamp=timestamp,
            )

        behavior = self.behaviors[mac]
        if ssid not in behavior.ssid_preference:
            behavior.ssid_preference.append(ssid)
        if observation["hour"] not in behavior.active_hours:
            behavior.active_hours.append(observation["hour"])

    def predict_next_ssid(self, mac: str) -> Optional[str]:
        """
        Predict next SSID the client will connect to.

        Returns:
            Predicted SSID or None
        """
        if mac not in self.behaviors:
            return None

        behavior = self.behaviors[mac]
        if not behavior.ssid_preference:
            return None

        self.stats["predictions_made"] += 1
        return behavior.ssid_preference[0]

    def predict_vulnerability(self, mac: str) -> Dict[str, Any]:
        """
        Predict client vulnerability based on behavior.

        Returns:
            Vulnerability assessment
        """
        if mac not in self.behaviors:
            return {"risk": "unknown", "confidence": 0.0}

        behavior = self.behaviors[mac]
        risk_factors = []

        # High channel hopping = potential rogue AP detection
        if behavior.channel_hopping_rate > 0.5:
            risk_factors.append("high_channel_hopping")

        # Unusual active hours
        if behavior.active_hours and len(behavior.active_hours) > 12:
            risk_factors.append("unusual_hours")

        risk_level = "low"
        if len(risk_factors) >= 2:
            risk_level = "high"
        elif len(risk_factors) == 1:
            risk_level = "medium"

        return {
            "risk": risk_level,
            "confidence": min(1.0, len(risk_factors) * 0.3),
            "factors": risk_factors,
        }

    def get_behavior(self, mac: str) -> Optional[Dict[str, Any]]:
        """Get behavior profile for a client."""
        if mac not in self.behaviors:
            return None
        return asdict(self.behaviors[mac])

    def get_stats(self) -> Dict[str, int]:
        """Return predictor statistics."""
        return {
            **self.stats,
            "tracked_clients": len(self.behaviors),
            "total_observations": len(self.observation_window),
        }
