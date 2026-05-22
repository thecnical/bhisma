"""
Real-Time Decision Agent
========================
Makes dynamic attack decisions based on current state and tool feedback.
"""

from typing import Dict, Any, Optional, List

from bhisma.brain.orchestrator import LLMOrchestrator


class RealTimeDecider:
    """AI agent for real-time attack decision making."""

    def __init__(self, orchestrator: Optional[LLMOrchestrator] = None):
        self.orchestrator = orchestrator or LLMOrchestrator()

    def decide_next_action(
        self,
        current_state: Dict[str, Any],
        last_result: Optional[Dict[str, Any]] = None,
        available_actions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Decide the next action in the attack chain.

        Args:
            current_state: Current attack state (phase, target info, elapsed time)
            last_result: Result of the previous action
            available_actions: List of possible next actions

        Returns:
            Dict with: action, reason, parameters, abort_if_fails, timeout
        """
        prompt = self._build_decision_prompt(current_state, last_result, available_actions)
        response = self.orchestrator.query(
            prompt,
            system=(
                "You are an autonomous attack decision engine. Given current state and last result, "
                "choose the next action from the available list. Return JSON: "
                "{\"action\": \"...\", \"reason\": \"...\", \"parameters\": {}, "
                "\"abort_if_fails\": false, \"timeout_sec\": 300}"
            ),
            max_tokens=1024,
            temperature=0.2,
        )
        return self._parse_decision(response.text)

    def _build_decision_prompt(
        self,
        state: Dict[str, Any],
        last_result: Optional[Dict[str, Any]],
        actions: Optional[List[str]],
    ) -> str:
        lines = [
            "Current attack state:",
            f"  Phase: {state.get('phase', 'unknown')}",
            f"  Target: {state.get('target_ssid', 'N/A')} ({state.get('target_bssid', 'N/A')})",
            f"  Elapsed: {state.get('elapsed_sec', 0)}s",
            f"  Attempts: {state.get('attempt_count', 0)}",
            f"  Successes: {state.get('success_count', 0)}",
        ]
        if last_result:
            lines.append("")
            lines.append("Last action result:")
            lines.append(f"  Action: {last_result.get('action', 'N/A')}")
            lines.append(f"  Status: {last_result.get('status', 'N/A')}")
            lines.append(f"  Findings: {last_result.get('findings', [])}")
        if actions:
            lines.append("")
            lines.append("Available next actions:")
            for a in actions:
                lines.append(f"  - {a}")
        lines.append("")
        lines.append("Decide the next action and return JSON.")
        return "\n".join(lines)

    def _parse_decision(self, text: str) -> Dict[str, Any]:
        import json
        import re
        try:
            match = re.search(r'```(?:json)?\s*(\{.*?)```', text, re.DOTALL)
            if match:
                text = match.group(1)
            data = json.loads(text)
            if "action" in data:
                return data
        except Exception:
            pass
        return {
            "action": "recon",
            "reason": "Fallback: gather more intelligence before proceeding.",
            "parameters": {},
            "abort_if_fails": False,
            "timeout_sec": 300,
        }

    def should_abort(self, state: Dict[str, Any], consecutive_failures: int) -> bool:
        """Determine if the attack chain should be aborted."""
        if consecutive_failures >= 3:
            return True
        if state.get("elapsed_sec", 0) > state.get("max_time_sec", 3600):
            return True
        return False

    def estimate_success_probability(
        self,
        target: Dict[str, Any],
        action: str,
    ) -> float:
        """Ask AI to estimate success probability for a given action."""
        prompt = (
            f"Given target {target.get('ssid', 'N/A')} with encryption "
            f"{target.get('encryption', 'N/A')}, clients={target.get('clients', 0)}, "
            f"signal={target.get('signal', 0)} dBm, "
            f"estimate success probability (0.0-1.0) for action: {action}. "
            f"Return ONLY a number."
        )
        try:
            response = self.orchestrator.query(prompt, max_tokens=10, temperature=0.1)
            prob = float(response.text.strip().replace("%", "").split()[0])
            return max(0.0, min(1.0, prob))
        except Exception:
            return 0.5
