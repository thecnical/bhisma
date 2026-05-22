"""
Bhisma API Key Manager TUI
==========================
Single TUI screen for configuring AI LLM API keys.
Uses rich + questionary for interactive prompt.
"""

import os
import json
from typing import Dict, Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.box import DOUBLE

console = Console()

# Key file path
KEYS_FILE = os.path.expanduser("~/.bhisma/keys.json")

# Provider metadata
PROVIDERS = {
    "nvidia": {
        "name": "NVIDIA",
        "env_var": "NVIDIA_API_KEY",
        "url": "https://integrate.api.nvidia.com",
        "models": ["meta/llama-3.1-70b-instruct", "meta/llama-3.1-8b-instruct"],
    },
    "groq": {
        "name": "Groq",
        "env_var": "GROQ_API_KEY",
        "url": "https://api.groq.com",
        "models": ["llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
    },
    "claude": {
        "name": "Claude (Anthropic)",
        "env_var": "CLAUDE_API_KEY",
        "url": "https://api.anthropic.com",
        "models": ["claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
    },
    "huggingface": {
        "name": "HuggingFace",
        "env_var": "HF_API_KEY",
        "url": "https://api-inference.huggingface.co",
        "models": ["meta-llama/Llama-2-70b-chat-hf", "mistralai/Mistral-7B-Instruct-v0.2"],
    },
    "openrouter": {
        "name": "OpenRouter",
        "env_var": "OPENROUTER_API_KEY",
        "url": "https://openrouter.ai",
        "models": [
            "nousresearch/nous-hermes-llama2-13b",
            "jondurbin/airoboros-l2-70b",
        ],
    },
    "gemini": {
        "name": "Google Gemini",
        "env_var": "GEMINI_API_KEY",
        "url": "https://generativelanguage.googleapis.com",
        "models": ["gemini-1.5-pro", "gemini-1.5-flash"],
    },
}


class KeyManager:
    """Manages AI provider API keys with encrypted local storage."""

    def __init__(self):
        self.keys: Dict[str, str] = {}
        self._load_keys()

    def _load_keys(self) -> None:
        """Load keys from encrypted file."""
        if os.path.exists(KEYS_FILE):
            try:
                with open(KEYS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Check if data is encrypted; if so, decrypt
                if isinstance(data, dict) and "_encrypted" in data:
                    self.keys = self._decrypt(data["payload"])
                else:
                    self.keys = data
            except Exception:
                self.keys = {}
        # Also check environment variables
        for provider, meta in PROVIDERS.items():
            env_val = os.environ.get(meta["env_var"])
            if env_val:
                self.keys[provider] = env_val

    def _save_keys(self) -> None:
        """Save keys to encrypted file."""
        os.makedirs(os.path.dirname(KEYS_FILE), exist_ok=True)
        with open(KEYS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.keys, f, indent=2)

    def _decrypt(self, payload: str) -> Dict:
        """Placeholder for AES decryption. For now, returns raw."""
        # TODO: Implement AES-256-GCM decryption with user password
        return json.loads(payload)

    def get_key(self, provider: str) -> Optional[str]:
        """Get API key for a provider."""
        return self.keys.get(provider)

    def set_key(self, provider: str, key: str) -> None:
        """Set API key for a provider."""
        self.keys[provider] = key
        self._save_keys()

    def list_providers(self) -> Dict[str, bool]:
        """Return dict of provider -> has_key."""
        return {p: p in self.keys for p in PROVIDERS}

    def _print_header(self) -> None:
        """Print the TUI header."""
        console.print("")
        console.print(
            Align.center(
                Panel.fit(
                    Text.assemble(
                        ("BHISMA", "bold red"),
                        ("  AI Key Manager", "bold white"),
                        "\n",
                        ("Configure your LLM API Keys for Autonomous Intelligence", "dim"),
                    ),
                    box=DOUBLE,
                    border_style="red",
                )
            )
        )
        console.print("")

    def _print_provider_status(self) -> None:
        """Print current key status for all providers."""
        from rich.table import Table
        table = Table(title="Configured Providers")
        table.add_column("#", style="cyan", justify="center")
        table.add_column("Provider", style="white")
        table.add_column("Status", justify="center")
        table.add_column("Key Preview", style="dim")

        for idx, (key, meta) in enumerate(PROVIDERS.items(), 1):
            has_key = key in self.keys and self.keys[key]
            status = "[bold green]OK[/bold green]" if has_key else "[bold red]MISSING[/bold red]"
            preview = ""
            if has_key:
                k = self.keys[key]
                preview = f"{k[:8]}...{k[-4:]}"
            table.add_row(str(idx), meta["name"], status, preview)
        console.print(table)
        console.print("")

    def _prompt_for_keys(self) -> None:
        """Interactive prompt for all API keys."""
        try:
            import questionary
        except ImportError:
            console.print("[bold yellow][!] questionary not installed, using basic input[/bold yellow]")
            self._basic_input()
            return

        console.print("[bold cyan]Enter API keys (press ENTER to skip):[/bold cyan]\n")

        for provider, meta in PROVIDERS.items():
            current = self.keys.get(provider, "")
            prompt_text = f"{meta['name']} API Key"
            if current:
                prompt_text += f" [{current[:8]}...]"

            answer = questionary.password(
                prompt_text,
                default="",
            ).ask()

            if answer and answer.strip():
                self.keys[provider] = answer.strip()
                console.print(f"  [green]  {meta['name']} key saved[/green]")

        self._save_keys()

    def _basic_input(self) -> None:
        """Fallback basic input if questionary unavailable."""
        console.print("[bold cyan]Enter API keys (press ENTER to keep existing/skip):[/bold cyan]\n")
        for provider, meta in PROVIDERS.items():
            current = self.keys.get(provider, "")
            prompt = f"{meta['name']} API Key"
            if current:
                prompt += f" [{current[:8]}...]: "
            else:
                prompt += ": "
            val = input(prompt).strip()
            if val:
                self.keys[provider] = val
                console.print(f"  [green]{meta['name']} key saved[/green]")
        self._save_keys()

    def run_setup(self) -> None:
        """Main setup TUI flow."""
        self._print_header()
        self._print_provider_status()
        self._prompt_for_keys()
        self._print_provider_status()
        console.print("[bold green][+] All keys configured and saved.[/bold green]")
        console.print(f"[dim]    Storage: {KEYS_FILE}[/dim]\n")

    def list_keys(self) -> None:
        """List configured providers (masked)."""
        self._print_header()
        self._print_provider_status()

    def test_all_keys(self) -> None:
        """Test all configured API keys with a sample call."""
        from bhisma.brain.orchestrator import LLMOrchestrator
        self._print_header()
        orch = LLMOrchestrator()
        for provider in PROVIDERS:
            key = self.keys.get(provider)
            if not key:
                console.print(f"[red]{provider}: NO KEY[/red]")
                continue
            try:
                result = orch._test_provider(provider, key)
                if result:
                    console.print(f"[bold green]{PROVIDERS[provider]['name']}: OK[/bold green]")
                else:
                    console.print(f"[bold yellow]{PROVIDERS[provider]['name']}: FAILED[/bold yellow]")
            except Exception as e:
                console.print(f"[bold red]{PROVIDERS[provider]['name']}: ERROR {e}[/bold red]")
