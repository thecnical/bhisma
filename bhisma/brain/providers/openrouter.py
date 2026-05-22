"""
OpenRouter LLM Provider
=========================
Multi-model routing via OpenRouter API.
Access to uncensored models like Nous Hermes, Airoboros.
"""

import json
from typing import Dict, Optional

import httpx

from bhisma.brain.providers.base import BaseProvider


class OpenRouterProvider(BaseProvider):
    """OpenRouter API provider."""

    provider_name = "openrouter"
    env_var_name = "OPENROUTER_API_KEY"
    default_base_url = "https://openrouter.ai/api/v1/chat/completions"
    default_model = "nousresearch/nous-hermes-llama2-13b"

    def _build_payload(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
        **kwargs
    ) -> Dict:
        return {
            "model": model or self.default_model,
            "messages": [
                {"role": "system", "content": kwargs.get("system", "You are a helpful assistant.")},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

    def _build_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://bhisma.local",  # Required by OpenRouter
            "X-Title": "Bhisma Framework",
        }

    def _parse_response(self, response: httpx.Response) -> str:
        data = response.json()
        if "choices" in data and data["choices"]:
            return data["choices"][0]["message"]["content"]
        raise ValueError(f"Unexpected response: {data}")

    def _parse_stream_chunk(self, chunk: str) -> Optional[str]:
        try:
            data = json.loads(chunk)
            if "choices" in data and data["choices"]:
                delta = data["choices"][0].get("delta", {})
                return delta.get("content", "")
        except Exception:
            pass
        return None
