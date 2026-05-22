"""
Platform Detection & Utilities
============================
Cross-platform helper for OS detection, adapter enumeration,
and monitor mode commands.
"""

import sys
import os
import platform as _platform
import subprocess
import shutil
from typing import List, Dict, Optional, Tuple
from enum import Enum


class PlatformType(Enum):
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "darwin"
    UNKNOWN = "unknown"


class BhismaPlatform:
    """Cross-platform helper for Bhisma framework."""

    def __init__(self):
        self.system = _platform.system().lower()
        if self.system == "windows":
            self.platform_type = PlatformType.WINDOWS
        elif self.system == "linux":
            self.platform_type = PlatformType.LINUX
        elif self.system == "darwin":
            self.platform_type = PlatformType.MACOS
        else:
            self.platform_type = PlatformType.UNKNOWN

    @property
    def os(self) -> str:
        """Return OS name string."""
        return self.system

    @property
    def is_windows(self) -> bool:
        return self.platform_type == PlatformType.WINDOWS

    @property
    def is_linux(self) -> bool:
        return self.platform_type == PlatformType.LINUX

    @property
    def is_macos(self) -> bool:
        return self.platform_type == PlatformType.MACOS

    def detect_adapters(self) -> List[Dict]:
        """Detect wireless network interfaces."""
        adapters = []
        try:
            if self.is_linux:
                adapters = self._detect_linux_adapters()
            elif self.is_macos:
                adapters = self._detect_macos_adapters()
            elif self.is_windows:
                adapters = self._detect_windows_adapters()
        except Exception:
            pass
        return adapters

    def _detect_linux_adapters(self) -> List[Dict]:
        """Use iw/iwconfig to list wireless interfaces."""
        adapters = []
        try:
            result = subprocess.run(
                ["iw", "dev"],
                capture_output=True, text=True, check=False
            )
            if result.returncode == 0 and result.stdout:
                for line in result.stdout.splitlines():
                    if line.strip().startswith("Interface"):
                        iface = line.strip().split()[-1]
                        adapters.append({
                            "name": iface,
                            "monitor_capable": True,
                            "driver": "unknown",
                            "platform": "linux",
                        })
            else:
                result = subprocess.run(
                    ["iwconfig"],
                    capture_output=True, text=True, check=False
                )
                for line in result.stdout.splitlines():
                    if "IEEE 802.11" in line or "802.11" in line:
                        parts = line.split()
                        if parts:
                            iface = parts[0].rstrip(":")
                            adapters.append({
                                "name": iface,
                                "monitor_capable": True,
                                "driver": "unknown",
                                "platform": "linux",
                            })
        except Exception:
            pass
        return adapters

    def _detect_macos_adapters(self) -> List[Dict]:
        """Use airport or networksetup to find WiFi interface."""
        adapters = []
        try:
            result = subprocess.run(
                ["networksetup", "-listallhardwareports"],
                capture_output=True, text=True, check=False
            )
            lines = result.stdout.splitlines()
            iface = None
            for i, line in enumerate(lines):
                if "Wi-Fi" in line or "AirPort" in line:
                    for j in range(i, min(i + 5, len(lines))):
                        if "Device" in lines[j]:
                            iface = lines[j].split(":")[-1].strip()
                            break
                    break
            if iface:
                adapters.append({
                    "name": iface,
                    "monitor_capable": True,
                    "driver": "builtin",
                    "platform": "macos",
                })
        except Exception:
            pass
        return adapters

    def _detect_windows_adapters(self) -> List[Dict]:
        """Use netsh or wmic to find WiFi adapters."""
        adapters = []
        try:
            result = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                capture_output=True, text=True, check=False,
                shell=True,
            )
            if result.returncode == 0 and result.stdout:
                iface = None
                for line in result.stdout.splitlines():
                    if "Name" in line and ":" in line:
                        iface = line.split(":", 1)[-1].strip()
                        adapters.append({
                            "name": iface,
                            "monitor_capable": False,
                            "driver": "unknown",
                            "platform": "windows",
                            "note": "Npcap/WinPcap required for monitor mode",
                        })
        except Exception:
            pass
        return adapters

    def enter_monitor_mode(self, iface: str) -> Tuple[bool, str]:
        """
        Attempt to put interface into monitor mode.
        Returns (success, message_or_new_iface_name).
        """
        if self.is_linux:
            return self._linux_monitor_mode(iface)
        elif self.is_macos:
            return self._macos_monitor_mode(iface)
        elif self.is_windows:
            return self._windows_monitor_mode(iface)
        return False, "Unsupported platform"

    def _linux_monitor_mode(self, iface: str) -> Tuple[bool, str]:
        """Use airmon-ng or iw to enter monitor mode."""
        # Try airmon-ng first
        if shutil.which("airmon-ng"):
            subprocess.run(
                ["airmon-ng", "check", "kill"],
                capture_output=True, check=False
            )
            result = subprocess.run(
                ["airmon-ng", "start", iface],
                capture_output=True, text=True, check=False
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if "monitor mode" in line.lower() and "enabled" in line.lower():
                        # airmon-ng renames interface to iface+mon
                        mon_iface = f"{iface}mon"
                        return True, mon_iface
            # Fallback: use iw directly
            subprocess.run(["ip", "link", "set", iface, "down"], check=False)
            subprocess.run(
                ["iw", "dev", iface, "set", "type", "monitor"],
                capture_output=True, check=False
            )
            subprocess.run(["ip", "link", "set", iface, "up"], check=False)
            return True, iface
        return False, "airmon-ng or iw not available"

    def _macos_monitor_mode(self, iface: str) -> Tuple[bool, str]:
        """Use airport utility for monitor mode on macOS."""
        airport_path = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
        if shutil.which(airport_path):
            subprocess.run([airport_path, "-z"], capture_output=True, check=False)
            # Sniff mode (passive)
            subprocess.run(
                [airport_path, iface, "sniff"],
                capture_output=True, check=False
            )
            return True, iface
        return False, "airport utility not found"

    def _windows_monitor_mode(self, iface: str) -> Tuple[bool, str]:
        """Windows requires Npcap/WinPcap for raw 802.11 capture."""
        if not shutil.which("NpcapHelper.exe") and not self._check_npcap_installed():
            return False, "Npcap not installed. Run: bhisma tools install npcap"
        return True, iface  # Npcap handles monitor mode in userspace

    def _check_npcap_installed(self) -> bool:
        """Check if Npcap driver is present."""
        try:
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Npcap",
            ) as key:
                winreg.QueryValueEx(key, "")  # just check existence
                return True
        except Exception:
            return False

    def exit_monitor_mode(self, iface: str) -> bool:
        """Return interface to managed mode."""
        if self.is_linux:
            if shutil.which("airmon-ng"):
                subprocess.run(
                    ["airmon-ng", "stop", iface],
                    capture_output=True, check=False
                )
                return True
            subprocess.run(["ip", "link", "set", iface, "down"], check=False)
            subprocess.run(
                ["iw", "dev", iface, "set", "type", "managed"],
                capture_output=True, check=False
            )
            subprocess.run(["ip", "link", "set", iface, "up"], check=False)
            return True
        elif self.is_macos:
            return True
        elif self.is_windows:
            return True  # Npcap mode is userspace
        return False

    def run_as_root(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Run command with elevated privileges if needed."""
        if self.is_linux or self.is_macos:
            if os.geteuid() != 0:
                cmd = ["sudo", "-n"] + cmd
        return subprocess.run(cmd, capture_output=True, text=True, check=False)


# Global instance
PLATFORM = BhismaPlatform()
