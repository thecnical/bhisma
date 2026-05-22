"""
Report Generation Agent
=======================
Generates automated pentest reports from attack data.
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime

from bhisma.brain.orchestrator import LLMOrchestrator
from bhisma.utils.constants import DEFAULT_REPORTS_DIR


class ReportAgent:
    """AI agent for generating pentest reports."""

    def __init__(self, orchestrator: Optional[LLMOrchestrator] = None):
        self.orchestrator = orchestrator or LLMOrchestrator()

    def generate(
        self,
        session_id: Optional[str] = None,
        output_path: Optional[str] = None,
        fmt: str = "markdown",
        attack_data: Optional[List[Dict]] = None,
    ) -> str:
        """
        Generate a pentest report.

        Args:
            session_id: Session identifier for loading data
            output_path: Where to save the report
            fmt: Output format (markdown, json, html)
            attack_data: Raw attack timeline data

        Returns:
            Path to generated report file
        """
        data = attack_data or self._load_session_data(session_id)
        prompt = self._build_report_prompt(data, fmt)
        response = self.orchestrator.query(
            prompt,
            system=(
                "You are a professional penetration testing report writer. "
                "Generate a detailed, well-structured technical report. "
                "Include executive summary, methodology, findings with evidence, "
                "risk ratings, and remediation advice. Be thorough and technical."
            ),
            max_tokens=4096,
            temperature=0.4,
        )

        report_text = response.text
        out_path = output_path or os.path.join(
            DEFAULT_REPORTS_DIR, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{fmt}"
        )
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        if fmt == "html":
            report_text = self._wrap_html(report_text)

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(report_text)

        return out_path

    def _load_session_data(self, session_id: Optional[str]) -> List[Dict]:
        """Load attack data from session logs."""
        import json
        log_file = os.path.expanduser(f"~/.bhisma/logs/{session_id or 'latest'}.json")
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                return json.load(f)
        return []

    def _build_report_prompt(self, data: List[Dict], fmt: str) -> str:
        timeline = "\n".join(
            f"- [{d.get('timestamp', '?')}] {d.get('phase', '?')}: {d.get('result', '?')}"
            for d in data[:50]
        )
        return (
            f"Generate a {fmt.upper()} penetration test report from the following attack timeline:\n\n"
            f"{timeline}\n\n"
            f"Include: Executive Summary, Target Information, Methodology, "
            f"Findings (with evidence), Risk Ratings (Critical/High/Medium/Low), "
            f"Remediation Recommendations, and Appendix."
        )

    def _wrap_html(self, content: str) -> str:
        return (
            "<!DOCTYPE html>\n"
            "<html><head><meta charset='utf-8'>"
            "<title>Bhisma Pentest Report</title>"
            "<style>body{font-family:Arial,sans-serif;max-width:900px;margin:40px auto;line-height:1.6}"
            "h1{color:#333}h2{color:#555;border-bottom:2px solid #ddd;padding-bottom:5px}"
            "pre{background:#f4f4f4;padding:10px;border-radius:4px;overflow-x:auto}"
            "table{border-collapse:collapse;width:100%}th,td{border:1px solid #ddd;padding:8px}"
            "th{background:#f2f2f2}</style></head><body>"
            f"{content}"
            "</body></html>"
        )
