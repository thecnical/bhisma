"""
Conversation Memory
===================
Maintains context across AI agent interactions.
"""

import json
import os
from collections import deque
from typing import List, Dict, Optional
from datetime import datetime

from bhisma.utils.constants import FRAMEWORK_NAME

MEMORY_FILE = os.path.expanduser("~/.bhisma/ai_memory.json")
MAX_MEMORY_TURNS = 20


class ConversationMemory:
    """Stores and retrieves conversation turns for AI context."""

    def __init__(self, max_turns: int = MAX_MEMORY_TURNS):
        self.max_turns = max_turns
        self.turns: deque = deque(maxlen=max_turns)
        self._load()

    def _load(self) -> None:
        """Load persisted memory from file."""
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.turns = deque(data.get("turns", []), maxlen=self.max_turns)
            except Exception:
                self.turns = deque(maxlen=self.max_turns)

    def _save(self) -> None:
        """Persist memory to file."""
        os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "framework": FRAMEWORK_NAME,
                "last_updated": datetime.utcnow().isoformat(),
                "turns": list(self.turns),
            }, f, indent=2)

    def add_turn(self, user_prompt: str, ai_response: str, metadata: Optional[Dict] = None) -> None:
        """Add a conversation turn."""
        self.turns.append({
            "timestamp": datetime.utcnow().isoformat(),
            "user": user_prompt[:500],  # Truncate for storage
            "ai": ai_response[:1000],
            "metadata": metadata or {},
        })
        self._save()

    def get_formatted_history(self, turns: Optional[int] = None) -> str:
        """Get formatted conversation history string."""
        n = turns or len(self.turns)
        recent = list(self.turns)[-n:]
        lines = []
        for turn in recent:
            lines.append(f"User: {turn['user']}")
            lines.append(f"AI: {turn['ai'][:300]}")  # Truncate in context
            lines.append("")
        return "\n".join(lines)

    def get_raw_history(self) -> List[Dict]:
        """Get raw turn data."""
        return list(self.turns)

    def clear(self) -> None:
        """Clear all memory."""
        self.turns.clear()
        self._save()

    def get_attack_context(self) -> str:
        """Extract attack-relevant context from memory."""
        relevant = []
        for turn in self.turns:
            meta = turn.get("metadata", {})
            if meta.get("type") in ["attack", "tool", "decision"]:
                relevant.append(turn)
        if not relevant:
            return ""
        lines = []
        for turn in relevant[-5:]:
            lines.append(f"- {meta.get('type', 'action')}: {turn['ai'][:200]}")
        return "Recent actions:\n" + "\n".join(lines)
