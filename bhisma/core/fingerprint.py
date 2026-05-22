"""
Behavioral Fingerprinting Engine
================================
Analyzes target traffic patterns to build behavioral profiles.
"""

import time
import statistics
from typing import Dict, List, Optional, Any
from collections import deque, defaultdict
from dataclasses import dataclass, field


@dataclass
class TrafficProfile:
    """Behavioral profile of a target AP or client."""
    bssid: str
    beacon_intervals: deque = field(default_factory=lambda: deque(maxlen=100))
    packet_sizes: deque = field(default_factory=lambda: deque(maxlen=500))
    inter_arrival_times: deque = field(default_factory=lambda: deque(maxlen=500))
    data_rates: deque = field(default_factory=lambda: deque(maxlen=100))
    channel_dwell: Dict[int, float] = field(default_factory=dict)
    timestamp_drift: float = 0.0
    ie_order: List[int] = field(default_factory=list)
    rates_list: List[int] = field(default_factory=list)
    last_update: float = field(default_factory=time.time)

    def add_beacon(self, interval: int, timestamp: int, packet_size: int, rate: int) -> None:
        """Record a beacon frame observation."""
        now = time.time()
        if self.beacon_intervals:
            expected_interval = statistics.mean(self.beacon_intervals) if len(self.beacon_intervals) > 5 else 100
            drift = abs(interval - expected_interval) / max(expected_interval, 1)
            self.timestamp_drift = (self.timestamp_drift * 0.9) + (drift * 0.1)
        self.beacon_intervals.append(interval)
        self.packet_sizes.append(packet_size)
        self.data_rates.append(rate)
        self.last_update = now

    def add_data_packet(self, size: int, timestamp: float) -> None:
        """Record a data frame observation."""
        self.packet_sizes.append(size)
        if self.inter_arrival_times:
            self.inter_arrival_times.append(timestamp - self.last_update)
        self.last_update = timestamp

    def get_statistics(self) -> Dict[str, Any]:
        """Compute statistical profile."""
        stats = {}
        if self.beacon_intervals:
            stats["beacon_interval_mean"] = statistics.mean(self.beacon_intervals)
            stats["beacon_interval_std"] = statistics.stdev(self.beacon_intervals) if len(self.beacon_intervals) > 1 else 0
        if self.packet_sizes:
            stats["packet_size_mean"] = statistics.mean(self.packet_sizes)
            stats["packet_size_std"] = statistics.stdev(self.packet_sizes) if len(self.packet_sizes) > 1 else 0
        if self.inter_arrival_times:
            stats["iat_mean"] = statistics.mean(self.inter_arrival_times)
            stats["iat_std"] = statistics.stdev(self.inter_arrival_times) if len(self.inter_arrival_times) > 1 else 0
        if self.data_rates:
            stats["rate_mean"] = statistics.mean(self.data_rates)
        stats["timestamp_drift"] = self.timestamp_drift
        return stats


class FingerprintingEngine:
    """Builds and compares behavioral profiles."""

    def __init__(self):
        self.profiles: Dict[str, TrafficProfile] = {}

    def observe_beacon(
        self,
        bssid: str,
        beacon_interval: int,
        timestamp: int,
        packet_size: int,
        rate: int,
        ie_elements: Optional[List[int]] = None,
    ) -> TrafficProfile:
        """Observe and record a beacon frame."""
        if bssid not in self.profiles:
            self.profiles[bssid] = TrafficProfile(bssid=bssid)
        profile = self.profiles[bssid]
        profile.add_beacon(beacon_interval, timestamp, packet_size, rate)
        if ie_elements:
            profile.ie_order = ie_elements
        return profile

    def observe_data(self, bssid: str, packet_size: int, timestamp: Optional[float] = None) -> None:
        """Observe a data frame."""
        if bssid not in self.profiles:
            self.profiles[bssid] = TrafficProfile(bssid=bssid)
        self.profiles[bssid].add_data_packet(packet_size, timestamp or time.time())

    def compare_profiles(self, bssid1: str, bssid2: str) -> float:
        """
        Compare two profiles and return similarity score (0.0-1.0).

        Used for detecting honeypots (too similar = suspicious).
        """
        if bssid1 not in self.profiles or bssid2 not in self.profiles:
            return 0.0
        p1 = self.profiles[bssid1].get_statistics()
        p2 = self.profiles[bssid2].get_statistics()
        if not p1 or not p2:
            return 0.0

        # Compare beacon intervals
        bi_diff = abs(p1.get("beacon_interval_mean", 100) - p2.get("beacon_interval_mean", 100)) / 100
        # Compare packet sizes
        ps_diff = abs(p1.get("packet_size_mean", 0) - p2.get("packet_size_mean", 0)) / 500
        # Compare rates
        rate_diff = abs(p1.get("rate_mean", 0) - p2.get("rate_mean", 0)) / 100

        similarity = 1.0 - min(1.0, (bi_diff + ps_diff + rate_diff) / 3)
        return max(0.0, similarity)

    def detect_anomalies(self, bssid: str) -> List[str]:
        """
        Detect anomalies in a target's behavior that suggest honeypot/decoy.

        Returns:
            List of anomaly descriptions
        """
        if bssid not in self.profiles:
            return []
        profile = self.profiles[bssid]
        stats = profile.get_statistics()
        anomalies = []

        # Too-perfect beacon intervals
        if stats.get("beacon_interval_std", 1) < 0.5:
            anomalies.append("Suspiciously consistent beacon intervals")

        # No timestamp drift
        if stats.get("timestamp_drift", 1) < 0.001:
            anomalies.append("Zero timestamp drift (virtual AP?)")

        # Unusual packet size distribution
        if stats.get("packet_size_std", 0) < 1:
            anomalies.append("Uniform packet sizes")

        return anomalies

    def get_profile(self, bssid: str) -> Optional[TrafficProfile]:
        """Get profile for a BSSID."""
        return self.profiles.get(bssid)

    def export_profiles(self) -> Dict[str, Dict]:
        """Export all profiles as dicts."""
        return {bssid: profile.get_statistics() for bssid, profile in self.profiles.items()}
