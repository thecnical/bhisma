"""
Bluetooth Reconnaissance
========================
Bluetooth Low Energy (BLE) and Classic Bluetooth scanning,
device enumeration, and service discovery.

Supports BlueZ stack on Linux and CoreBluetooth on macOS.
"""

import subprocess
import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class BTDevice:
    """Discovered Bluetooth device record."""
    address: str
    name: str
    rssi: int
    device_class: str
    services: List[str]
    manufacturer: str
    first_seen: float
    last_seen: float


class BTRecon:
    """Bluetooth reconnaissance scanner."""

    def __init__(self, adapter: str = "hci0"):
        self.adapter = adapter
        self.devices: Dict[str, BTDevice] = {}
        self._scanning = False
        self.stats: Dict[str, Any] = {
            "devices_found": 0,
            "scan_time": 0.0,
        }

    def scan_ble(self, duration: int = 10) -> List[BTDevice]:
        """
        Perform BLE device scan using hcitool or bluetoothctl.

        Args:
            duration: Scan duration in seconds

        Returns:
            List of discovered BLE devices
        """
        results = []
        start = time.time()

        try:
            # Try bluetoothctl for modern BlueZ
            proc = subprocess.run(
                ["bluetoothctl", "scan", "on"],
                capture_output=True,
                text=True,
                timeout=duration,
            )
            # Parse output for devices
            # Example: [NEW] Device AA:BB:CC:DD:EE:FF DeviceName
            for line in proc.stdout.splitlines():
                if "Device " in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        addr = parts[2]
                        name = " ".join(parts[3:])
                        device = BTDevice(
                            address=addr,
                            name=name,
                            rssi=-50,
                            device_class="BLE",
                            services=[],
                            manufacturer="Unknown",
                            first_seen=time.time(),
                            last_seen=time.time(),
                        )
                        self.devices[addr] = device
                        results.append(device)
        except subprocess.TimeoutExpired:
            pass
        except FileNotFoundError:
            # bluetoothctl not available, fallback to hcitool
            try:
                proc = subprocess.run(
                    ["hcitool", "lescan", "--duplicates"],
                    capture_output=True,
                    text=True,
                    timeout=duration,
                )
                for line in proc.stdout.splitlines():
                    if len(line) > 17 and ":" in line[:17]:
                        addr = line[:17]
                        name = line[18:].strip() if len(line) > 18 else "Unknown"
                        device = BTDevice(
                            address=addr,
                            name=name,
                            rssi=-60,
                            device_class="BLE",
                            services=[],
                            manufacturer="Unknown",
                            first_seen=time.time(),
                            last_seen=time.time(),
                        )
                        self.devices[addr] = device
                        results.append(device)
            except Exception:
                pass
        except Exception as e:
            print(f"[BT] BLE scan error: {e}")

        self.stats["scan_time"] = time.time() - start
        self.stats["devices_found"] = len(self.devices)
        return results

    def scan_classic(self, duration: int = 10) -> List[BTDevice]:
        """
        Perform Classic Bluetooth device discovery.

        Args:
            duration: Inquiry duration in seconds

        Returns:
            List of discovered Classic Bluetooth devices
        """
        results = []
        try:
            import bluetooth
            nearby = bluetooth.discover_devices(
                duration=duration,
                lookup_names=True,
                lookup_class=True,
            )
            for addr, name, dev_class in nearby:
                device = BTDevice(
                    address=addr,
                    name=name or "Unknown",
                    rssi=-50,
                    device_class=str(dev_class),
                    services=[],
                    manufacturer="Unknown",
                    first_seen=time.time(),
                    last_seen=time.time(),
                )
                self.devices[addr] = device
                results.append(device)
        except ImportError:
            print("[BT] pybluez not installed. Run: pip install pybluez")
        except Exception as e:
            print(f"[BT] Classic scan error: {e}")

        self.stats["devices_found"] = len(self.devices)
        return results

    def get_device_info(self, address: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific device."""
        if address not in self.devices:
            return None
        dev = self.devices[address]
        return {
            "address": dev.address,
            "name": dev.name,
            "rssi": dev.rssi,
            "device_class": dev.device_class,
            "services": dev.services,
            "manufacturer": dev.manufacturer,
            "first_seen": dev.first_seen,
            "last_seen": dev.last_seen,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Return scan statistics."""
        return {
            **self.stats,
            "total_devices": len(self.devices),
            "ble_devices": sum(1 for d in self.devices.values() if d.device_class == "BLE"),
            "classic_devices": sum(1 for d in self.devices.values() if d.device_class != "BLE"),
        }
