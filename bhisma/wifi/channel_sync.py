"""
Channel Synchronization
=======================
Smart channel hopping that follows target AP announcements.
"""

import time
import subprocess
from typing import List, Optional

from bhisma.utils.platform import PLATFORM
from rich.console import Console

console = Console()


class ChannelSync:
    """Synchronizes channel following with target AP behavior."""

    def __init__(self, iface: str):
        self.iface = iface
        self._current_channel = 0
        self._target_channel = None
        self._dwell_history = {}

    def set_channel(self, channel: int) -> bool:
        """Set interface to specific channel."""
        try:
            if PLATFORM.is_linux:
                subprocess.run(
                    ["iw", "dev", self.iface, "set", "channel", str(channel)],
                    capture_output=True,
                    check=False,
                )
            elif PLATFORM.is_macos:
                subprocess.run(
                    ["sudo", "airport", "-c", str(channel)],
                    capture_output=True,
                    check=False,
                )
            self._current_channel = channel
            return True
        except Exception:
            return False

    def follow_target(self, target_channel: int, dwell_time: float = 1.0) -> None:
        """Follow a target AP on its channel."""
        if target_channel != self._current_channel:
            console.print(f"[dim]    Channel sync: {self._current_channel} -> {target_channel}[/dim]")
            self.set_channel(target_channel)
            time.sleep(dwell_time)

    def optimized_hop(
        self,
        channels: List[int],
        target_bssid: Optional[str] = None,
        dwell_time: float = 0.5,
    ) -> None:
        """Hop channels prioritizing target's known channel."""
        if target_bssid and self._target_channel:
            # Prioritize target channel
            ordered = [self._target_channel] + [c for c in channels if c != self._target_channel]
        else:
            ordered = channels

        for ch in ordered:
            self.set_channel(ch)
            time.sleep(dwell_time)

    def record_channel_switch(self, bssid: str, old_ch: int, new_ch: int) -> None:
        """Record a channel switch announcement from AP."""
        console.print(f"[dim]    AP {bssid} switched {old_ch} -> {new_ch}[/dim]")
        self._target_channel = new_ch
        self._dwell_history[bssid] = {"from": old_ch, "to": new_ch, "time": time.time()}
