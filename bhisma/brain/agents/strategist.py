"""
Attack Strategist Agent
========================
Generates optimal attack sequences based on target profiles.
"""

from typing import Dict, List, Any, Optional

from bhisma.brain.orchestrator import LLMOrchestrator, AIResponse


class AttackStrategist:
    """AI agent that plans attack chains for given targets."""

    def __init__(self, orchestrator: Optional[LLMOrchestrator] = None):
        self.orchestrator = orchestrator or LLMOrchestrator()

    def generate_strategy(
        self,
        target: Dict[str, Any],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate an attack strategy for a target.

        Args:
            target: Target profile dict (bssid, ssid, encryption, channel, signal, etc.)
            constraints: Optional constraints (time_limit, stealth_level, etc.)

        Returns:
            Dict with attack chain, estimated success probability, timing, etc.
        """
        prompt = self._build_strategy_prompt(target, constraints)
        response = self.orchestrator.query(
            prompt,
            system="You are an elite red team strategist. Given a target profile, produce a structured attack plan. Output must be valid JSON with keys: phases (list), estimated_success (0-1), estimated_time_seconds, priority, notes.",
            max_tokens=2048,
            temperature=0.3,
        )
        return self._parse_strategy_response(response.text, target)

    def _build_strategy_prompt(
        self,
        target: Dict[str, Any],
        constraints: Optional[Dict[str, Any]],
    ) -> str:
        lines = [
            "Generate a precise attack strategy for the following WiFi target:",
            "",
            f"BSSID: {target.get('bssid', 'N/A')}",
            f"SSID: {target.get('ssid', 'N/A')}",
            f"Encryption: {target.get('encryption', 'N/A')}",
            f"Channel: {target.get('channel', 'N/A')}",
            f"Signal: {target.get('signal', 'N/A')} dBm",
            f"Clients: {target.get('clients', 0)}",
            f"WPS Enabled: {target.get('wps', False)}",
            f"WPA3/SAE: {target.get('wpa3', False)}",
            f"WiFi 6 (802.11ax): {target.get('wifi6', False)}",
            f"6GHz Band: {target.get('band_6ghz', False)}",
            f"Mesh Network: {target.get('mesh', False)}",
        ]
        if constraints:
            lines.append("")
            lines.append("Constraints:")
            for k, v in constraints.items():
                lines.append(f"  {k}: {v}")
        lines.append("")
        lines.append(
            "Return ONLY valid JSON with this exact structure:\n"
            '{\n'
            '  "phases": [\n'
            '    {"phase": "recon", "tools": ["airodump-ng"], "duration_sec": 30, "success_prob": 0.99},\n'
            '    ...\n'
            '  ],\n'
            '  "estimated_success": 0.75,\n'
            '  "estimated_time_seconds": 600,\n'
            '  "priority": "high",\n'
            '  "notes": "string"\n'
            '}'
        )
        return "\n".join(lines)

    def _parse_strategy_response(self, text: str, target: Dict) -> Dict[str, Any]:
        """Parse AI JSON response, fallback to default if invalid."""
        import json
        import re
        try:
            # Extract JSON from markdown code block if present
            match = re.search(r'```(?:json)?\s*(\{.*?)```', text, re.DOTALL)
            if match:
                text = match.group(1)
            data = json.loads(text)
            if "phases" in data:
                return data
        except Exception:
            pass
        # Fallback default strategy based on target profile
        return self._default_strategy(target)

    def _default_strategy(self, target: Dict) -> Dict[str, Any]:
        """Fallback heuristic strategy."""
        enc = target.get("encryption", "").lower()
        phases = []
        if "wep" in enc:
            phases.append({"phase": "wep_crack", "tools": ["aireplay-ng", "aircrack-ng"], "duration_sec": 300, "success_prob": 0.95})
        elif "wpa3" in enc or "sae" in enc:
            phases.append({"phase": "wpa3_dragonblood", "tools": ["hcxdumptool"], "duration_sec": 600, "success_prob": 0.3})
        elif "wpa2" in enc:
            if target.get("wps", False):
                phases.append({"phase": "wps_pixie", "tools": ["reaver"], "duration_sec": 120, "success_prob": 0.6})
            phases.append({"phase": "handshake_capture", "tools": ["hcxdumptool", "aircrack-ng"], "duration_sec": 300, "success_prob": 0.8})
            phases.append({"phase": "hash_crack", "tools": ["hashcat"], "duration_sec": 3600, "success_prob": 0.5})
        else:
            phases.append({"phase": "recon_deep", "tools": ["airodump-ng"], "duration_sec": 60, "success_prob": 0.95})

        return {
            "phases": phases,
            "estimated_success": 0.7,
            "estimated_time_seconds": sum(p.get("duration_sec", 60) for p in phases),
            "priority": "high" if target.get("clients", 0) > 0 else "medium",
            "notes": "AI-generated strategy based on target profile",
        }
