"""
Dependency Manager
==================
Robust Python dependency checking and installation for Linux.
Handles virtual environments, permission issues, and system packages.
"""

import os
import sys
import subprocess
import shutil
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class DependencyManager:
    """Manages Python dependencies with Linux-specific handling."""

    def __init__(self):
        self.venv_path = Path(os.path.expanduser("~/.bhisma/venv"))
        self.system_python = sys.executable
        self.venv_python = str(self.venv_path / "bin" / "python") if self.venv_path.exists() else None

    def check_environment(self) -> Dict[str, bool]:
        """Check current Python environment status."""
        return {
            "has_venv": self.venv_path.exists(),
            "in_venv": hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix),
            "pip_available": shutil.which("pip") is not None,
            "pip3_available": shutil.which("pip3") is not None,
            "sudo_available": shutil.which("sudo") is not None,
        }

    def ensure_venv(self) -> bool:
        """Create virtual environment if not exists."""
        if self.venv_path.exists():
            return True

        console.print("[bold cyan][*] Creating virtual environment at ~/.bhisma/venv[/bold cyan]")
        try:
            subprocess.run(
                [self.system_python, "-m", "venv", str(self.venv_path)],
                check=True,
                capture_output=True,
            )
            self.venv_python = str(self.venv_path / "bin" / "python")
            console.print("[bold green][+] Virtual environment created[/bold green]")
            return True
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red][!] Failed to create venv: {e}[/bold red]")
            return False

    def install_package(self, package: str, upgrade: bool = False) -> Tuple[bool, str]:
        """Install a Python package with proper error handling."""
        python = self.venv_python or self.system_python
        pip = str(Path(python).parent / "pip")

        cmd = [pip, "install", package]
        if upgrade:
            cmd.append("--upgrade")

        # Try without sudo first
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode == 0:
                return True, result.stdout
        except subprocess.TimeoutExpired:
            return False, "Installation timed out"
        except Exception as e:
            pass

        # Try with --user if permission denied
        if "Permission denied" in str(result.stderr) or "Access denied" in str(result.stderr):
            try:
                result = subprocess.run(
                    cmd + ["--user"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                if result.returncode == 0:
                    return True, result.stdout
            except Exception:
                pass

        # Try with sudo as last resort
        if shutil.which("sudo"):
            try:
                result = subprocess.run(
                    ["sudo"] + cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                if result.returncode == 0:
                    return True, result.stdout
            except Exception:
                pass

        return False, result.stderr if 'result' in locals() else "Unknown error"

    def install_requirements(self, requirements_file: str = "requirements.txt") -> bool:
        """Install all packages from requirements.txt."""
        if not os.path.exists(requirements_file):
            console.print(f"[yellow][!] {requirements_file} not found[/yellow]")
            return False

        console.print(f"[bold cyan][*] Installing dependencies from {requirements_file}[/bold cyan]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
        ) as progress:
            task = progress.add_task("Installing packages...", total=None)

            python = self.venv_python or self.system_python
            pip = str(Path(python).parent / "pip")

            # Try pip install -r
            try:
                result = subprocess.run(
                    [pip, "install", "-r", requirements_file],
                    capture_output=True,
                    text=True,
                    timeout=600,
                )
                if result.returncode == 0:
                    console.print("[bold green][+] All dependencies installed[/bold green]")
                    return True
            except subprocess.TimeoutExpired:
                console.print("[bold red][!] Installation timed out[/bold red]")
                return False
            except Exception as e:
                console.print(f"[yellow][!] pip install failed: {e}[/yellow]")

            # Fallback: install each package individually
            with open(requirements_file, "r") as f:
                packages = [line.strip() for line in f if line.strip() and not line.startswith("#")]

            for pkg in packages:
                # Extract package name (strip version specs)
                pkg_name = pkg.split(">")[0].split("<")[0].split("=")[0].split("[")[0].strip()
                progress.update(task, description=f"Installing {pkg_name}...")
                success, output = self.install_package(pkg)
                if not success:
                    console.print(f"[yellow][!] Failed to install {pkg_name}: {output[:100]}[/yellow]")

        console.print("[bold green][+] Dependency installation complete[/bold green]")
        return True

    def check_system_packages(self) -> Dict[str, bool]:
        """Check if required system packages are installed (Linux)."""
        required = {
            "python3": shutil.which("python3"),
            "pip3": shutil.which("pip3"),
            "git": shutil.which("git"),
            "gcc": shutil.which("gcc"),
            "make": shutil.which("make"),
            "libssl-dev": self._check_deb_package("libssl-dev") or self._check_rpm_package("openssl-devel"),
            "libffi-dev": self._check_deb_package("libffi-dev") or self._check_rpm_package("libffi-devel"),
        }
        return {k: bool(v) for k, v in required.items()}

    def _check_deb_package(self, package: str) -> bool:
        """Check if Debian/Ubuntu package is installed."""
        try:
            result = subprocess.run(
                ["dpkg", "-l", package],
                capture_output=True,
                text=True,
            )
            return "ii" in result.stdout
        except Exception:
            return False

    def _check_rpm_package(self, package: str) -> bool:
        """Check if RHEL/CentOS/Fedora package is installed."""
        try:
            result = subprocess.run(
                ["rpm", "-q", package],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except Exception:
            return False

    def install_system_packages(self) -> bool:
        """Install missing system packages."""
        missing = [pkg for pkg, installed in self.check_system_packages().items() if not installed]
        if not missing:
            console.print("[bold green][+] All system packages present[/bold green]")
            return True

        console.print(f"[bold yellow][!] Missing system packages: {', '.join(missing)}[/bold yellow]")
        console.print("[yellow]Run: sudo apt install python3 python3-pip python3-venv git gcc make libssl-dev libffi-dev[/yellow]")
        return False

    def fix_path_issues(self) -> None:
        """Add user bin to PATH if needed."""
        user_bin = os.path.expanduser("~/.local/bin")
        if user_bin not in os.environ.get("PATH", ""):
            console.print(f"[yellow][!] Adding {user_bin} to PATH[/yellow]")
            os.environ["PATH"] = f"{user_bin}:{os.environ.get('PATH', '')}"
