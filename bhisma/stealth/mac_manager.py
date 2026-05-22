"""
MAC Address Manager
===================
Rotates MAC addresses while maintaining OUI consistency.
"""

import random
from typing import Optional, Dict

from bhisma.utils.helpers import generate_mac
from bhisma.utils.constants import COMMON_OUIS


class MACManager:
    """Manages MAC address rotation with vendor-family consistency."""

    def __init__(self, oui_consistency: bool = True):
        self.oui_consistency = oui_consistency
        self.current_mac: Optional[str] = None
        self.current_oui: Optional[str] = None
        self.rotation_count = 0

    def rotate(self, target_vendor: Optional[str] = None) -> str:
        """Generate a new MAC, optionally matching a vendor OUI."""
        if target_vendor and self.oui_consistency:
            oui = self._find_oui_by_vendor(target_vendor)
            if oui:
                self.current_oui = oui
                self.current_mac = generate_mac(oui=oui)
                self.rotation_count += 1
                return self.current_mac

        # Random MAC with random OUI
        self.current_mac = generate_mac()
        self.current_oui = self.current_mac[:8]
        self.rotation_count += 1
        return self.current_mac

    def spoof_for_target(self, target_bssid: str) -> str:
        """Spoof a MAC in the same vendor family as target."""
        target_oui = target_bssid[:8].upper()
        vendor = COMMON_OUIS.get(target_oui)
        if vendor and self.oui_consistency:
            return self.rotate(target_vendor=vendor)
        return self.rotate()

    def get_current(self) -> Optional[str]:
        """Get current MAC address."""
        return self.current_mac

    def _find_oui_by_vendor(self, vendor: str) -> Optional[str]:
        """Find an OUI matching the vendor name."""
        vendor_lower = vendor.lower()
        for oui, name in COMMON_OUIS.items():
            if vendor_lower in name.lower():
                return oui
        return None
