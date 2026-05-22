"""
Claude (Anthropic) LLM Provider
=================================
Anthropic Claude API integration.
"""

import json
from typing import Dict, Optional, List

import httpx

from bhisma.brain.providers.base import BaseProvider


class ClaudeProvider(BaseProvider):
    """Anthropic Claude API provider."""

    provider_name = "claude"
    env_var_name = "CLAUDE_API_KEY"
    default_base_url = "https://api.anthropic.com/v1/messages"
    default_model = "claude-3-sonnet-20240229"

    def _build_payload(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
        **kwargs
    ) -> Dict:
        system = kwargs.get("system", "")
        payload = {
            "model": model or self.default_model,
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
        }
        if system:
            payload["system"] = system
        return payload

    def _build_headers(self) -> Dict[str, str]:
        return {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

    def _parse_response(self, response: httpx.Response) -> str:
        data = response.json()
        if "content" in data:
            return "".join(block.get("text", "") for block in data["content"] if block.get("type") == "text")
        if "error" in data:
            raise ValueError(f"Claude API error: {data['error']}")
        raise ValueError(f"Unexpected response: {data}")

    def _parse_stream_chunk(self, chunk: str) -> Optional[str]:
        try:
            data = json.loads(chunk)
            if data.get("type") == "content_block_delta":
                return data.get("delta", {}).get("text", "")
        except Exception:
            pass
        return None
