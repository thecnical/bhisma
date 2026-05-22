"""
Daemon Controller
=================
Background process manager for autonomous mode.
"""

import os
import sys
import signal
import time
import json
from typing import Optional

from rich.console import Console

console = Console()

PID_FILE = os.path.expanduser("~/.bhisma/daemon.pid")


class DaemonController:
    """Controls the Bhisma background daemon."""

    def __init__(self):
        self.pid: Optional[int] = None
        self._running = False

    def start(self, config_file: Optional[str] = None) -> bool:
        """Start the background daemon."""
        if self.is_running():
            console.print("[yellow][!] Daemon already running[/yellow]")
            return False

        console.print("[bold green][+] Starting Bhisma daemon...[/bold green]")
        # In a real implementation, this would fork/detach
        # For now, write PID and run main loop
        pid = os.getpid()
        with open(PID_FILE, "w") as f:
            f.write(str(pid))
        self.pid = pid
        self._running = True

        try:
            self._run_main_loop(config_file)
        except KeyboardInterrupt:
            self.stop()
        return True

    def _run_main_loop(self, config_file: Optional[str]) -> None:
        """Main daemon loop."""
        from bhisma.core.autonomous.scheduler import AttackScheduler
        from bhisma.core.config import BhismaConfig

        config = BhismaConfig.load(config_file)
        scheduler = AttackScheduler(config)

        console.print("[dim]Daemon running. Press Ctrl+C to stop.[/dim]")
        while self._running:
            scheduler.tick()
            time.sleep(config.autonomous.daemon_poll_interval)

    def stop(self) -> bool:
        """Stop the background daemon."""
        if not self.is_running():
            console.print("[yellow][!] Daemon not running[/yellow]")
            return False

        try:
            with open(PID_FILE, "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
            console.print(f"[bold green][+] Daemon stopped (PID {pid})[/bold green]")
        except (ProcessLookupError, ValueError):
            console.print("[yellow][!] Daemon process not found[/yellow]")
        finally:
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
            self._running = False
            self.pid = None
        return True

    def status(self) -> None:
        """Show daemon status."""
        if self.is_running():
            with open(PID_FILE, "r") as f:
                pid = f.read().strip()
            console.print(f"[bold green][+] Daemon running (PID: {pid})[/bold green]")
        else:
            console.print("[bold red][!] Daemon not running[/bold red]")

    def is_running(self) -> bool:
        """Check if daemon is currently running."""
        if not os.path.exists(PID_FILE):
            return False
        try:
            with open(PID_FILE, "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)  # Check if process exists
            return True
        except (OSError, ValueError):
            os.remove(PID_FILE)
            return False


# Alias for compatibility
BhismaDaemon = DaemonController
