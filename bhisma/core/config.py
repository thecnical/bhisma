"""
Configuration Management
========================
Pydantic-based configuration for Bhisma framework.
"""

import os
import yaml
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class AIConfig(BaseModel):
    """AI / LLM configuration."""
    nvidia_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    claude_api_key: Optional[str] = None
    huggingface_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    timeout_seconds: int = 60
    max_retries: int = 3
    uncensored_mode: bool = True
    fallback_chain: List[tuple] = Field(default_factory=list)
    enable_ai_brain: bool = True
    ai_memory_limit: int = 20  # conversation turns to keep


class ToolConfig(BaseModel):
    """External tool configuration."""
    auto_install: bool = True
    install_timeout: int = 300
    tool_paths: Dict[str, str] = Field(default_factory=dict)
    check_on_startup: bool = True


class WiFiConfig(BaseModel):
    """WiFi-specific configuration."""
    default_interface: Optional[str] = None
    scan_channels: List[int] = Field(default_factory=list)  # empty = all
    dwell_time: float = 0.5
    auto_target_timeout: int = 20  # seconds before auto-select
    deauth_count: int = 3
    silent_deauth_enabled: bool = True
    evil_twin_portal_enabled: bool = True
    handshake_auto_crack: bool = True
    wordlist_url: str = "https://github.com/danielmiessler/SecLists/raw/master/Passwords/Common-Credentials/rockyou.txt.tar.gz"


class MITMConfig(BaseModel):
    """MITM configuration."""
    arp_spoof_enabled: bool = True
    dns_spoof_enabled: bool = True
    ssl_strip_enabled: bool = False
    rogue_dhcp_enabled: bool = True
    socks_proxy_port: int = 1080
    traffic_capture_enabled: bool = True


class DashboardConfig(BaseModel):
    """Web dashboard configuration."""
    enabled: bool = True
    host: str = "127.0.0.1"
    port: int = 8080
    auto_open_browser: bool = True
    websocket_max_size: int = 1048576


class AutonomousConfig(BaseModel):
    """Autonomous mode configuration."""
    enabled: bool = True
    daemon_poll_interval: float = 5.0
    max_concurrent_attacks: int = 3
    safety_whitelist: List[str] = Field(default_factory=list)
    safety_blacklist: List[str] = Field(default_factory=list)
    rules_file: Optional[str] = None
    enable_ml_models: bool = True


class StealthConfig(BaseModel):
    """Stealth / evasion configuration."""
    mac_rotation_interval: int = 300  # seconds
    oui_consistency: bool = True
    timing_jitter: bool = True
    honeypot_auto_detect: bool = True
    rf_randomization: bool = True


class BhismaConfig(BaseModel):
    """Root configuration model."""
    framework_name: str = "Bhisma"
    version: str = "3.0.0"
    data_dir: str = os.path.expanduser("~/.bhisma")
    log_level: str = "INFO"
    log_file: Optional[str] = None
    ai: AIConfig = Field(default_factory=AIConfig)
    tools: ToolConfig = Field(default_factory=ToolConfig)
    wifi: WiFiConfig = Field(default_factory=WiFiConfig)
    mitm: MITMConfig = Field(default_factory=MITMConfig)
    dashboard: DashboardConfig = Field(default_factory=DashboardConfig)
    autonomous: AutonomousConfig = Field(default_factory=AutonomousConfig)
    stealth: StealthConfig = Field(default_factory=StealthConfig)

    @classmethod
    def load(cls, path: Optional[str] = None) -> "BhismaConfig":
        """Load configuration from YAML file or return defaults."""
        if path and os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return cls(**data)
        return cls()

    def save(self, path: Optional[str] = None) -> None:
        """Save configuration to YAML file."""
        target = path or os.path.join(self.data_dir, "config.yaml")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False, sort_keys=False)

    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        dirs = [
            self.data_dir,
            os.path.join(self.data_dir, "logs"),
            os.path.join(self.data_dir, "captures"),
            os.path.join(self.data_dir, "wordlists"),
            os.path.join(self.data_dir, "reports"),
            os.path.join(self.data_dir, "models"),
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)
