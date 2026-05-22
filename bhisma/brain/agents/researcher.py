"""
Vulnerability Research Agent
============================
Looks up CVEs, known vulnerabilities, and exploit suggestions.
"""

from typing import Dict, Any, Optional, List

from bhisma.brain.orchestrator import LLMOrchestrator


class VulnResearcher:
    """AI agent for vulnerability research and exploit suggestion."""

    def __init__(self, orchestrator: Optional[LLMOrchestrator] = None):
        self.orchestrator = orchestrator or LLMOrchestrator()

    def research_target(
        self,
        target: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Research a target for known vulnerabilities.

        Returns:
            Dict with: cves, exploits, recommendations, risk_score
        """
        prompt = self._build_research_prompt(target)
        response = self.orchestrator.query(
            prompt,
            system=(
                "You are a vulnerability researcher. Given a WiFi target profile, "
                "identify known CVEs, applicable exploits, and risk scores. "
                "Return JSON: {\"cves\": [...], \"exploits\": [...], "
                "\"recommendations\": [...], \"risk_score\": 0-10}"
            ),
            max_tokens=1500,
            temperature=0.3,
        )
        return self._parse_research(response.text)

    def _build_research_prompt(self, target: Dict[str, Any]) -> str:
        return (
            f"Research known vulnerabilities for this target:\n"
            f"SSID: {target.get('ssid', 'N/A')}\n"
            f"Encryption: {target.get('encryption', 'N/A')}\n"
            f"WPS: {target.get('wps', False)}\n"
            f"WPA3: {target.get('wpa3', False)}\n"
            f"Vendor (from MAC): {target.get('vendor', 'Unknown')}\n"
            f"WiFi 6: {target.get('wifi6', False)}\n"
            f"\nReturn known CVEs, exploit techniques, and risk score (0-10)."
        )

    def _parse_research(self, text: str) -> Dict[str, Any]:
        import json
        import re
        try:
            match = re.search(r'```(?:json)?\s*(\{.*?)```', text, re.DOTALL)
            if match:
                text = match.group(1)
            data = json.loads(text)
            if "cves" in data:
                return data
        except Exception:
            pass
        return {
            "cves": [],
            "exploits": [],
            "recommendations": ["No specific CVEs identified. Proceed with standard attack chain."],
            "risk_score": 5.0,
        }

    def suggest_wordlist_rules(self, target: Dict[str, Any]) -> List[str]:
        """AI-suggest hashcat rules or masks for a target."""
        prompt = (
            f"Given target SSID '{target.get('ssid', '')}' and vendor '{target.get('vendor', '')}', "
            f"suggest 3-5 hashcat rules or mask patterns that might be effective. "
            f"Return as a simple list, one per line."
        )
        try:
            response = self.orchestrator.query(prompt, max_tokens=200, temperature=0.5)
            rules = [r.strip("- *") for r in response.text.strip().splitlines() if r.strip()]
            return rules[:10]
        except Exception:
            return ["?d?d?d?d?d?d?d?d", "?l?l?l?l?d?d?d?d"]

    def analyze_firmware(self, vendor: str, model_hint: Optional[str] = None) -> Dict[str, Any]:
        """Research known firmware vulnerabilities for a vendor/model."""
        prompt = f"Research known firmware vulnerabilities for {vendor} {model_hint or 'routers'}. Return JSON."
        try:
            response = self.orchestrator.query(prompt, max_tokens=1000, temperature=0.3)
            return self._parse_research(response.text)
        except Exception:
            return {"cves": [], "exploits": [], "recommendations": [], "risk_score": 5.0}
