"""
Attack State Machine
====================
Manages the lifecycle of an attack from reconnaissance to completion.
"""

from enum import Enum, auto
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field


class AttackPhase(Enum):
    IDLE = auto()
    RECON = auto()
    ANALYZE = auto()
    DEAUTH = auto()
    HARVEST = auto()
    CRACK = auto()
    EVIL_TWIN = auto()
    WPS = auto()
    WEP = auto()
    MITM = auto()
    PERSIST = auto()
    CLEANUP = auto()
    COMPLETE = auto()
    FAILED = auto()


class AttackEvent(Enum):
    START = auto()
    RECON_COMPLETE = auto()
    TARGET_LOCKED = auto()
    HANDSHAKE_CAPTURED = auto()
    PASSWORD_CRACKED = auto()
    WPS_SUCCESS = auto()
    WEP_CRACKED = auto()
    TIMEOUT = auto()
    FAILURE = auto()
    ABORT = auto()
    RETRY = auto()


@dataclass
class StateTransition:
    """Defines a valid state transition."""
    from_phase: AttackPhase
    event: AttackEvent
    to_phase: AttackPhase
    condition: Optional[Callable] = None


class AttackStateMachine:
    """Finite state machine for attack lifecycle management."""

    TRANSITIONS = [
        StateTransition(AttackPhase.IDLE, AttackEvent.START, AttackPhase.RECON),
        StateTransition(AttackPhase.RECON, AttackEvent.TARGET_LOCKED, AttackPhase.ANALYZE),
        StateTransition(AttackPhase.ANALYZE, AttackEvent.START, AttackPhase.DEAUTH),
        StateTransition(AttackPhase.DEAUTH, AttackEvent.HANDSHAKE_CAPTURED, AttackPhase.HARVEST),
        StateTransition(AttackPhase.DEAUTH, AttackEvent.FAILURE, AttackPhase.EVIL_TWIN),
        StateTransition(AttackPhase.HARVEST, AttackEvent.HANDSHAKE_CAPTURED, AttackPhase.CRACK),
        StateTransition(AttackPhase.HARVEST, AttackEvent.FAILURE, AttackPhase.EVIL_TWIN),
        StateTransition(AttackPhase.CRACK, AttackEvent.PASSWORD_CRACKED, AttackPhase.MITM),
        StateTransition(AttackPhase.CRACK, AttackEvent.FAILURE, AttackPhase.EVIL_TWIN),
        StateTransition(AttackPhase.EVIL_TWIN, AttackEvent.PASSWORD_CRACKED, AttackPhase.MITM),
        StateTransition(AttackPhase.EVIL_TWIN, AttackEvent.FAILURE, AttackPhase.WPS),
        StateTransition(AttackPhase.WPS, AttackEvent.WPS_SUCCESS, AttackPhase.MITM),
        StateTransition(AttackPhase.WPS, AttackEvent.FAILURE, AttackPhase.WEP),
        StateTransition(AttackPhase.WEP, AttackEvent.WEP_CRACKED, AttackPhase.MITM),
        StateTransition(AttackPhase.WEP, AttackEvent.FAILURE, AttackPhase.CLEANUP),
        StateTransition(AttackPhase.MITM, AttackEvent.TIMEOUT, AttackPhase.PERSIST),
        StateTransition(AttackPhase.PERSIST, AttackEvent.TIMEOUT, AttackPhase.CLEANUP),
        StateTransition(AttackPhase.CLEANUP, AttackEvent.START, AttackPhase.COMPLETE),
        # Retry paths
        StateTransition(AttackPhase.DEAUTH, AttackEvent.RETRY, AttackPhase.DEAUTH),
        StateTransition(AttackPhase.HARVEST, AttackEvent.RETRY, AttackPhase.DEAUTH),
        StateTransition(AttackPhase.CRACK, AttackEvent.RETRY, AttackPhase.CRACK),
        # Abort
        StateTransition(AttackPhase.RECON, AttackEvent.ABORT, AttackPhase.FAILED),
        StateTransition(AttackPhase.ANALYZE, AttackEvent.ABORT, AttackPhase.FAILED),
        StateTransition(AttackPhase.DEAUTH, AttackEvent.ABORT, AttackPhase.FAILED),
        StateTransition(AttackPhase.HARVEST, AttackEvent.ABORT, AttackPhase.FAILED),
        StateTransition(AttackPhase.CRACK, AttackEvent.ABORT, AttackPhase.FAILED),
    ]

    def __init__(self):
        self.current_phase = AttackPhase.IDLE
        self.phase_history: List[AttackPhase] = []
        self.transition_log: List[Dict[str, Any]] = []

    def get_valid_events(self) -> List[AttackEvent]:
        """Get list of valid events from current state."""
        return [
            t.event for t in self.TRANSITIONS
            if t.from_phase == self.current_phase
        ]

    def can_transition(self, event: AttackEvent) -> bool:
        """Check if an event can be processed in current state."""
        return any(
            t.from_phase == self.current_phase and t.event == event
            for t in self.TRANSITIONS
        )

    def transition(self, event: AttackEvent, context: Optional[Dict] = None) -> Optional[AttackPhase]:
        """
        Process an event and transition state if valid.

        Args:
            event: The event to process
            context: Optional context dict for condition checking

        Returns:
            New phase if transition occurred, None otherwise
        """
        for t in self.TRANSITIONS:
            if t.from_phase == self.current_phase and t.event == event:
                if t.condition and context:
                    if not t.condition(context):
                        continue
                self.phase_history.append(self.current_phase)
                self.current_phase = t.to_phase
                self.transition_log.append({
                    "from": t.from_phase.name,
                    "event": event.name,
                    "to": t.to_phase.name,
                    "context": context,
                })
                return t.to_phase
        return None

    def get_next_recommended_phases(self) -> List[str]:
        """Get human-readable list of next possible phases."""
        next_phases = set()
        for t in self.TRANSITIONS:
            if t.from_phase == self.current_phase:
                next_phases.add(t.to_phase.name)
        return sorted(next_phases)

    def reset(self) -> None:
        """Reset to initial state."""
        self.current_phase = AttackPhase.IDLE
        self.phase_history.clear()
        self.transition_log.clear()

    @property
    def is_terminal(self) -> bool:
        """Check if current state is terminal (complete or failed)."""
        return self.current_phase in (AttackPhase.COMPLETE, AttackPhase.FAILED)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state machine to dict."""
        return {
            "current_phase": self.current_phase.name,
            "history": [p.name for p in self.phase_history],
            "transitions": self.transition_log,
            "is_terminal": self.is_terminal,
        }
