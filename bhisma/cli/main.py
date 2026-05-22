"""
Bhisma CLI Entry Point
======================
Click-based command-line interface.
"""

import sys
import click
from bhisma.utils.constants import FRAMEWORK_NAME, FRAMEWORK_VERSION, FRAMEWORK_DESCRIPTION
from bhisma.cli.commands import (
    cmd_auto, cmd_start, cmd_recon, cmd_scan, cmd_deauth,
    cmd_evil_twin, cmd_harvest, cmd_crack, cmd_mitm,
    cmd_wps, cmd_wep, cmd_setup, cmd_keys, cmd_tools,
    cmd_daemon, cmd_dashboard, cmd_ml, cmd_report,
)


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show version and exit")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.pass_context
def cli(ctx, version, verbose):
    """
    \b
    ██████╗ ██╗  ██╗██╗███████╗███╗   ███╗ █████╗
    ██╔══██╗██║  ██║██║██╔════╝████╗ ████║██╔══██╗
    ██████╔╝███████║██║███████╗██╔████╔██║███████║
    ██╔══██╗██╔══██║██║╚════██║██║╚██╔╝██║██╔══██║
    ██████╔╝██║  ██║██║███████║██║ ╚═╝ ██║██║  ██║
    ╚═════╝ ╚═╝  ╚═╝╚═╝╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝
    \b
    AI-Powered Autonomous Multi-Protocol Offensive WiFi Framework
    """
    if version:
        click.echo(f"{FRAMEWORK_NAME} v{FRAMEWORK_VERSION}")
        sys.exit(0)
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# Register all commands
cli.add_command(cmd_auto, name="auto")
cli.add_command(cmd_start, name="start")
cli.add_command(cmd_recon, name="recon")
cli.add_command(cmd_scan, name="scan")
cli.add_command(cmd_deauth, name="deauth")
cli.add_command(cmd_evil_twin, name="evil-twin")
cli.add_command(cmd_harvest, name="harvest")
cli.add_command(cmd_crack, name="crack")
cli.add_command(cmd_mitm, name="mitm")
cli.add_command(cmd_wps, name="wps")
cli.add_command(cmd_wep, name="wep")
cli.add_command(cmd_setup, name="setup")
cli.add_command(cmd_keys, name="keys")
cli.add_command(cmd_tools, name="tools")
cli.add_command(cmd_daemon, name="daemon")
cli.add_command(cmd_dashboard, name="dashboard")
cli.add_command(cmd_ml, name="ml")
cli.add_command(cmd_report, name="report")


def main():
    """Entry point for console_scripts."""
    cli()


if __name__ == "__main__":
    main()
