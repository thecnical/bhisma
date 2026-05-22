"""
Code Generation Agent
=====================
Generates custom scripts, Scapy packets, and automation code on-the-fly.
"""

from typing import Dict, Any, Optional

from bhisma.brain.orchestrator import LLMOrchestrator


class CodeAgent:
    """AI agent for generating code and scripts dynamically."""

    def __init__(self, orchestrator: Optional[LLMOrchestrator] = None):
        self.orchestrator = orchestrator or LLMOrchestrator()

    def generate_scapy_script(
        self,
        description: str,
        target_bssid: Optional[str] = None,
        interface: Optional[str] = None,
    ) -> str:
        """Generate a Scapy packet crafting script."""
        prompt = (
            f"Write a Python script using Scapy to {description}.\n"
        )
        if target_bssid:
            prompt += f"Target BSSID: {target_bssid}\n"
        if interface:
            prompt += f"Interface: {interface}\n"
        prompt += (
            "\nThe script should be complete, runnable, and handle errors gracefully. "
            "Include comments. Return ONLY the Python code in a markdown code block."
        )
        response = self.orchestrator.query(
            prompt,
            system="You are an expert Python and Scapy developer. Generate production-quality scripts.",
            max_tokens=2048,
            temperature=0.3,
        )
        return self._extract_code(response.text)

    def generate_exploit(
        self,
        vulnerability: str,
        target_info: Dict[str, Any],
    ) -> str:
        """Generate a proof-of-concept exploit script."""
        prompt = (
            f"Generate a proof-of-concept exploit script for: {vulnerability}\n"
            f"Target info: {target_info}\n"
            f"\nThe script should demonstrate the vulnerability without causing damage. "
            f"Include safety checks. Return ONLY the code in a markdown block."
        )
        response = self.orchestrator.query(
            prompt,
            system="You are a security researcher writing PoC exploits for authorized testing.",
            max_tokens=2048,
            temperature=0.3,
        )
        return self._extract_code(response.text)

    def generate_bash_command(
        self,
        task: str,
        tools_available: Optional[list] = None,
    ) -> str:
        """Generate a bash one-liner or script for a task."""
        prompt = f"Write a bash command or script to: {task}\n"
        if tools_available:
            prompt += f"Available tools: {', '.join(tools_available)}\n"
        prompt += "\nReturn ONLY the bash code in a markdown block."
        response = self.orchestrator.query(
            prompt,
            system="You are a Linux command-line expert. Write efficient, safe bash commands.",
            max_tokens=1024,
            temperature=0.2,
        )
        return self._extract_code(response.text)

    def generate_hashcat_command(
        self,
        hash_file: str,
        hash_mode: int,
        wordlist: Optional[str] = None,
        rules: Optional[list] = None,
    ) -> str:
        """Generate an optimized hashcat command."""
        prompt = (
            f"Generate the optimal hashcat command for:\n"
            f"Hash file: {hash_file}\n"
            f"Hash mode: {hash_mode}\n"
        )
        if wordlist:
            prompt += f"Wordlist: {wordlist}\n"
        if rules:
            prompt += f"Rules: {', '.join(rules)}\n"
        prompt += "\nReturn ONLY the command string, no markdown."
        response = self.orchestrator.query(
            prompt,
            max_tokens=200,
            temperature=0.1,
        )
        return response.text.strip()

    def _extract_code(self, text: str) -> str:
        """Extract code from markdown code block."""
        import re
        match = re.search(r'```(?:python|bash)?\s*\n(.*?)```', text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return text.strip()
