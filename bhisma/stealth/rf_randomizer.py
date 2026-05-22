"""
RF Signature Randomization
==========================
Randomizes transmit power, rate, and timing to evade RF fingerprinting.
"""

import random


class RFRandomizer:
    """Randomizes RF characteristics to avoid RF-based detection."""

    def __init__(self, power_variance: float = 2.0, rate_variance: int = 6):
        self.power_variance = power_variance
        self.rate_variance = rate_variance
        self.base_power = 20  # dBm
        self.base_rate = 54   # Mbps

    def randomize_power(self, base: Optional[int] = None) -> int:
        """Generate randomized transmit power."""
        b = base or self.base_power
        variance = random.uniform(-self.power_variance, self.power_variance)
        return max(1, min(30, int(b + variance)))

    def randomize_rate(self, base: Optional[int] = None) -> int:
        """Generate randomized data rate."""
        b = base or self.base_rate
        valid_rates = [1, 2, 5, 6, 9, 11, 12, 18, 24, 36, 48, 54]
        # Find closest valid rate
        closest = min(valid_rates, key=lambda x: abs(x - b))
        idx = valid_rates.index(closest)
        jitter = random.randint(-1, 1)
        new_idx = max(0, min(len(valid_rates) - 1, idx + jitter))
        return valid_rates[new_idx]

    def randomize_timing(self, base_ms: float = 100.0) -> float:
        """Add micro-jitter to timing."""
        jitter = random.uniform(-0.05, 0.05)
        return max(0.01, base_ms + jitter)
