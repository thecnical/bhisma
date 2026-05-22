"""
Helper Utilities
================
Common utility functions used across Bhisma.
"""

import os
import re
import time
import hashlib
import random
import string
from typing import Optional, List, Dict, Any
from datetime import datetime


def generate_mac(oui: Optional[str] = None) -> str:
    """Generate a random MAC address, optionally within a given OUI."""
    if oui:
        oui_clean = oui.replace(":", "").replace("-", "").upper()
        suffix = "".join(f"{random.randint(0, 255):02X}" for _ in range(3))
        mac = oui_clean + suffix
    else:
        mac = "".join(f"{random.randint(0, 255):02X}" for _ in range(6))
    return ":".join(mac[i : i + 2] for i in range(0, 12, 2))


def random_string(length: int = 8) -> str:
    """Generate a random alphanumeric string."""
    return "".join(
        random.choices(string.ascii_letters + string.digits, k=length)
    )


def timestamp() -> str:
    """Current ISO timestamp."""
    return datetime.utcnow().isoformat() + "Z"


def now_epoch() -> float:
    """Current Unix timestamp."""
    return time.time()


def format_mac(mac: str) -> str:
    """Normalize MAC address to colon-separated upper case."""
    clean = re.sub(r"[^0-9A-Fa-f]", "", mac).upper()
    if len(clean) != 12:
        raise ValueError("Invalid MAC address length")
    return ":".join(clean[i : i + 2] for i in range(0, 12, 2))


def mac_to_oui(mac: str) -> str:
    """Extract OUI from MAC address."""
    return format_mac(mac)[:8]


def signal_to_dbm(signal: int) -> int:
    """Convert raw signal value (e.g. from radiotap) to dBm."""
    if signal > 127:
        signal = signal - 256
    return signal


def channel_to_frequency(channel: int) -> float:
    """Convert 802.11 channel to frequency in GHz."""
    if 1 <= channel <= 14:
        if channel == 14:
            return 2.484
        return 2.407 + 0.005 * (channel - 1)
    elif 36 <= channel <= 165:
        return 5.0 + 0.005 * channel
    elif 1 <= channel <= 233:
        return 5.95 + 0.005 * channel
    return 0.0


def sanitize_filename(name: str) -> str:
    """Sanitize a string for use as a filename."""
    return re.sub(r"[^\w\-]", "_", name)


def ensure_dir(path: str) -> str:
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)
    return path


def file_hash(filepath: str, algo: str = "md5") -> str:
    """Compute file hash."""
    h = hashlib.new(algo)
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_oui_db(oui_text: str) -> Dict[str, str]:
    """Parse IEEE OUI database text into dict."""
    ouis = {}
    for line in oui_text.splitlines():
        match = re.match(r"^([0-9A-Fa-f]{2}-[0-9A-Fa-f]{2}-[0-9A-Fa-f]{2})\s+(.+)", line)
        if match:
            ouis[match.group(1).upper()] = match.group(2).strip()
    return ouis


def chunk_list(lst: List[Any], size: int) -> List[List[Any]]:
    """Split a list into chunks of given size."""
    return [lst[i : i + size] for i in range(0, len(lst), size)]


def retry(max_retries: int = 3, delay: float = 1.0):
    """Decorator for retrying a function with exponential backoff."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(delay * (2 ** attempt))
            return None
        return wrapper
    return decorator


def rate_limit(interval: float = 1.0):
    """Decorator for simple rate limiting."""
    last_call = [0.0]
    def decorator(func):
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_call[0]
            if elapsed < interval:
                time.sleep(interval - elapsed)
            last_call[0] = time.time()
            return func(*args, **kwargs)
        return wrapper
    return decorator


def human_readable_size(size_bytes: int) -> str:
    """Convert bytes to human readable string."""
    if size_bytes == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    idx = 0
    while size_bytes >= 1024 and idx < len(units) - 1:
        size_bytes /= 1024
        idx += 1
    return f"{size_bytes:.2f} {units[idx]}"


def is_multicast_mac(mac: str) -> bool:
    """Check if MAC is multicast."""
    clean = format_mac(mac)
    first_octet = int(clean[:2], 16)
    return (first_octet & 0x01) != 0


def is_broadcast_mac(mac: str) -> bool:
    """Check if MAC is broadcast."""
    return format_mac(mac).upper() == "FF:FF:FF:FF:FF:FF"


def parse_rssi_color(rssi: int) -> str:
    """Return color string for RSSI value."""
    if rssi >= -50:
        return "green"
    elif rssi >= -65:
        return "yellow"
    elif rssi >= -80:
        return "orange"
    return "red"
