"""
Google Gemini LLM Provider
============================
Gemini API integration via Google AI Studio.
"""

import json
from typing import Dict, Optional

import httpx

from bhisma.brain.providers.base import BaseProvider


class GeminiProvider(BaseProvider):
    """Google Gemini API provider."""

    provider_name = "gemini"
    env_var_name = "GEMINI_API_KEY"
    default_base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent"
    default_model = "gemini-1.5-pro"

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        # Gemini uses URL query param for key, so we store it separately
        super().__init__(api_key=api_key, base_url=base_url)
        self._api_key_query = f"?key={self.api_key}"
        self.base_url = (base_url or self.default_base_url) + self._api_key_query

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
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": kwargs.get("system", "") + "\n\n" + prompt if kwargs.get("system") else prompt}
                    ],
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

    def _build_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
        }

    def _parse_response(self, response: httpx.Response) -> str:
        data = response.json()
        if "candidates" in data and data["candidates"]:
            parts = data["candidates"][0].get("content", {}).get("parts", [])
            return "".join(p.get("text", "") for p in parts)
        if "error" in data:
            raise ValueError(f"Gemini API error: {data['error']}")
        raise ValueError(f"Unexpected response: {data}")

    def _parse_stream_chunk(self, chunk: str) -> Optional[str]:
        try:
            data = json.loads(chunk)
            if "candidates" in data and data["candidates"]:
                parts = data["candidates"][0].get("content", {}).get("parts", [])
                return "".join(p.get("text", "") for p in parts)
        except Exception:
            pass
        return None

    def test_connection(self) -> bool:
        """Override test to handle Gemini URL structure."""
        try:
            payload = self._build_payload("Hello", max_tokens=5, temperature=0.1)
            response = self._client.post(
                self.base_url,
                headers=self._build_headers(),
                json=payload,
            )
            if response.status_code == 200:
                return True
            if response.status_code == 429:
                return True  # Key works, quota issue
            return False
        except Exception:
            return False
