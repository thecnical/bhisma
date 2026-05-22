"""
WiFi Reconnaissance Module
==========================
Passive scanning, hidden SSID discovery, and target profiling.
"""

import os
import time
import json
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

try:
    from scapy.all import sniff, Dot11, Dot11Beacon, Dot11Elt, Dot11ProbeReq, Dot11ProbeResp
    from scapy.all import RadioTap, Dot11Auth, Dot11AssoReq, Dot11Deauth
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False

from bhisma.core.config import BhismaConfig
from bhisma.utils.constants import (
    CHANNELS_2_4_GHZ, CHANNELS_5_GHZ, CHANNELS_6_GHZ,
    DOT11_TYPE_MANAGEMENT, DOT11_SUBTYPE_BEACON,
    DOT11_SUBTYPE_PROBE_REQ, DOT11_SUBTYPE_PROBE_RESP,
    DOT11_SUBTYPE_DEAUTH, COMMON_OUIS,
)
from bhisma.utils.helpers import format_mac, mac_to_oui, signal_to_dbm, now_epoch
from bhisma.utils.platform import PLATFORM

console = Console()


@dataclass
class AccessPoint:
    """Discovered access point profile."""
    bssid: str
    ssid: str = ""
    channel: int = 0
    signal: int = -100
    encryption: str = "OPEN"
    cipher: str = ""
    auth: str = ""
    wps: bool = False
    wpa3: bool = False
    wifi6: bool = False
    mesh: bool = False
    hidden: bool = False
    vendor: str = "Unknown"
    beacon_interval: int = 0
    rates: List[int] = field(default_factory=list)
    clients: List[str] = field(default_factory=list)
    first_seen: float = field(default_factory=now_epoch)
    last_seen: float = field(default_factory=now_epoch)
    probe_requests: List[str] = field(default_factory=list)
    score: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WiFiClient:
    """Discovered WiFi client profile."""
    mac: str
    vendor: str = "Unknown"
    probed_networks: List[str] = field(default_factory=list)
    associated_bssid: Optional[str] = None
    signal: int = -100
    first_seen: float = field(default_factory=now_epoch)
    last_seen: float = field(default_factory=now_epoch)


class ReconManager:
    """Manages WiFi reconnaissance operations."""

    def __init__(self, iface: str, config: Optional[BhismaConfig] = None):
        self.iface = iface
        self.config = config or BhismaConfig.load()
        self.aps: Dict[str, AccessPoint] = {}
        self.clients: Dict[str, WiFiClient] = {}
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def scan_networks(
        self,
        bands: Optional[List[str]] = None,
        duration: int = 30,
        broadcast: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Actively scan for networks using channel hopping.

        Args:
            bands: List of bands ("2.4", "5", "6")
            duration: Scan duration in seconds
            broadcast: Send results to dashboard

        Returns:
            List of AP dictionaries sorted by score
        """
        if not SCAPY_AVAILABLE:
            console.print("[bold red][!] Scapy not installed. Install: pip install scapy[/bold red]")
            return self._demo_scan()

        channels = self._resolve_channels(bands)
        console.print(f"[bold cyan][*] Scanning {len(channels)} channels for {duration}s...[/bold cyan]")

        # Start packet capture thread
        capture_thread = threading.Thread(
            target=self._packet_capture,
            args=(duration,),
            daemon=True,
        )
        capture_thread.start()

        # Channel hop
        hop_thread = threading.Thread(
            target=self._channel_hop,
            args=(channels, duration),
            daemon=True,
        )
        hop_thread.start()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
        ) as progress:
            task = progress.add_task(f"Scanning {len(channels)} channels...", total=duration)
            for _ in range(duration):
                time.sleep(1)
                progress.advance(task)
                with self._lock:
                    count = len(self.aps)
                progress.update(task, description=f"Found {count} networks")

        self._stop_event.set()
        capture_thread.join(timeout=2)
        hop_thread.join(timeout=2)

        with self._lock:
            self._score_aps()
            results = [ap.to_dict() for ap in sorted(self.aps.values(), key=lambda a: a.score, reverse=True)]

        # Broadcast to dashboard
        if broadcast:
            self._broadcast_targets(results)

        return results

    def passive_recon(self, duration: int = 60) -> Dict[str, List[Dict]]:
        """
        Passive reconnaissance — just listen without transmitting.

        Returns:
            Dict with 'aps' and 'clients' lists
        """
        if not SCAPY_AVAILABLE:
            console.print("[bold red][!] Scapy not installed[/bold red]")
            return {"aps": [], "clients": []}

        console.print(f"[bold cyan][*] Passive recon for {duration}s...[/bold cyan]")
        self._stop_event.clear()

        def packet_handler(pkt):
            self._process_packet(pkt)

        sniff_thread = threading.Thread(
            target=lambda: sniff(
                iface=self.iface,
                prn=packet_handler,
                stop_filter=lambda x: self._stop_event.is_set(),
                timeout=duration,
            ),
            daemon=True,
        )
        sniff_thread.start()
        time.sleep(duration)
        self._stop_event.set()
        sniff_thread.join(timeout=2)

        with self._lock:
            self._score_aps()
            return {
                "aps": [ap.to_dict() for ap in self.aps.values()],
                "clients": [{"mac": c.mac, "vendor": c.vendor, "probed": c.probed_networks}
                            for c in self.clients.values()],
            }

    def discover_hidden_ssid(self, target_bssid: str) -> Optional[str]:
        """
        Attempt to discover hidden SSID by observing client associations
        or sending a deauth to force a reconnection.

        Returns:
            Discovered SSID or None
        """
        if target_bssid not in self.aps:
            return None
        ap = self.aps[target_bssid]
        if ap.ssid:
            return ap.ssid  # Already known

        # Force client to reconnect by sending deauth
        console.print(f"[yellow][*] Attempting hidden SSID discovery for {target_bssid}[/yellow]")
        try:
            from scapy.all import RadioTap, Dot11, Dot11Deauth
            pkt = RadioTap() / Dot11(
                addr1="ff:ff:ff:ff:ff:ff",
                addr2=target_bssid,
                addr3=target_bssid,
            ) / Dot11Deauth(reason=7)
            # Send 1-2 deauth packets
            for _ in range(2):
                pkt.send(iface=self.iface, verbose=0)
                time.sleep(0.5)
        except Exception:
            pass

        # Wait and listen for probe requests/assoc with SSID
        time.sleep(3)
        with self._lock:
            if ap.ssid:
                return ap.ssid
        return None

    def _packet_capture(self, duration: int) -> None:
        """Background packet capture."""
        try:
            sniff(
                iface=self.iface,
                prn=self._process_packet,
                stop_filter=lambda x: self._stop_event.is_set(),
                timeout=duration,
            )
        except Exception as e:
            console.print(f"[red]Capture error: {e}[/red]")

    def _channel_hop(self, channels: List[int], duration: int) -> None:
        """Channel hopping thread."""
        start = time.time()
        idx = 0
        while time.time() - start < duration and not self._stop_event.is_set():
            ch = channels[idx % len(channels)]
            try:
                if PLATFORM.is_linux:
                    import subprocess
                    subprocess.run(
                        ["iw", "dev", self.iface, "set", "channel", str(ch)],
                        capture_output=True,
                        check=False,
                    )
                elif PLATFORM.is_macos:
                    import subprocess
                    subprocess.run(
                        ["sudo", "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-c", str(ch)],
                        capture_output=True,
                        check=False,
                    )
            except Exception:
                pass
            idx += 1
            time.sleep(self.config.wifi.dwell_time)

    def _process_packet(self, pkt) -> None:
        """Process a captured 802.11 packet."""
        try:
            if not pkt.haslayer(Dot11):
                return

            dot11 = pkt[Dot11]
            bssid = format_mac(dot11.addr3) if dot11.addr3 else "00:00:00:00:00:00"

            # Beacon frame
            if pkt.haslayer(Dot11Beacon):
                self._process_beacon(pkt, bssid)

            # Probe Request
            elif dot11.type == DOT11_TYPE_MANAGEMENT and dot11.subtype == DOT11_SUBTYPE_PROBE_REQ:
                self._process_probe_req(pkt)

            # Probe Response
            elif dot11.type == DOT11_TYPE_MANAGEMENT and dot11.subtype == DOT11_SUBTYPE_PROBE_RESP:
                self._process_probe_resp(pkt, bssid)

            # Deauth / Disassoc
            elif dot11.type == DOT11_TYPE_MANAGEMENT and dot11.subtype == DOT11_SUBTYPE_DEAUTH:
                pass  # Log if needed

        except Exception:
            pass

    def _process_beacon(self, pkt, bssid: str) -> None:
        """Extract info from beacon frame."""
        try:
            ssid = ""
            channel = 0
            enc = "OPEN"
            cipher = ""
            auth = ""
            wps = False
            wpa3 = False
            wifi6 = False
            mesh = False
            rates = []

            # SSID
            if pkt.haslayer(Dot11Elt):
                elt = pkt[Dot11Elt]
                while elt:
                    if elt.ID == 0:  # SSID
                        try:
                            ssid = elt.info.decode("utf-8", errors="ignore")
                        except Exception:
                            ssid = ""
                    elif elt.ID == 3:  # DS Parameter (channel)
                        channel = int(elt.info[0]) if elt.info else 0
                    elif elt.ID == 1:  # Supported Rates
                        rates = list(elt.info)
                    elif elt.ID == 50:  # Extended Supported Rates
                        rates.extend(list(elt.info))
                    elif elt.ID == 48:  # RSN IE
                        enc = "WPA2"
                        if len(elt.info) > 6:
                            # Check for SAE (WPA3)
                            if b"\x00\x0f\xac\x08" in bytes(elt.info):
                                wpa3 = True
                                enc = "WPA3"
                    elif elt.ID == 221:  # Vendor Specific
                        if b"\x00\x50\xf2\x04" in bytes(elt.info[:4]):
                            wps = True
                        if b"\x00\x90\x4c" in bytes(elt.info[:3]):
                            wifi6 = True
                    elif elt.ID == 113:  # Mesh ID
                        mesh = True
                    elt = elt.payload.getlayer(Dot11Elt)

            # Signal
            signal = -100
            if pkt.haslayer(RadioTap):
                try:
                    rt = pkt[RadioTap]
                    if hasattr(rt, "dBm_AntSignal"):
                        signal = rt.dBm_AntSignal
                except Exception:
                    pass

            with self._lock:
                if bssid not in self.aps:
                    self.aps[bssid] = AccessPoint(
                        bssid=bssid,
                        ssid=ssid if ssid else "",
                        hidden=not ssid,
                        vendor=self._lookup_vendor(bssid),
                    )
                ap = self.aps[bssid]
                if ssid and not ap.ssid:
                    ap.ssid = ssid
                    ap.hidden = False
                if channel:
                    ap.channel = channel
                if signal > ap.signal:
                    ap.signal = signal
                ap.encryption = enc
                ap.wps = wps
                ap.wpa3 = wpa3
                ap.wifi6 = wifi6
                ap.mesh = mesh
                ap.rates = rates
                ap.last_seen = now_epoch()

        except Exception:
            pass

    def _process_probe_req(self, pkt) -> None:
        """Process probe request for client discovery."""
        try:
            client_mac = format_mac(pkt[Dot11].addr2)
            ssid = ""
            if pkt.haslayer(Dot11Elt):
                elt = pkt[Dot11Elt]
                while elt:
                    if elt.ID == 0:
                        try:
                            ssid = elt.info.decode("utf-8", errors="ignore")
                        except Exception:
                            pass
                        break
                    elt = elt.payload.getlayer(Dot11Elt)

            with self._lock:
                if client_mac not in self.clients:
                    self.clients[client_mac] = WiFiClient(
                        mac=client_mac,
                        vendor=self._lookup_vendor(client_mac),
                    )
                client = self.clients[client_mac]
                if ssid and ssid not in client.probed_networks:
                    client.probed_networks.append(ssid)
                client.last_seen = now_epoch()
        except Exception:
            pass

    def _process_probe_resp(self, pkt, bssid: str) -> None:
        """Process probe response."""
        self._process_beacon(pkt, bssid)

    def _lookup_vendor(self, mac: str) -> str:
        """Look up vendor from MAC OUI."""
        oui = mac_to_oui(mac)
        return COMMON_OUIS.get(oui, "Unknown")

    def _score_aps(self) -> None:
        """Score APs by vulnerability and attractiveness."""
        for ap in self.aps.values():
            score = 0
            # Signal strength (closer = better)
            score += max(0, (ap.signal + 30))
            # Encryption weakness
            if "WEP" in ap.encryption.upper():
                score += 100
            elif ap.wps:
                score += 70
            elif "WPA3" in ap.encryption.upper():
                score += 10
            elif "WPA2" in ap.encryption.upper():
                score += 40
            elif "WPA" in ap.encryption.upper():
                score += 50
            # Client count
            score += len(ap.clients) * 15
            # Hidden SSID bonus (interesting target)
            if ap.hidden:
                score += 20
            ap.score = score

    def _resolve_channels(self, bands: Optional[List[str]]) -> List[int]:
        """Resolve band strings to channel lists."""
        if not bands:
            return CHANNELS_2_4_GHZ + CHANNELS_5_GHZ
        channels = []
        for b in bands:
            b = str(b).strip().lower()
            if b in ("2.4", "2.4ghz", "24"):
                channels.extend(CHANNELS_2_4_GHZ)
            elif b in ("5", "5ghz"):
                channels.extend(CHANNELS_5_GHZ)
            elif b in ("6", "6ghz", "6e"):
                channels.extend(CHANNELS_6_GHZ)
        return channels if channels else CHANNELS_2_4_GHZ + CHANNELS_5_GHZ

    def _broadcast_targets(self, targets: List[Dict[str, Any]]) -> None:
        """Broadcast discovered targets to dashboard."""
        try:
            from bhisma.dashboard.websocket import DashboardWebsocket
            for target in targets:
                DashboardWebsocket.broadcast({
                    "type": "target",
                    "data": target,
                })
        except Exception:
            pass

    def _demo_scan(self) -> List[Dict[str, Any]]:
        """Return demo data when scapy is unavailable."""
        console.print("[yellow][!] Scapy not available — returning demo data[/yellow]")
        return [
            {
                "bssid": "AA:BB:CC:DD:EE:01",
                "ssid": "DemoNetwork_5G",
                "channel": 36,
                "signal": -45,
                "encryption": "WPA2",
                "wps": True,
                "clients": 3,
                "score": 85,
                "vendor": "Netgear",
            },
            {
                "bssid": "AA:BB:CC:DD:EE:02",
                "ssid": "CorpWiFi",
                "channel": 6,
                "signal": -55,
                "encryption": "WPA3",
                "wps": False,
                "clients": 12,
                "score": 70,
                "vendor": "Cisco",
            },
            {
                "bssid": "AA:BB:CC:DD:EE:03",
                "ssid": "",
                "channel": 11,
                "signal": -60,
                "encryption": "WPA2",
                "wps": False,
                "clients": 1,
                "score": 55,
                "vendor": "TP-Link",
                "hidden": True,
            },
        ]
