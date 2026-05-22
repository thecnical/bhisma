"""
HuggingFace Inference API Provider
==================================
Integration with HuggingFace Inference Endpoints.
Supports uncensored models via custom endpoints.
"""

import json
from typing import Dict, Optional

import httpx

from bhisma.brain.providers.base import BaseProvider


class HuggingFaceProvider(BaseProvider):
    """HuggingFace Inference API provider."""

    provider_name = "huggingface"
    env_var_name = "HF_API_KEY"
    default_base_url = "https://api-inference.huggingface.co/models/meta-llama/Llama-2-70b-chat-hf"
    default_model = "meta-llama/Llama-2-70b-chat-hf"

    def _build_payload(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
        **kwargs
    ) -> Dict:
        # For HF text generation inference, input is just the prompt text
        # We use the chat template via prompt injection
        system = kwargs.get("system", "")
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        return {
            "inputs": full_prompt,
            "parameters": {
                "temperature": temperature,
                "max_new_tokens": max_tokens,
                "return_full_text": False,
            },
        }

    def _parse_response(self, response: httpx.Response) -> str:
        data = response.json()
        # HF returns a list of generated texts
        if isinstance(data, list) and data:
            return data[0].get("generated_text", "")
        if isinstance(data, dict):
            return data.get("generated_text", "")
        raise ValueError(f"Unexpected response: {data}")

    def _build_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _parse_stream_chunk(self, chunk: str) -> Optional[str]:
        return None  # Streaming not standardized on HF
