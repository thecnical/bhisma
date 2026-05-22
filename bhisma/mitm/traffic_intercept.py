"""
Traffic Interceptor
===================
Passive and active traffic interception with content extraction.

Captures HTTP/HTTPS traffic, extracts credentials, files, and
session data. Supports real-time streaming to dashboard.
"""

import re
import json
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict


@dataclass
class CapturedFlow:
    """Intercepted network flow record."""
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    method: Optional[str]
    host: Optional[str]
    path: Optional[str]
    request_headers: Dict[str, str]
    request_body: Optional[str]
    response_code: Optional[int]
    response_headers: Dict[str, str]
    response_body: Optional[str]
    timestamp: float
    content_type: Optional[str]


class TrafficInterceptor:
    """Network traffic interception and analysis engine."""

    CREDITCARD_PATTERN = re.compile(r'\b(?:\d{4}[- ]?){3}\d{4}\b')
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PASSWORD_FIELDS = re.compile(r'(?:password|passwd|pwd)["\']?\s*[:=]\s*["\']?([^"\'\s&]+)', re.I)
    TOKEN_PATTERN = re.compile(r'(?:token|api_key|secret)["\']?\s*[:=]\s*["\']?([A-Za-z0-9_-]{20,})', re.I)

    def __init__(self, iface: str):
        self.iface = iface
        self.flows: List[CapturedFlow] = []
        self.credentials_found: List[Dict[str, Any]] = []
        self._callbacks: List[Callable[[CapturedFlow], None]] = []
        self._running = False
        self.stats = {
            "flows_captured": 0,
            "credentials_extracted": 0,
            "files_extracted": 0,
        }

    def register_callback(self, cb: Callable[[CapturedFlow], None]) -> None:
        """Register a callback for new flows."""
        self._callbacks.append(cb)

    def analyze_payload(self, flow: CapturedFlow) -> List[Dict[str, Any]]:
        """
        Analyze flow payload for sensitive data.

        Returns:
            List of extracted credential dictionaries
        """
        findings = []
        payload = ""

        if flow.request_body:
            payload += flow.request_body
        if flow.response_body:
            payload += flow.response_body

        # Search for credit cards
        for match in self.CREDITCARD_PATTERN.finditer(payload):
            findings.append({
                "type": "credit_card",
                "value": match.group(),
                "host": flow.host,
                "timestamp": flow.timestamp,
            })

        # Search for emails
        for match in self.EMAIL_PATTERN.finditer(payload):
            findings.append({
                "type": "email",
                "value": match.group(),
                "host": flow.host,
                "timestamp": flow.timestamp,
            })

        # Search for passwords
        for match in self.PASSWORD_FIELDS.finditer(payload):
            findings.append({
                "type": "password",
                "value": match.group(1),
                "host": flow.host,
                "timestamp": flow.timestamp,
            })

        # Search for tokens
        for match in self.TOKEN_PATTERN.finditer(payload):
            findings.append({
                "type": "token",
                "value": match.group(1),
                "host": flow.host,
                "timestamp": flow.timestamp,
            })

        self.credentials_found.extend(findings)
        self.stats["credentials_extracted"] += len(findings)
        return findings

    def add_flow(self, flow: CapturedFlow) -> None:
        """Add a captured flow and trigger analysis."""
        self.flows.append(flow)
        self.stats["flows_captured"] += 1
        self.analyze_payload(flow)
        for cb in self._callbacks:
            try:
                cb(flow)
            except Exception:
                pass

    def get_flows(self, host_filter: Optional[str] = None,
                  method_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get captured flows with optional filtering."""
        results = []
        for f in self.flows:
            if host_filter and host_filter.lower() not in (f.host or "").lower():
                continue
            if method_filter and f.method != method_filter.upper():
                continue
            results.append(asdict(f))
        return results

    def export_flows(self, filepath: str) -> bool:
        """Export all flows to JSON file."""
        try:
            with open(filepath, "w") as f:
                json.dump(self.get_flows(), f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"[Traffic] Export error: {e}")
            return False

    def clear(self) -> None:
        """Clear all captured flows and credentials."""
        self.flows.clear()
        self.credentials_found.clear()
        self.stats["flows_captured"] = 0
        self.stats["credentials_extracted"] = 0

    def get_stats(self) -> Dict[str, Any]:
        """Return interception statistics."""
        return {
            **self.stats,
            "total_flows": len(self.flows),
            "total_credentials": len(self.credentials_found),
        }
