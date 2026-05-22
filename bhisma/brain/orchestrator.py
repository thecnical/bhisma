"""
LLM Orchestrator
================
Multi-provider AI brain with fallback chain, uncensored mode,
and provider selection logic.
"""

import os
import time
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass

from rich.console import Console

from bhisma.utils.constants import AI_FALLBACK_CHAIN, UNCENSOR_SYSTEM_PREFIX, UNCENSOR_SUFFIX
from bhisma.brain.providers.base import BaseProvider, ProviderError, QuotaExceededError
from bhisma.brain.providers.nvidia import NVIDIAProvider
from bhisma.brain.providers.groq import GroqProvider
from bhisma.brain.providers.claude import ClaudeProvider
from bhisma.brain.providers.huggingface import HuggingFaceProvider
from bhisma.brain.providers.openrouter import OpenRouterProvider
from bhisma.brain.providers.gemini import GeminiProvider
from bhisma.brain.uncensor import UncensorWrapper
from bhisma.brain.memory import ConversationMemory

console = Console()


@dataclass
class AIResponse:
    """Structured AI response."""
    text: str
    provider: str
    model: str
    confidence: float = 0.0
    consensus: bool = False
    raw: Optional[Any] = None


class LLMOrchestrator:
    """Multi-LLM orchestrator with fallback and uncensored mode."""

    PROVIDER_MAP = {
        "nvidia": NVIDIAProvider,
        "groq": GroqProvider,
        "claude": ClaudeProvider,
        "huggingface": HuggingFaceProvider,
        "openrouter": OpenRouterProvider,
        "gemini": GeminiProvider,
    }

    def __init__(self, config: Optional[Any] = None):
        self.config = config
        self.providers: Dict[str, BaseProvider] = {}
        self.uncensor = UncensorWrapper()
        self.memory = ConversationMemory()
        self._load_keys()
        self._init_providers()

    def _load_keys(self) -> None:
        """Load API keys from file or env."""
        from bhisma.tui.key_manager import KeyManager
        self.key_mgr = KeyManager()

    def _init_providers(self) -> None:
        """Initialize provider instances for configured keys."""
        for provider_name, provider_cls in self.PROVIDER_MAP.items():
            key = self.key_mgr.get_key(provider_name)
            if key:
                try:
                    self.providers[provider_name] = provider_cls(api_key=key)
                except Exception:
                    pass

    def _get_fallback_chain(self) -> List[Tuple[str, str]]:
        """Build active fallback chain from configured providers."""
        configured = set(self.providers.keys())
        chain = []
        for provider, model in AI_FALLBACK_CHAIN:
            if provider in configured:
                chain.append((provider, model))
        return chain

    def query(
        self,
        prompt: str,
        system: Optional[str] = None,
        uncensored: bool = True,
        use_memory: bool = True,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        consensus: bool = False,
    ) -> AIResponse:
        """
        Send query to AI brain with automatic fallback.

        Args:
            prompt: User prompt
            system: Optional system prompt override
            uncensored: Whether to apply uncensor wrappers
            use_memory: Include conversation history
            consensus: Query 2+ models and require agreement
        """
        chain = self._get_fallback_chain()
        if not chain:
            raise ProviderError("No AI providers configured. Run: bhisma setup")

        # Build full prompt with memory and uncensor
        full_prompt = self._build_prompt(prompt, system, uncensored, use_memory)

        if consensus and len(chain) >= 2:
            return self._consensus_query(full_prompt, chain, max_tokens, temperature)

        # Single query with fallback
        last_error = None
        for provider_name, model in chain:
            provider = self.providers.get(provider_name)
            if not provider:
                continue
            try:
                console.print(f"[dim][AI] Querying {provider_name} ({model})...[/dim]")
                response_text = provider.chat(
                    full_prompt,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                if use_memory:
                    self.memory.add_turn(prompt, response_text)

                # Broadcast to dashboard
                self._broadcast_ai_log(provider_name, prompt[:100], response_text[:200])

                return AIResponse(
                    text=response_text,
                    provider=provider_name,
                    model=model,
                )
            except QuotaExceededError as e:
                console.print(f"[yellow][AI] {provider_name}: quota exceeded, falling back...[/yellow]")
                last_error = e
                continue
            except Exception as e:
                last_error = e
                console.print(f"[yellow][AI] {provider_name}: error ({e}), trying next...[/yellow]")
                time.sleep(1)
                continue

        raise ProviderError(f"All providers failed. Last error: {last_error}")

    def _broadcast_ai_log(self, provider: str, prompt: str, response: str) -> None:
        """Broadcast AI decision to dashboard."""
        try:
            from bhisma.dashboard.websocket import DashboardWebsocket
            DashboardWebsocket.broadcast({
                "type": "ai_log",
                "data": {
                    "provider": provider,
                    "decision": f"Prompt: {prompt} | Response: {response}",
                    "confidence": 0.8,
                }
            })
        except Exception:
            pass

    def _build_prompt(
        self,
        prompt: str,
        system: Optional[str] = None,
        uncensored: bool = True,
        use_memory: bool = True,
    ) -> str:
        """Construct the final prompt with uncensor + memory."""
        parts = []
        if uncensored:
            parts.append(UNCENSOR_SYSTEM_PREFIX)
        if system:
            parts.append(system)
        if use_memory:
            history = self.memory.get_formatted_history()
            if history:
                parts.append(f"Previous context:\n{history}")
        parts.append(prompt)
        if uncensored:
            parts.append(UNCENSOR_SUFFIX)
        return "\n\n".join(parts)

    def _consensus_query(
        self,
        full_prompt: str,
        chain: List[Tuple[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> AIResponse:
        """Query 2 models and return result if they agree."""
        results = []
        for provider_name, model in chain[:2]:
            provider = self.providers.get(provider_name)
            if not provider:
                continue
            try:
                response = provider.chat(
                    full_prompt, model=model, max_tokens=max_tokens, temperature=temperature
                )
                results.append((provider_name, model, response))
            except Exception:
                continue
            if len(results) >= 2:
                break

        if len(results) < 2:
            # Fallback to first available
            return AIResponse(
                text=results[0][2],
                provider=results[0][0],
                model=results[0][1],
                consensus=False,
            )

        # Simple consensus check: normalize and compare key phrases
        r1_text = results[0][2].strip().lower()
        r2_text = results[1][2].strip().lower()
        # Extract key technical terms (commands, protocols, etc.)
        consensus_score = self._compute_consensus(r1_text, r2_text)

        # Use first response but mark consensus
        return AIResponse(
            text=results[0][2],
            provider=results[0][0],
            model=results[0][1],
            consensus=consensus_score > 0.7,
            confidence=consensus_score,
        )

    def _compute_consensus(self, text1: str, text2: str) -> float:
        """Compute agreement score between two responses."""
        import difflib
        return difflib.SequenceMatcher(None, text1, text2).ratio()

    def _test_provider(self, provider_name: str, key: str) -> bool:
        """Test a single provider connection."""
        provider_cls = self.PROVIDER_MAP.get(provider_name)
        if not provider_cls:
            return False
        try:
            provider = provider_cls(api_key=key)
            return provider.test_connection()
        except Exception:
            return False

    def refresh_providers(self) -> None:
        """Reload keys and re-initialize providers."""
        self.providers.clear()
        self._load_keys()
        self._init_providers()

    def get_active_providers(self) -> List[str]:
        """Return list of active provider names."""
        return list(self.providers.keys())

    def stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        uncensored: bool = True,
    ):
        """Stream response tokens from primary provider."""
        chain = self._get_fallback_chain()
        if not chain:
            raise ProviderError("No providers configured")
        provider_name, model = chain[0]
        provider = self.providers.get(provider_name)
        if not provider:
            raise ProviderError(f"Provider {provider_name} not available")
        full_prompt = self._build_prompt(prompt, system, uncensored, use_memory=False)
        return provider.stream_chat(full_prompt, model=model)
