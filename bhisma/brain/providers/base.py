"""
Base LLM Provider
=================
Abstract base class for all LLM provider implementations.
"""

import os
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Generator
import httpx

from bhisma.utils.constants import AI_TIMEOUT_SECONDS, AI_MAX_RETRIES


class ProviderError(Exception):
    """Raised when a provider API call fails."""
    pass


class QuotaExceededError(ProviderError):
    """Raised when API quota is exceeded."""
    pass


class BaseProvider(ABC):
    """Abstract base for LLM providers."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.environ.get(self.env_var_name, "")
        self.base_url = base_url or self.default_base_url
        self.timeout = AI_TIMEOUT_SECONDS
        self.max_retries = AI_MAX_RETRIES
        self._client = httpx.Client(timeout=self.timeout)

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def env_var_name(self) -> str:
        pass

    @property
    @abstractmethod
    def default_base_url(self) -> str:
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        pass

    @abstractmethod
    def _build_payload(self, prompt: str, model: Optional[str] = None, **kwargs) -> Dict:
        """Build the request payload for this provider."""
        pass

    @abstractmethod
    def _parse_response(self, response: httpx.Response) -> str:
        """Extract text from the API response."""
        pass

    def _check_quota_error(self, response: httpx.Response) -> bool:
        """Check if response indicates quota/rate limit exceeded."""
        if response.status_code == 429:
            return True
        try:
            data = response.json()
            error_msg = str(data.get("error", "")).lower()
            if any(x in error_msg for x in ["quota", "rate limit", "too many", "exceeded"]):
                return True
        except Exception:
            pass
        return False

    def chat(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> str:
        """Send a chat completion request. Returns text response."""
        if not self.api_key:
            raise ProviderError(f"{self.provider_name}: API key not configured")

        payload = self._build_payload(
            prompt, model=model, temperature=temperature, max_tokens=max_tokens, **kwargs
        )
        headers = self._build_headers()

        last_exception = None
        for attempt in range(self.max_retries):
            try:
                response = self._client.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                )
                if self._check_quota_error(response):
                    raise QuotaExceededError(f"{self.provider_name}: quota/rate limit exceeded")
                if response.status_code >= 400:
                    raise ProviderError(
                        f"{self.provider_name}: HTTP {response.status_code} - {response.text[:200]}"
                    )
                return self._parse_response(response)
            except QuotaExceededError:
                raise
            except Exception as e:
                last_exception = e
                time.sleep(1.5 * (attempt + 1))

        raise ProviderError(
            f"{self.provider_name}: Failed after {self.max_retries} retries: {last_exception}"
        )

    def stream_chat(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> Generator[str, None, None]:
        """Stream chat completion tokens."""
        if not self.api_key:
            raise ProviderError(f"{self.provider_name}: API key not configured")

        payload = self._build_payload(
            prompt, model=model, temperature=temperature, max_tokens=max_tokens, stream=True, **kwargs
        )
        headers = self._build_headers()

        with httpx.stream(
            "POST", self.base_url, headers=headers, json=payload, timeout=self.timeout
        ) as response:
            if response.status_code >= 400:
                raise ProviderError(
                    f"{self.provider_name}: HTTP {response.status_code}"
                )
            for line in response.iter_lines():
                line = line.strip()
                if line.startswith("data: "):
                    chunk = line[6:]
                    if chunk == "[DONE]":
                        break
                    try:
                        parsed = self._parse_stream_chunk(chunk)
                        if parsed:
                            yield parsed
                    except Exception:
                        pass

    def _build_headers(self) -> Dict[str, str]:
        """Default headers. Override in subclass if needed."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _parse_stream_chunk(self, chunk: str) -> Optional[str]:
        """Override in subclass for streaming support."""
        return None

    def test_connection(self) -> bool:
        """Test if the provider API is accessible with current key."""
        try:
            # Minimal test prompt
            self.chat("Hi", max_tokens=5, temperature=0.1)
            return True
        except QuotaExceededError:
            return True  # Key works, just out of quota
        except Exception:
            return False

    def __del__(self):
        """Cleanup HTTP client."""
        try:
            self._client.close()
        except Exception:
            pass
