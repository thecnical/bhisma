"""
Tool Manager
============
Auto-detects, installs, and manages external tool dependencies.
"""

import os
import shutil
import subprocess
import platform as _platform
from typing import Dict, List, Optional, Tuple

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from bhisma.tools.registry import TOOL_REGISTRY, get_tool
from bhisma.utils.platform import PLATFORM
from bhisma.core.config import BhismaConfig

console = Console()


class ToolManager:
    """Manages external tool dependencies for Bhisma."""

    def __init__(self, config: Optional[BhismaConfig] = None):
        self.config = config or BhismaConfig.load()
        self.status_cache: Dict[str, bool] = {}

    def check_all(self) -> Dict[str, bool]:
        """Check all registered tools and print status table."""
        results = {}
        table = Table(title="External Tool Status")
        table.add_column("Tool", style="cyan")
        table.add_column("Category", style="magenta")
        table.add_column("Purpose")
        table.add_column("Status", justify="center")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Checking tools...", total=len(TOOL_REGISTRY))
            for name, meta in TOOL_REGISTRY.items():
                available = self._check_tool(meta.command)
                results[name] = available
                self.status_cache[name] = available
                status = "[bold green]OK[/bold green]" if available else "[bold red]MISSING[/bold red]"
                table.add_row(meta.name, meta.category, meta.purpose, status)
                progress.advance(task)

        console.print(table)
        missing = [k for k, v in results.items() if not v]
        if missing:
            console.print(f"\n[bold yellow][!] {len(missing)} tools missing. Run: bhisma tools install[/bold yellow]")
        else:
            console.print("\n[bold green][+] All tools available[/bold green]")
        return results

    def _check_tool(self, command: str) -> bool:
        """Check if a command exists in PATH."""
        if shutil.which(command):
            return True
        # Also check common Windows extensions
        if PLATFORM.is_windows:
            for ext in [".exe", ".bat", ".cmd"]:
                if shutil.which(command + ext):
                    return True
        return False

    def install_tool(self, tool_name: str) -> bool:
        """Install a specific tool using platform-appropriate method."""
        meta = get_tool(tool_name)
        if not meta:
            console.print(f"[bold red][!] Unknown tool: {tool_name}[/bold red]")
            return False

        if self._check_tool(meta.command):
            console.print(f"[green]{meta.name} already installed[/green]")
            return True

        install_cmd = None
        if PLATFORM.is_linux and meta.install_linux:
            install_cmd = meta.install_linux
        elif PLATFORM.is_macos and meta.install_macos:
            install_cmd = meta.install_macos
        elif PLATFORM.is_windows and meta.install_windows:
            install_cmd = meta.install_windows

        if not install_cmd:
            console.print(f"[yellow][!] No install method for {meta.name} on this platform[/yellow]")
            return False

        console.print(f"[cyan][*] Installing {meta.name}...[/cyan]")
        console.print(f"[dim]    Command: {install_cmd}[/dim]")

        try:
            result = subprocess.run(
                install_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.config.tools.install_timeout,
            )
            if result.returncode == 0 or self._check_tool(meta.command):
                console.print(f"[bold green][+] {meta.name} installed successfully[/bold green]")
                self.status_cache[tool_name] = True
                return True
            else:
                console.print(f"[bold red][!] {meta.name} install failed[/bold red]")
                if result.stderr:
                    console.print(f"[dim]{result.stderr[:500]}[/dim]")
                return False
        except subprocess.TimeoutExpired:
            console.print(f"[bold red][!] {meta.name} install timed out[/bold red]")
            return False
        except Exception as e:
            console.print(f"[bold red][!] {meta.name} install error: {e}[/bold red]")
            return False

    def install_all(self) -> Dict[str, bool]:
        """Install all missing tools."""
        results = {}
        missing = [name for name in TOOL_REGISTRY if not self._check_tool(TOOL_REGISTRY[name].command)]
        if not missing:
            console.print("[bold green][+] All tools already installed[/bold green]")
            return {}

        console.print(f"[bold cyan][*] Installing {len(missing)} missing tools...[/bold cyan]")
        for name in missing:
            results[name] = self.install_tool(name)
        return results

    def get_install_commands(self, tool_name: str) -> Optional[str]:
        """Get the install command for a tool on current platform."""
        meta = get_tool(tool_name)
        if not meta:
            return None
        if PLATFORM.is_linux:
            return meta.install_linux
        elif PLATFORM.is_macos:
            return meta.install_macos
        elif PLATFORM.is_windows:
            return meta.install_windows
        return None

    def ensure_tool(self, tool_name: str) -> bool:
        """Ensure a tool is installed, installing if necessary."""
        if tool_name in self.status_cache and self.status_cache[tool_name]:
            return True
        if self._check_tool(TOOL_REGISTRY[tool_name].command):
            self.status_cache[tool_name] = True
            return True
        if self.config.tools.auto_install:
            return self.install_tool(tool_name)
        return False
