"""
Behavioral Mimicry Engine
===========================
Morphs attack traffic to match target's exact behavioral profile.
"""

import random
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass

from bhisma.core.fingerprint import FingerprintingEngine, TrafficProfile


@dataclass
class MimicryConfig:
    """Configuration for traffic mimicry."""
    enabled: bool = True
    jitter_percent: float = 5.0  # Variation within normal range
    match_beacon_interval: bool = True
    match_packet_size: bool = True
    match_rate: bool = True
    match_ie_order: bool = True


class MimicryEngine:
    """Morphs attack traffic to match target behavioral profile."""

    def __init__(self, fingerprint_engine: FingerprintingEngine, config: Optional[MimicryConfig] = None):
        self.fingerprint = fingerprint_engine
        self.config = config or MimicryConfig()

    def get_mimicry_params(self, target_bssid: str) -> Dict[str, Any]:
        """
        Generate parameters for mimicking target traffic.

        Returns:
            Dict with timing, size, rate parameters
        """
        if not self.config.enabled:
            return self._default_params()

        profile = self.fingerprint.get_profile(target_bssid)
        if not profile:
            return self._default_params()

        stats = profile.get_statistics()
        params = {}

        if self.config.match_beacon_interval and "beacon_interval_mean" in stats:
            base = stats["beacon_interval_mean"]
            jitter = base * (self.config.jitter_percent / 100.0)
            params["beacon_interval"] = base + random.uniform(-jitter, jitter)

        if self.config.match_packet_size and "packet_size_mean" in stats:
            base = stats["packet_size_mean"]
            std = stats.get("packet_size_std", base * 0.1)
            params["packet_size"] = max(0, random.gauss(base, std))

        if self.config.match_rate and "rate_mean" in stats:
            base = stats["rate_mean"]
            params["data_rate"] = max(1, base + random.gauss(0, base * 0.05))

        if self.config.match_ie_order:
            params["ie_order"] = profile.ie_order

        params["timestamp_drift"] = stats.get("timestamp_drift", 0)
        return params

    def calculate_delay(self, target_bssid: str, base_delay: float = 0.1) -> float:
        """Calculate an appropriate inter-packet delay matching target behavior."""
        profile = self.fingerprint.get_profile(target_bssid)
        if not profile:
            return base_delay
        stats = profile.get_statistics()
        if "iat_mean" in stats and stats["iat_mean"] > 0:
            iat = stats["iat_mean"]
            jitter = iat * (self.config.jitter_percent / 100.0)
            return max(0.001, iat + random.uniform(-jitter, jitter))
        return base_delay

    def generate_packet_size(self, target_bssid: str, default: int = 256) -> int:
        """Generate a packet size matching target distribution."""
        profile = self.fingerprint.get_profile(target_bssid)
        if not profile:
            return default
        stats = profile.get_statistics()
        if "packet_size_mean" in stats:
            mean = stats["packet_size_mean"]
            std = stats.get("packet_size_std", mean * 0.1)
            return max(64, int(random.gauss(mean, std)))
        return default

    def _default_params(self) -> Dict[str, Any]:
        """Default parameters when no profile exists."""
        return {
            "beacon_interval": 100.0,
            "packet_size": 256.0,
            "data_rate": 54.0,
            "timestamp_drift": 0.0,
        }

    def apply_to_deauth(self, target_bssid: str, count: int) -> Dict[str, Any]:
        """Get deauth-specific mimicry parameters."""
        params = self.get_mimicry_params(target_bssid)
        delay = self.calculate_delay(target_bssid)
        return {
            "count": count,
            "delay": delay,
            "packet_size": self.generate_packet_size(target_bssid),
            **params,
        }

    def apply_to_beacon_flood(self, target_bssid: str, ssid: str) -> Dict[str, Any]:
        """Get beacon flood mimicry parameters."""
        params = self.get_mimicry_params(target_bssid)
        return {
            "ssid": ssid,
            "beacon_interval": params.get("beacon_interval", 100),
            "packet_size": params.get("packet_size", 256),
            "rates": params.get("ie_order", []),
        }
