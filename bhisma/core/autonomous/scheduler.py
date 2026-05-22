"""
Attack Scheduler
================
Time-aware attack scheduling for autonomous mode.
"""

import time
from typing import Dict, Any, Optional

from bhisma.core.config import BhismaConfig
from bhisma.core.autonomous.target_queue import TargetQueue
from bhisma.core.autonomous.rules import RuleEngine

from rich.console import Console

console = Console()


class AttackScheduler:
    """Schedules and executes attacks in autonomous mode."""

    def __init__(self, config: BhismaConfig):
        self.config = config
        self.queue = TargetQueue()
        self.rules = RuleEngine(config.autonomous.rules_file)
        self.last_tick = 0
        self.active_attacks = 0
        self.max_concurrent = config.autonomous.max_concurrent_attacks

    def tick(self) -> None:
        """Process one scheduler tick."""
        now = time.time()
        if now - self.last_tick < self.config.autonomous.daemon_poll_interval:
            return
        self.last_tick = now

        # Check for targets to process
        if self.active_attacks < self.max_concurrent:
            target = self.queue.get_next()
            if target:
                self._process_target(target)

    def _process_target(self, target: Dict[str, Any]) -> None:
        """Process a target from the queue."""
        console.print(f"[dim][AUTO] Processing target: {target.get('ssid', target['bssid'])}[/dim]")
        # Apply rules
        actions = self.rules.evaluate(target)
        for action in actions:
            console.print(f"[dim]    Rule action: {action}[/dim]")
        self.active_attacks += 1
        # In real implementation, spawn attack thread
        # For now, just simulate
        self.active_attacks -= 1
