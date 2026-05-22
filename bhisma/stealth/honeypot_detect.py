"""
Honeypot Detection
==================
ML + heuristic detection of honeypots, decoys, and fake APs.
"""

import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from bhisma.core.fingerprint import FingerprintingEngine
from rich.console import Console

console = Console()


@dataclass
class HoneypotCheck:
    indicator: str
    severity: str  # low, medium, high
    confidence: float = 0.0


class HoneypotDetector:
    """Detects honeypots and suspicious APs."""

    def __init__(self):
        self.fingerprint = FingerprintingEngine()
        self._known_honeypots = set()
        self._suspicious_bssids = {}

    def analyze_ap(self, ap_data: Dict[str, Any]) -> List[HoneypotCheck]:
        """
        Analyze an AP for honeypot indicators.

        Returns:
            List of HoneypotCheck findings
        """
        findings = []
        bssid = ap_data.get("bssid", "")

        # Check 1: Karma response indicator
        if self._is_karma_responsive(ap_data):
            findings.append(HoneypotCheck(
                indicator="AP responds to all probe requests (Karma behavior)",
                severity="high",
                confidence=0.9,
            ))

        # Check 2: Unrealistic signal strength
        signal = ap_data.get("signal", -100)
        if signal > -20:
            findings.append(HoneypotCheck(
                indicator=f"Unrealistically strong signal ({signal} dBm)",
                severity="medium",
                confidence=0.7,
            ))

        # Check 3: Beacon interval anomalies
        beacon_interval = ap_data.get("beacon_interval", 0)
        if beacon_interval > 0 and (beacon_interval < 50 or beacon_interval > 1200):
            findings.append(HoneypotCheck(
                indicator=f"Unusual beacon interval: {beacon_interval} TU",
                severity="low",
                confidence=0.5,
            ))

        # Check 4: No client history but very responsive
        if ap_data.get("clients", 0) == 0 and ap_data.get("response_rate", 0) > 0.9:
            findings.append(HoneypotCheck(
                indicator="Over-responsive with no legitimate clients",
                severity="medium",
                confidence=0.6,
            ))

        # Check 5: SSID suspicious patterns
        ssid = ap_data.get("ssid", "")
        suspicious_ssids = ["Free_WiFi", "GuestNetwork", "PublicWiFi", "xfinitywifi", "Starbucks_Guest"]
        if ssid in suspicious_ssids and not ap_data.get("probed_by_clients", False):
            findings.append(HoneypotCheck(
                indicator=f"Suspicious SSID '{ssid}' with no client probes",
                severity="medium",
                confidence=0.65,
            ))

        # Check 6: Behavioral fingerprint anomalies
        anomalies = self.fingerprint.detect_anomalies(bssid)
        for anomaly in anomalies:
            findings.append(HoneypotCheck(
                indicator=anomaly,
                severity="medium",
                confidence=0.6,
            ))

        # Check 7: Instant association acceptance
        if ap_data.get("instant_assoc", False):
            findings.append(HoneypotCheck(
                indicator="Instant association acceptance",
                severity="high",
                confidence=0.85,
            ))

        if findings:
            self._suspicious_bssids[bssid] = findings

        return findings

    def is_honeypot(self, ap_data: Dict[str, Any], threshold: int = 2) -> bool:
        """Return True if AP is likely a honeypot based on findings count."""
        findings = self.analyze_ap(ap_data)
        high_sev = sum(1 for f in findings if f.severity == "high")
        return high_sev >= 1 or len(findings) >= threshold

    def _is_karma_responsive(self, ap_data: Dict[str, Any]) -> bool:
        """Check if AP shows KARMA-like behavior."""
        probed = ap_data.get("probed_ssids", [])
        if len(probed) > 10:
            return True
        return False

    def add_known_honeypot(self, bssid: str) -> None:
        """Manually mark a BSSID as known honeypot."""
        self._known_honeypots.add(bssid)

    def is_blacklisted(self, bssid: str) -> bool:
        """Check if BSSID is in known honeypot list."""
        return bssid in self._known_honeypots

    def get_suspicious_report(self) -> Dict[str, List[Dict]]:
        """Generate report of all suspicious APs."""
        return {
            bssid: [{"indicator": f.indicator, "severity": f.severity, "confidence": f.confidence}
                    for f in findings]
            for bssid, findings in self._suspicious_bssids.items()
        }
