"""
Rule Engine
===========
YAML-based attack rule evaluation.
"""

import os
import yaml
from typing import Dict, Any, List, Optional

from bhisma.core.config import BhismaConfig


class RuleEngine:
    """Evaluates attack rules against target profiles."""

    DEFAULT_RULES = [
        {
            "name": "wps_auto",
            "condition": {"wps": True, "encryption": "WPA2"},
            "actions": ["wps_pixie", "wps_brute"],
            "throttle": "medium",
        },
        {
            "name": "handshake_auto",
            "condition": {"clients": ">0", "encryption": "WPA2"},
            "actions": ["silent_deauth", "harvest", "crack"],
            "throttle": "low",
        },
        {
            "name": "wep_fast",
            "condition": {"encryption": "WEP"},
            "actions": ["arp_replay", "crack"],
            "throttle": "high",
        },
        {
            "name": "evil_twin_fallback",
            "condition": {"handshake_failed": True, "clients": ">0"},
            "actions": ["evil_twin", "portal"],
            "throttle": "medium",
        },
    ]

    def __init__(self, rules_file: Optional[str] = None):
        self.rules: List[Dict] = []
        self._load_rules(rules_file)

    def _load_rules(self, path: Optional[str]) -> None:
        """Load rules from YAML file or use defaults."""
        if path and os.path.exists(path):
            with open(path, "r") as f:
                data = yaml.safe_load(f)
            self.rules = data.get("rules", self.DEFAULT_RULES)
        else:
            self.rules = self.DEFAULT_RULES

    def evaluate(self, target: Dict[str, Any]) -> List[str]:
        """
        Evaluate all rules against a target and return applicable actions.

        Args:
            target: Target profile dict

        Returns:
            List of action strings
        """
        actions = []
        for rule in self.rules:
            if self._check_condition(rule.get("condition", {}), target):
                actions.extend(rule.get("actions", []))
        return actions

    def _check_condition(self, condition: Dict, target: Dict) -> bool:
        """Check if target matches a rule condition."""
        for key, expected in condition.items():
            actual = target.get(key)
            if actual is None:
                return False
            if isinstance(expected, str) and expected.startswith(">"):
                try:
                    threshold = float(expected[1:])
                    if not (isinstance(actual, (int, float)) and actual > threshold):
                        return False
                except ValueError:
                    return False
            elif actual != expected:
                return False
        return True

    def add_rule(self, rule: Dict) -> None:
        """Add a custom rule at runtime."""
        self.rules.append(rule)

    def export_rules(self, path: str) -> None:
        """Export current rules to YAML file."""
        with open(path, "w") as f:
            yaml.dump({"rules": self.rules}, f, default_flow_style=False)
