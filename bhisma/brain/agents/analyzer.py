"""
Tool Output Analyzer Agent
==========================
Parses external tool output and generates actionable insights.
"""

from typing import Dict, Any, Optional

from bhisma.brain.orchestrator import LLMOrchestrator


class ToolOutputAnalyzer:
    """AI agent that analyzes tool stdout/stderr."""

    def __init__(self, orchestrator: Optional[LLMOrchestrator] = None):
        self.orchestrator = orchestrator or LLMOrchestrator()

    def analyze(
        self,
        tool_name: str,
        stdout: str,
        stderr: str,
        return_code: int,
        target: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze tool output and return structured interpretation.

        Returns:
            Dict with keys: status, findings, errors, next_recommendation, confidence
        """
        prompt = self._build_analysis_prompt(tool_name, stdout, stderr, return_code, target)
        response = self.orchestrator.query(
            prompt,
            system=(
                "You are a tool output analyzer for a penetration testing framework. "
                "Parse the given tool output and return structured JSON with: "
                "status (success/partial/failure), findings (list), errors (list), "
                "next_recommendation (string), confidence (0-1)."
            ),
            max_tokens=1500,
            temperature=0.2,
        )
        return self._parse_analysis(response.text, tool_name, return_code)

    def _build_analysis_prompt(
        self,
        tool_name: str,
        stdout: str,
        stderr: str,
        return_code: int,
        target: Optional[Dict],
    ) -> str:
        target_info = ""
        if target:
            target_info = f"\nTarget: {target.get('ssid', 'N/A')} ({target.get('bssid', 'N/A')})\n"

        stdout_trunc = stdout[:3000] if stdout else "(empty)"
        stderr_trunc = stderr[:1500] if stderr else "(empty)"

        return (
            f"Analyze the output of {tool_name}:\n"
            f"Return Code: {return_code}\n"
            f"{target_info}\n"
            f"--- STDOUT ---\n{stdout_trunc}\n"
            f"--- STDERR ---\n{stderr_trunc}\n"
            f"\nReturn JSON: {{\"status\": \"...\", \"findings\": [...], "
            f"\"errors\": [...], \"next_recommendation\": \"...\", \"confidence\": 0.0}}"
        )

    def _parse_analysis(self, text: str, tool_name: str, return_code: int) -> Dict[str, Any]:
        import json
        import re
        try:
            match = re.search(r'```(?:json)?\s*(\{.*?)```', text, re.DOTALL)
            if match:
                text = match.group(1)
            data = json.loads(text)
            if "status" in data:
                return data
        except Exception:
            pass
        # Fallback heuristic
        status = "success" if return_code == 0 else "failure"
        if "warning" in text.lower() or "partial" in text.lower():
            status = "partial"
        return {
            "status": status,
            "findings": [f"{tool_name} executed with return code {return_code}"],
            "errors": [stderr for stderr in [""] if return_code != 0],
            "next_recommendation": "Review output manually or retry with modified parameters.",
            "confidence": 0.5,
        }
