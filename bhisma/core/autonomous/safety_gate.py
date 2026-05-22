"""
Safety Gate
===========
Whitelist/blacklist and safety controls for autonomous mode.
"""

import re
from typing import Dict, Any, List, Optional, Set


class SafetyGate:
    """Prevents attacks on critical/sensitive networks."""

    def __init__(self, whitelist: Optional[List[str]] = None, blacklist: Optional[List[str]] = None):
        self.whitelist: Set[str] = set(w.upper() for w in (whitelist or []))
        self.blacklist: Set[str] = set(b.upper() for b in (blacklist or []))
        self.critical_patterns = [
            "police", "hospital", "emergency", "911", "dispatch",
            "medical", "ambulance", "fire", "rescue",
        ]

    def is_safe(self, target: Dict[str, Any]) -> bool:
        """
        Check if target is safe to attack.

        Returns:
            True if attack is permitted
        """
        bssid = target.get("bssid", "").upper()
        ssid = target.get("ssid", "").lower()

        # Blacklist check
        if bssid in self.blacklist:
            return False
        if any(pattern in ssid for pattern in self.critical_patterns):
            return False

        # Whitelist check (if whitelist exists, only attack whitelisted)
        if self.whitelist and bssid not in self.whitelist:
            return False

        return True

    def block(self, bssid: str) -> None:
        """Add BSSID to blacklist."""
        self.blacklist.add(bssid.upper())

    def allow(self, bssid: str) -> None:
        """Add BSSID to whitelist."""
        self.whitelist.add(bssid.upper())

    def is_blocked(self, bssid: str) -> bool:
        """Check if BSSID is blocked."""
        return bssid.upper() in self.blacklist
