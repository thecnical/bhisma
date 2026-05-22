"""
Autonomous Orchestrator
=======================
Main autonomous attack chain executor.
"""

import time
import threading
from typing import Dict, Any, Optional

from rich.console import Console

from bhisma.core.config import BhismaConfig
from bhisma.core.engine import BhismaEngine
from bhisma.core.state_machine import AttackStateMachine, AttackEvent
from bhisma.wifi.recon import ReconManager
from bhisma.brain.orchestrator import LLMOrchestrator

console = Console()


class AutonomousOrchestrator:
    """Executes fully autonomous attack chains."""

    def __init__(self, config: BhismaConfig, recon: ReconManager):
        self.config = config
        self.recon = recon
        self.engine = BhismaEngine(config)
        self.ai = LLMOrchestrator(config)
        self.state_machine = AttackStateMachine()
        self.max_consecutive_failures = 3
        self._consecutive_failures = 0
        self._stop_flag = threading.Event()

    def run(self, target: Dict[str, Any], iface: str) -> None:
        """
        Run full autonomous attack chain on target.

        Args:
            target: Selected target dict
            iface: Monitor mode interface
        """
        session = self.engine.start_session(target)
        self.state_machine.reset()
        self.state_machine.transition(AttackEvent.START)

        console.print(f"\n[bold red]╔══════════════════════════════════════════════════╗[/bold red]")
        console.print(f"[bold red]║     AUTONOMOUS ATTACK CHAIN INITIATED            ║[/bold red]")
        console.print(f"[bold red]╚══════════════════════════════════════════════════╝[/bold red]\n")

        # Phase 0: Deep Recon
        self._run_phase("recon", target, iface, {"duration": 30})

        # Phase 1: AI Strategy
        try:
            from bhisma.brain.agents.strategist import AttackStrategist
            strategist = AttackStrategist(self.ai)
            strategy = strategist.generate_strategy(target)
            console.print(f"[bold cyan][AI] Strategy: {strategy.get('estimated_success', 0)*100:.0f}% success prob | {strategy.get('estimated_time_seconds', 0)}s estimated[/bold cyan]")
            for ph in strategy.get("phases", []):
                console.print(f"[dim]    -> {ph.get('phase')}: {ph.get('tools')} ({ph.get('duration_sec')}s)[/dim]")
        except Exception as e:
            console.print(f"[yellow][AI] Strategy generation failed: {e}[/yellow]")

        # Execute attack chain based on target profile
        enc = target.get("encryption", "").lower()

        if "wep" in enc:
            self._run_phase("wep", target, iface)
        elif "wpa3" in enc or "sae" in enc:
            self._run_phase("deauth", target, iface, {"silent": True})
            self._run_phase("harvest", target, iface)
            self._run_phase("crack", target, iface)
            self._run_phase("evil_twin", target, iface) if not self._has_success() else None
        elif "wpa2" in enc:
            if target.get("wps", False):
                self._run_phase("wps", target, iface)
            self._run_phase("deauth", target, iface, {"silent": True})
            self._run_phase("harvest", target, iface)
            self._run_phase("crack", target, iface)
            if not self._has_success():
                self._run_phase("evil_twin", target, iface, {"portal": True})
        else:
            self._run_phase("evil_twin", target, iface)

        # Post-compromise
        if self._has_success():
            self._run_phase("mitm", target, iface)
            self._run_phase("persist", target, iface)

        self.state_machine.transition(AttackEvent.TIMEOUT)
        self.engine.end_session(session.session_id)

        console.print(f"\n[bold green]╔══════════════════════════════════════════════════╗[/bold green]")
        console.print(f"[bold green]║     AUTONOMOUS CHAIN COMPLETE                    ║[/bold green]")
        console.print(f"[bold green]╚══════════════════════════════════════════════════╝[/bold green]")

    def _run_phase(self, phase: str, target: Dict, iface: str, params: Optional[Dict] = None) -> None:
        """Execute a single phase with failure tracking."""
        if self._stop_flag.is_set():
            return

        params = params or {}
        result = self.engine.execute_phase(phase, target, iface, params)

        if result.get("status") == "success":
            self._consecutive_failures = 0
        else:
            self._consecutive_failures += 1

        if self._consecutive_failures >= self.max_consecutive_failures:
            console.print("[bold red][!] Max consecutive failures reached. Aborting chain.[/bold red]")
            self._stop_flag.set()

    def _has_success(self) -> bool:
        """Check if any phase succeeded."""
        session = self.engine._current_session
        if session:
            return len(session.phases_completed) > 0
        return False

    def stop(self) -> None:
        """Stop the autonomous chain."""
        self._stop_flag.set()
