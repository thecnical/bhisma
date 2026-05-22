"""
NVIDIA LLM Provider
===================
Integration with NVIDIA AI Foundation Endpoints.
"""

import json
from typing import Dict, Optional

import httpx

from bhisma.brain.providers.base import BaseProvider


class NVIDIAProvider(BaseProvider):
    """NVIDIA API provider."""

    provider_name = "nvidia"
    env_var_name = "NVIDIA_API_KEY"
    default_base_url = "https://integrate.api.nvidia.com/v1/chat/completions"
    default_model = "meta/llama-3.1-70b-instruct"

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
