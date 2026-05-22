"""
Target Queue
============
Priority queue for autonomous target selection.
"""

import heapq
from typing import Dict, Any, Optional, List


class TargetQueue:
    """Priority queue for attack targets."""

    def __init__(self):
        self._queue: List[tuple] = []  # (priority, counter, target)
        self._counter = 0
        self._seen_bssids: set = set()

    def add(self, target: Dict[str, Any], priority: Optional[float] = None) -> None:
        """Add a target to the queue."""
        bssid = target.get("bssid", "")
        if bssid in self._seen_bssids:
            return
        self._seen_bssids.add(bssid)

        if priority is None:
            priority = self._calculate_priority(target)

        heapq.heappush(self._queue, (-priority, self._counter, target))
        self._counter += 1

    def get_next(self) -> Optional[Dict[str, Any]]:
        """Get the highest priority target."""
        while self._queue:
            _, _, target = heapq.heappop(self._queue)
            return target
        return None

    def peek(self) -> Optional[Dict[str, Any]]:
        """Peek at highest priority target without removing."""
        if self._queue:
            return self._queue[0][2]
        return None

    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return len(self._queue) == 0

    def size(self) -> int:
        """Return queue size."""
        return len(self._queue)

    def clear(self) -> None:
        """Clear all targets."""
        self._queue.clear()
        self._seen_bssids.clear()

    def _calculate_priority(self, target: Dict[str, Any]) -> float:
        """Calculate priority score for a target."""
        score = 0.0
        # Signal strength (closer = higher priority)
        signal = target.get("signal", -100)
        score += max(0, (signal + 100) / 100 * 30)

        # Encryption weakness
        enc = target.get("encryption", "").upper()
        if "WEP" in enc:
            score += 50
        elif target.get("wps", False):
            score += 40
        elif "WPA2" in enc:
            score += 25
        elif "WPA3" in enc:
            score += 5

        # Client count
        clients = target.get("clients", 0)
        score += min(clients * 5, 25)

        # Vulnerability score from ML
        score += target.get("vuln_score", 0) * 0.5

        return score
