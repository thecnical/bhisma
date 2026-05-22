"""
AP Vulnerability Scorer
========================
Multi-factor vulnerability scoring engine for WiFi access points.

Analyzes encryption, protocol, client density, and known CVE
exposure to produce an attack priority score (0-100).
"""

import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class TargetProfile:
    """WiFi target profile for scoring."""
    bssid: str
    ssid: str
    encryption: str
    cipher: Optional[str]
    authentication: Optional[str]
    wps: bool
    signal: int
    channel: int
    clients: int
    manufacturer: Optional[str]
    model: Optional[str]
    firmware: Optional[str]


class VulnerabilityScorer:
    """WiFi target vulnerability scoring engine."""

    ENCRYPTION_SCORES = {
        "OPN": 100,
        "WEP": 95,
        "WPA": 70,
        "WPA2": 50,
        "WPA3": 20,
        "WPA2/WPA3": 35,
    }

    CIPHER_SCORES = {
        "TKIP": 30,
        "CCMP": 10,
        "GCMP": 5,
        "GCMP-256": 5,
        "CCMP-256": 10,
    }

    WPS_PENALTY = 25
    CLIENT_BONUS = 5
    SIGNAL_BONUS = 5

    def __init__(self):
        self.scores: Dict[str, Dict[str, Any]] = {}
        self.cve_db: Dict[str, List[str]] = self._load_cve_db()

    def _load_cve_db(self) -> Dict[str, List[str]]:
        """Load known vulnerability database."""
        return {
            "TP-Link": ["CVE-2022-30075", "CVE-2020-36158"],
            "Netgear": ["CVE-2021-35973", "CVE-2020-26919"],
            "D-Link": ["CVE-2021-27245", "CVE-2020-24581"],
            "Linksys": ["CVE-2021-35392", "CVE-2021-35393"],
            "ASUS": ["CVE-2021-32030", "CVE-2021-32031"],
            "Huawei": ["CVE-2022-2486", "CVE-2021-40119"],
            "Belkin": ["CVE-2018-11401", "CVE-2019-13261"],
            "Ubiquiti": ["CVE-2021-22909"],
            "Cisco": ["CVE-2022-20699", "CVE-2021-1577"],
        }

    def score(self, target: TargetProfile) -> Dict[str, Any]:
        """
        Calculate vulnerability score for a target AP.

        Returns:
            Dictionary with total score and breakdown
        """
        breakdown = {}

        # Encryption base score (0-100)
        enc_score = self.ENCRYPTION_SCORES.get(target.encryption.upper(), 50)
        breakdown["encryption"] = enc_score

        # Cipher adjustment
        if target.cipher:
            cipher = target.cipher.upper()
            cipher_bonus = self.CIPHER_SCORES.get(cipher, 0)
            breakdown["cipher"] = cipher_bonus
        else:
            cipher_bonus = 0
            breakdown["cipher"] = 0

        # WPS vulnerability
        wps_score = self.WPS_PENALTY if target.wps else 0
        breakdown["wps"] = wps_score

        # Client density bonus (more clients = higher value target)
        client_score = min(target.clients * self.CLIENT_BONUS, 20)
        breakdown["clients"] = client_score

        # Signal strength bonus (closer = more reliable attack)
        signal_score = 0
        if target.signal > -50:
            signal_score = self.SIGNAL_BONUS
        elif target.signal > -65:
            signal_score = self.SIGNAL_BONUS // 2
        breakdown["signal"] = signal_score

        # CVE exposure
        cve_score = 0
        cves = []
        if target.manufacturer:
            for vendor, vendor_cves in self.cve_db.items():
                if vendor.lower() in target.manufacturer.lower():
                    cve_score += len(vendor_cves) * 5
                    cves.extend(vendor_cves)
        breakdown["cve_exposure"] = min(cve_score, 30)
        breakdown["cves"] = cves

        # Calculate total (cap at 100)
        total = min(100, enc_score + cipher_bonus + wps_score +
                    client_score + signal_score + cve_score)

        result = {
            "bssid": target.bssid,
            "ssid": target.ssid,
            "total_score": total,
            "risk_level": self._risk_level(total),
            "recommended_attack": self._recommend_attack(target, total),
            "breakdown": breakdown,
            "timestamp": time.time(),
        }
        self.scores[target.bssid] = result
        return result

    def _risk_level(self, score: int) -> str:
        """Map score to risk level."""
        if score >= 80:
            return "critical"
        if score >= 60:
            return "high"
        if score >= 40:
            return "medium"
        if score >= 20:
            return "low"
        return "minimal"

    def _recommend_attack(self, target: TargetProfile, score: int) -> str:
        """Recommend attack vector based on target profile."""
        if target.encryption.upper() == "OPN":
            return "traffic_intercept"
        if target.encryption.upper() == "WEP":
            return "wep_crack"
        if target.wps:
            return "wps_pixie"
        if target.encryption.upper() in ("WPA", "WPA2"):
            if target.clients > 0:
                return "deauth_handshake"
            return "evil_twin"
        if target.encryption.upper() == "WPA3":
            return "dragonblood"
        return "recon"

    def get_ranked_targets(self) -> List[Dict[str, Any]]:
        """Get all scored targets sorted by score descending."""
        return sorted(
            self.scores.values(),
            key=lambda x: x["total_score"],
            reverse=True,
        )

    def export_scores(self, filepath: str) -> bool:
        """Export scores to JSON file."""
        try:
            with open(filepath, "w") as f:
                json.dump(self.get_ranked_targets(), f, indent=2)
            return True
        except Exception as e:
            print(f"[Scorer] Export error: {e}")
            return False
