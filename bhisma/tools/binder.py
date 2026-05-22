"""
Tool Binder
===========
Wraps external tool execution with output capture, AI analysis,
and real-time dashboard streaming.
"""

import os
import subprocess
import threading
import queue
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass

from rich.console import Console

from bhisma.tools.registry import get_tool
from bhisma.brain.agents.analyzer import ToolOutputAnalyzer
from bhisma.dashboard.websocket import DashboardWebsocket

console = Console()


@dataclass
class ToolResult:
    """Result of an external tool execution."""
    tool_name: str
    command: str
    return_code: int
    stdout: str
    stderr: str
    ai_analysis: Optional[Dict[str, Any]] = None
    duration_sec: float = 0.0


class ToolBinder:
    """Executes external tools with AI-enhanced output analysis."""

    def __init__(self, enable_ai: bool = True, stream_dashboard: bool = True):
        self.enable_ai = enable_ai
        self.stream_dashboard = stream_dashboard
        self.analyzer = ToolOutputAnalyzer() if enable_ai else None
        self.output_queue: queue.Queue = queue.Queue()

    def execute(
        self,
        tool_name: str,
        args: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        realtime_callback: Optional[Callable[[str], None]] = None,
        target_info: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        """
        Execute an external tool with full wrapping.

        Args:
            tool_name: Registered tool name
            args: Command-line arguments
            cwd: Working directory
            env: Environment variables
            timeout: Execution timeout
            realtime_callback: Callback for real-time output lines
            target_info: Target metadata for AI analysis

        Returns:
            ToolResult with stdout, stderr, return code, and AI analysis
        """
        meta = get_tool(tool_name)
        if not meta:
            raise ValueError(f"Unknown tool: {tool_name}")

        command = [meta.command] + args
        cmd_str = " ".join(command)
        console.print(f"[dim][EXEC] {cmd_str}[/dim]")

        start_time = __import__('time').time()
        stdout_lines: List[str] = []
        stderr_lines: List[str] = []

        try:
            proc = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=cwd,
                env={**os.environ, **(env or {})},
                bufsize=1,
                universal_newlines=True,
            )

            # Read stdout in real-time
            def read_stdout():
                if proc.stdout:
                    for line in iter(proc.stdout.readline, ""):
                        line = line.rstrip("\n")
                        stdout_lines.append(line)
                        if realtime_callback:
                            realtime_callback(line)
                        if self.stream_dashboard:
                            self._stream_to_dashboard(tool_name, "stdout", line)

            stdout_thread = threading.Thread(target=read_stdout, daemon=True)
            stdout_thread.start()

            # Read stderr
            if proc.stderr:
                for line in iter(proc.stderr.readline, ""):
                    stderr_lines.append(line.rstrip("\n"))
                    if self.stream_dashboard:
                        self._stream_to_dashboard(tool_name, "stderr", line.rstrip("\n"))

            proc.wait(timeout=timeout)
            stdout_thread.join(timeout=5)

            return_code = proc.returncode or 0
        except subprocess.TimeoutExpired:
            proc.kill()
            return_code = -1
            stderr_lines.append("[TIMEOUT]")
        except Exception as e:
            return_code = -1
            stderr_lines.append(str(e))

        duration = __import__('time').time() - start_time
        stdout = "\n".join(stdout_lines)
        stderr = "\n".join(stderr_lines)

        # AI analysis
        ai_analysis = None
        if self.enable_ai and self.analyzer:
            try:
                ai_analysis = self.analyzer.analyze(
                    tool_name=tool_name,
                    stdout=stdout,
                    stderr=stderr,
                    return_code=return_code,
                    target=target_info,
                )
                console.print(f"[dim][AI] Analysis: {ai_analysis.get('status', '?')} | "
                              f"Next: {ai_analysis.get('next_recommendation', '?')}[/dim]")
            except Exception as e:
                console.print(f"[dim][AI] Analysis failed: {e}[/dim]")

        result = ToolResult(
            tool_name=tool_name,
            command=cmd_str,
            return_code=return_code,
            stdout=stdout,
            stderr=stderr,
            ai_analysis=ai_analysis,
            duration_sec=duration,
        )

        self._stream_result_to_dashboard(result)
        return result

    def execute_shell(
        self,
        command: str,
        shell: bool = True,
        **kwargs
    ) -> ToolResult:
        """Execute a raw shell command."""
        console.print(f"[dim][SHELL] {command}[/dim]")
        start_time = __import__('time').time()
        try:
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=kwargs.get("timeout"),
                cwd=kwargs.get("cwd"),
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                tool_name="shell",
                command=command,
                return_code=-1,
                stdout="",
                stderr="TIMEOUT",
                duration_sec=0,
            )
        duration = __import__('time').time() - start_time
        return ToolResult(
            tool_name="shell",
            command=command,
            return_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            duration_sec=duration,
        )

    def _stream_to_dashboard(self, tool: str, stream: str, line: str) -> None:
        """Stream a single output line to dashboard."""
        try:
            DashboardWebsocket.broadcast({
                "type": "tool_output",
                "tool": tool,
                "stream": stream,
                "line": line,
            })
        except Exception:
            # Dashboard may not be running, ignore
            pass

    def _stream_result_to_dashboard(self, result: ToolResult) -> None:
        """Stream final result to dashboard."""
        try:
            DashboardWebsocket.broadcast({
                "type": "tool_result",
                "tool": result.tool_name,
                "return_code": result.return_code,
                "duration": result.duration_sec,
                "ai_status": result.ai_analysis.get("status") if result.ai_analysis else None,
            })
        except Exception:
            pass
