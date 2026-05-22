"""
Bhisma CLI Commands
===================
All subcommands for the Bhisma CLI.
"""

import os
import sys
import time
import threading
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt

from bhisma.utils.constants import FRAMEWORK_NAME, FRAMEWORK_VERSION
from bhisma.core.config import BhismaConfig
from bhisma.utils.platform import PLATFORM
from bhisma.utils.deps import DependencyManager

console = Console()


def _print_banner():
    """Print the Bhisma ASCII banner."""
    banner = """
[bold red]    ██████╗ ██╗  ██╗██╗███████╗███╗   ███╗ █████╗[/bold red]
[bold red]    ██╔══██╗██║  ██║██║██╔════╝████╗ ████║██╔══██╗[/bold red]
[bold red]    ██████╔╝███████║██║███████╗██╔████╔██║███████║[/bold red]
[bold red]    ██╔══██╗██╔══██║██║╚════██║██║╚██╔╝██║██╔══██║[/bold red]
[bold red]    ██████╔╝██║  ██║██║███████║██║ ╚═╝ ██║██║  ██║[/bold red]
[bold red]    ╚═════╝ ╚═╝  ╚═╝╚═╝╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝[/bold red]
[bold cyan]    AI-Powered Autonomous Multi-Protocol Offensive WiFi Framework[/bold cyan]
[dim]    v{}[/dim]
""".format(FRAMEWORK_VERSION)
    console.print(banner)


@click.command()
@click.option("--iface", "-i", required=True, help="Wireless interface")
@click.option("--band", default="2.4,5", help="Bands to scan (2.4,5,6)")
@click.option("--timeout", "-t", default=20, help="Auto-select timeout seconds")
@click.option("--dashboard/--no-dashboard", default=True, help="Launch web dashboard")
@click.option("--offline", is_flag=True, help="Run without AI brain")
def cmd_auto(iface, band, timeout, dashboard, offline):
    """Fully autonomous attack mode: scan, select, attack — all automated."""
    _print_banner()
    console.print("[bold cyan][*] Checking dependencies...[/bold cyan]")
    dep_mgr = DependencyManager()
    env_status = dep_mgr.check_environment()
    if not env_status["pip_available"]:
        console.print("[bold red][!] pip not found. Install Python pip first.[/bold red]")
        return
    if PLATFORM.is_linux:
        sys_status = dep_mgr.check_system_packages()
        missing = [k for k, v in sys_status.items() if not v]
        if missing:
            console.print(f"[bold yellow][!] Missing system packages: {', '.join(missing)}[/bold yellow]")
            console.print("[yellow]Run: sudo apt install python3 python3-pip python3-venv git gcc make libssl-dev libffi-dev[/yellow]")
            console.print("[yellow]Or use: bhisma setup --install-system[/yellow]")
            return
    config = BhismaConfig.load()
    if offline:
        config.ai.enable_ai_brain = False

    console.print(f"[bold green][+] Starting autonomous mode on {iface}[/bold green]")
    console.print(f"[dim]    Bands: {band} | Auto-select timeout: {timeout}s[/dim]")

    # Adapter detection & monitor mode
    from bhisma.wifi.recon import ReconManager
    recon = ReconManager(iface, config)

    # Enter monitor mode
    success, mon_iface = PLATFORM.enter_monitor_mode(iface)
    if not success:
        console.print(f"[bold red][!] Failed to enter monitor mode: {mon_iface}[/bold red]")
        sys.exit(1)
    console.print(f"[bold green][+] Monitor mode active: {mon_iface}[/bold green]")

    # Scan
    console.print("[bold cyan][*] Scanning for targets...[/bold cyan]")
    targets = recon.scan_networks(bands=band.split(","))
    if not targets:
        console.print("[bold red][!] No targets found[/bold red]")
        sys.exit(1)

    # Display table
    table = Table(title="Discovered Networks")
    table.add_column("#", style="cyan")
    table.add_column("BSSID", style="magenta")
    table.add_column("SSID", style="green")
    table.add_column("Channel", justify="center")
    table.add_column("Signal", justify="right")
    table.add_column("Enc", justify="center")
    table.add_column("Clients", justify="center")
    table.add_column("Score", justify="right")

    for idx, t in enumerate(targets, 1):
        table.add_row(
            str(idx),
            t.get("bssid", "?"),
            t.get("ssid", "<hidden>")[:20],
            str(t.get("channel", "?")),
            f"{t.get('signal', 0)} dBm",
            t.get("encryption", "?"),
            str(t.get("clients", 0)),
            str(t.get("score", "N/A")),
        )
    console.print(table)

    # Prompt user
    console.print(f"\n[bold yellow]Select target [1-{len(targets)}] or press ENTER for auto-select ({timeout}s)[/bold yellow]")
    selected = None
    start_time = time.time()
    while time.time() - start_time < timeout:
        if not selected:
            try:
                import select
                if sys.stdin in select.select([sys.stdin], [], [], 0.5)[0]:
                    choice = input().strip()
                    if choice:
                        try:
                            idx = int(choice)
                            if 1 <= idx <= len(targets):
                                selected = targets[idx - 1]
                                break
                        except ValueError:
                            pass
            except Exception:
                time.sleep(0.5)
    if not selected:
        # Auto-select: highest signal + highest score
        targets_sorted = sorted(targets, key=lambda x: (x.get("score", 0), x.get("signal", -100)), reverse=True)
        selected = targets_sorted[0]
        console.print(f"[bold yellow][*] Auto-selected target: {selected.get('ssid', '<hidden>')} ({selected['bssid']})[/bold yellow]")
    else:
        console.print(f"[bold green][+] Target locked: {selected.get('ssid', '<hidden>')} ({selected['bssid']})[/bold green]")

    # Launch dashboard
    if dashboard:
        from bhisma.dashboard.server import start_dashboard
        dashboard_thread = threading.Thread(
            target=start_dashboard,
            args=(config.dashboard.host, config.dashboard.port),
            daemon=True,
        )
        dashboard_thread.start()
        time.sleep(1)
        console.print(f"[bold green][+] Dashboard: http://{config.dashboard.host}:{config.dashboard.port}[/bold green]")

    # Start autonomous attack chain
    console.print("[bold red][!] Initiating autonomous attack chain...[/bold red]")
    from bhisma.core.autonomous.orchestrator import AutonomousOrchestrator
    orchestrator = AutonomousOrchestrator(config, recon)
    orchestrator.run(selected, mon_iface)


@click.command()
def cmd_start():
    """Interactive mode — manual target selection and module control."""
    _print_banner()
    console.print("[bold yellow]Interactive mode — use subcommands for specific actions[/bold yellow]")
    console.print("  bhisma scan      — scan networks")
    console.print("  bhisma recon     — passive reconnaissance")
    console.print("  bhisma deauth    — deauthentication attacks")
    console.print("  bhisma evil-twin — rogue AP attacks")
    console.print("  bhisma harvest   — handshake capture")
    console.print("  bhisma mitm      — man-in-the-middle")
    console.print("  bhisma auto      — fully autonomous mode")


@click.command()
@click.option("--iface", "-i", required=True, help="Wireless interface")
def cmd_recon(iface):
    """Passive reconnaissance — discover hidden SSIDs and clients."""
    from bhisma.wifi.recon import ReconManager
    config = BhismaConfig.load()
    recon = ReconManager(iface, config)
    results = recon.passive_recon(duration=60)
    console.print(f"[bold green][+] Recon complete. Found {len(results.get('aps', []))} APs, {len(results.get('clients', []))} clients[/bold green]")


@click.command()
@click.option("--band", default="2.4,5", help="Bands to scan")
@click.option("--iface", "-i", required=True, help="Wireless interface")
@click.option("--duration", "-d", default=30, help="Scan duration in seconds")
def cmd_scan(iface, band, duration):
    """Active network scan with AI-enhanced target scoring."""
    from bhisma.wifi.recon import ReconManager
    config = BhismaConfig.load()
    recon = ReconManager(iface, config)
    targets = recon.scan_networks(bands=band.split(","), duration=duration)

    table = Table(title="Scan Results")
    table.add_column("BSSID", style="magenta")
    table.add_column("SSID", style="green")
    table.add_column("Ch", justify="center")
    table.add_column("Signal", justify="right")
    table.add_column("Enc")
    table.add_column("Clients", justify="center")
    for t in targets:
        table.add_row(
            t.get("bssid", "?"),
            t.get("ssid", "<hidden>")[:20],
            str(t.get("channel", "?")),
            f"{t.get('signal', 0)} dBm",
            t.get("encryption", "?"),
            str(t.get("clients", 0)),
        )
    console.print(table)


@click.command()
@click.option("--target", "-t", required=True, help="Target BSSID")
@click.option("--client", "-c", help="Specific client MAC")
@click.option("--iface", "-i", required=True, help="Interface")
@click.option("--silent", is_flag=True, help="Use silent pulse (predictive) deauth")
@click.option("--count", default=5, help="Deauth packet count")
def cmd_deauth(target, client, iface, silent, count):
    """Deauthentication attacks — flood, directed, or silent pulse."""
    from bhisma.wifi.deauth import DeauthManager
    config = BhismaConfig.load()
    mgr = DeauthManager(iface, config)
    if silent:
        mgr.silent_pulse_deauth(target, client)
    else:
        mgr.directed_deauth(target, client, count=count)
    console.print(f"[bold red][!] Deauth attack sent to {target}[/bold red]")


@click.command()
@click.option("--target", "-t", required=True, help="Target BSSID to clone")
@click.option("--portal", is_flag=True, help="Enable captive portal phishing")
@click.option("--karma", is_flag=True, help="Enable KARMA attack")
@click.option("--mana", is_flag=True, help="Enable MANA attack")
@click.option("--iface", "-i", required=True, help="Interface")
def cmd_evil_twin(target, portal, karma, mana, iface):
    """Rogue access point attacks — evil twin, KARMA, MANA."""
    from bhisma.wifi.evil_twin import EvilTwinManager
    config = BhismaConfig.load()
    mgr = EvilTwinManager(iface, config)
    mgr.start_rogue_ap(
        target_bssid=target,
        portal=portal,
        karma=karma,
        mana=mana,
    )
    console.print(f"[bold red][!] Evil Twin active for {target}[/bold red]")


@click.command()
@click.option("--target", "-t", required=True, help="Target BSSID")
@click.option("--pmkid", is_flag=True, help="Capture PMKID")
@click.option("--handshake", is_flag=True, help="Capture 4-way handshake")
@click.option("--iface", "-i", required=True, help="Interface")
@click.option("--output", "-o", help="Output file path")
def cmd_harvest(target, pmkid, handshake, iface, output):
    """Capture WPA handshakes and PMKID hashes."""
    from bhisma.wifi.harvester import HarvesterManager
    config = BhismaConfig.load()
    mgr = HarvesterManager(iface, config)
    if not pmkid and not handshake:
        pmkid = handshake = True
    result = mgr.capture(target, pmkid=pmkid, handshake=handshake, output=output)
    console.print(f"[bold green][+] Capture result: {result}[/bold green]")


@click.command()
@click.option("--file", "-f", required=True, help="Capture file (.pcapng)")
@click.option("--wordlist", "-w", help="Wordlist file")
@click.option("--hashcat", is_flag=True, help="Use hashcat GPU cracking")
def cmd_crack(file, wordlist, hashcat):
    """Crack captured handshakes or PMKID hashes."""
    from bhisma.wifi.harvester import CrackManager
    mgr = CrackManager()
    result = mgr.crack(file, wordlist=wordlist, use_hashcat=hashcat)
    console.print(f"[bold green][+] Crack result: {result}[/bold green]")


@click.command()
@click.option("--target", "-t", required=True, help="Target network BSSID")
@click.option("--arp", is_flag=True, help="ARP spoofing")
@click.option("--dns", is_flag=True, help="DNS hijacking")
@click.option("--sslstrip", is_flag=True, help="SSL stripping")
@click.option("--iface", "-i", required=True, help="Interface")
def cmd_mitm(target, arp, dns, sslstrip, iface):
    """Man-in-the-middle attacks on compromised network."""
    console.print(f"[bold red][!] MITM mode: {target}[/bold red]")
    from bhisma.mitm.arp import ARPSpoofer
    from bhisma.mitm.dns import DNSHijacker
    if arp:
        spoofer = ARPSpoofer(iface)
        spoofer.start(target)
    if dns:
        hijacker = DNSHijacker(iface)
        hijacker.start()


@click.command()
@click.option("--target", "-t", required=True, help="Target BSSID")
@click.option("--pixie", is_flag=True, help="Pixie Dust attack")
@click.option("--brute", is_flag=True, help="PIN brute-force")
@click.option("--iface", "-i", required=True, help="Interface")
@click.option("--timeout", default=600, help="Attack timeout")
def cmd_wps(target, pixie, brute, iface, timeout):
    """WPS PIN attacks — Pixie Dust, brute-force, NULL PIN."""
    from bhisma.wifi.wps import WPSAttacker
    mgr = WPSAttacker(iface)
    if pixie:
        mgr.pixie_dust(target, timeout=timeout)
    elif brute:
        mgr.brute_force(target, timeout=timeout)
    else:
        mgr.auto_attack(target, timeout=timeout)


@click.command()
@click.option("--target", "-t", required=True, help="Target BSSID")
@click.option("--iface", "-i", required=True, help="Interface")
def cmd_wep(target, iface):
    """WEP cracking — FMS, PTW, KoreK chopchop, ARP replay."""
    from bhisma.wifi.wep import WEPCracker
    mgr = WEPCracker(iface)
    mgr.attack(target)


@click.command()
@click.option("--install-system", is_flag=True, help="Install system dependencies")
@click.option("--install-python", is_flag=True, help="Install Python dependencies")
def cmd_setup(install_system, install_python):
    """First-time setup — configure API keys and dependencies."""
    _print_banner()
    console.print("[bold cyan][*] Bhisma Setup[/bold cyan]")

    dep_mgr = DependencyManager()

    if install_system:
        console.print("[bold cyan][*] Installing system dependencies...[/bold cyan]")
        if dep_mgr.install_system_packages():
            console.print("[bold green][+] System packages installed[/bold green]")
        else:
            console.print("[bold red][!] Failed to install system packages[/bold red]")
            return

    if install_python:
        console.print("[bold cyan][*] Installing Python dependencies...[/bold cyan]")
        if dep_mgr.install_requirements():
            console.print("[bold green][+] Python dependencies installed[/bold green]")
        else:
            console.print("[bold red][!] Failed to install Python dependencies[/bold red]")
            return

    # Check environment
    env_status = dep_mgr.check_environment()
    console.print(f"[dim]    Virtual env: {env_status['has_venv']} | In venv: {env_status['in_venv']}[/dim]")

    # API key setup
    from bhisma.tui.key_manager import KeyManager
    mgr = KeyManager()
    mgr.run_setup()
    console.print("[bold green][+] Setup complete. Run: bhisma auto --iface <interface>[/bold green]")


@click.command()
@click.option("--add", is_flag=True, help="Add/update API keys")
@click.option("--list", "list_keys", is_flag=True, help="List configured providers")
@click.option("--test", is_flag=True, help="Test all configured keys")
def cmd_keys(add, list_keys, test):
    """Manage AI LLM API keys — configure, test, update providers."""
    from bhisma.tui.key_manager import KeyManager
    mgr = KeyManager()
    if add:
        mgr.run_setup()
    elif list_keys:
        mgr.list_keys()
    elif test:
        mgr.test_all_keys()
    else:
        mgr.run_setup()


@click.group()
def cmd_tools():
    """Manage external tools — check, install, configure."""
    pass


@cmd_tools.command(name="check")
def tools_check():
    """Check status of all external tools."""
    from bhisma.tools.manager import ToolManager
    mgr = ToolManager()
    mgr.check_all()


@cmd_tools.command(name="install")
@click.argument("tool_name", required=False)
def tools_install(tool_name):
    """Install missing tools (or all if no name given)."""
    from bhisma.tools.manager import ToolManager
    mgr = ToolManager()
    if tool_name:
        mgr.install_tool(tool_name)
    else:
        mgr.install_all()


@click.group()
def cmd_daemon():
    """Control the autonomous background daemon."""
    pass


@cmd_daemon.command(name="start")
@click.option("--config-file", "-c", help="Path to rules YAML")
def daemon_start(config_file):
    """Start the autonomous background daemon."""
    from bhisma.core.autonomous.daemon import DaemonController
    DaemonController().start(config_file)


@cmd_daemon.command(name="stop")
def daemon_stop():
    """Stop the background daemon."""
    from bhisma.core.autonomous.daemon import DaemonController
    DaemonController().stop()


@cmd_daemon.command(name="status")
def daemon_status():
    """Show daemon status."""
    from bhisma.core.autonomous.daemon import DaemonController
    DaemonController().status()


@click.command()
@click.option("--port", "-p", default=8080, help="Dashboard port")
@click.option("--host", default="127.0.0.1", help="Dashboard host")
@click.option("--no-browser", is_flag=True, help="Don't auto-open browser")
def cmd_dashboard(port, host, no_browser):
    """Launch the web dashboard."""
    from bhisma.dashboard.server import start_dashboard
    console.print(f"[bold green][+] Starting dashboard at http://{host}:{port}[/bold green]")
    start_dashboard(host, port, open_browser=not no_browser)


@click.group()
def cmd_ml():
    """Machine Learning engine commands."""
    pass


@cmd_ml.command(name="train")
@click.option("--dataset", "-d", help="Path to training dataset directory")
def ml_train(dataset):
    """Train/update local ML models."""
    from bhisma.ml.auto_trainer import ModelTrainer
    trainer = ModelTrainer()
    trainer.train_all(dataset)


@cmd_ml.command(name="predict")
@click.option("--target", "-t", required=True, help="Target BSSID")
def ml_predict(target):
    """Run ML prediction on a target."""
    from bhisma.ml.success_predictor import SuccessPredictor
    predictor = SuccessPredictor()
    result = predictor.predict(target)
    console.print(f"[bold cyan]Prediction: {result}[/bold cyan]")


@click.command()
@click.option("--session", "-s", help="Session ID or capture directory")
@click.option("--output", "-o", default="report.md", help="Output report file")
@click.option("--format", "fmt", default="markdown", type=click.Choice(["markdown", "json", "html"]))
def cmd_report(session, output, fmt):
    """Generate AI-enhanced pentest report."""
    from bhisma.brain.agents.reporter import ReportAgent
    agent = ReportAgent()
    agent.generate(session_id=session, output_path=output, fmt=fmt)
    console.print(f"[bold green][+] Report saved: {output}[/bold green]")
