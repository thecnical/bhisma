"""
Bhisma Framework Test Suite
============================
Comprehensive tests for core functionality.
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================
# CONFIG TESTS
# ============================================================
class TestConfig:
    """Test configuration loading and validation."""

    def test_config_load(self):
        from bhisma.core.config import BhismaConfig
        config = BhismaConfig.load()
        assert config.framework_name == "Bhisma"
        assert config.version == "3.0.0"

    def test_config_singleton(self):
        from bhisma.core.config import BhismaConfig
        c1 = BhismaConfig.load()
        c2 = BhismaConfig.load()
        assert c1 is c2


# ============================================================
# PLATFORM TESTS
# ============================================================
class TestPlatform:
    """Test platform detection utilities."""

    def test_platform_detection(self):
        from bhisma.utils.platform import PLATFORM
        assert PLATFORM.os is not None
        assert PLATFORM.os in ["linux", "windows", "darwin"]

    def test_is_linux(self):
        from bhisma.utils.platform import PLATFORM
        result = PLATFORM.is_linux
        assert isinstance(result, bool)

    def test_is_windows(self):
        from bhisma.utils.platform import PLATFORM
        result = PLATFORM.is_windows
        assert isinstance(result, bool)

    def test_is_macos(self):
        from bhisma.utils.platform import PLATFORM
        result = PLATFORM.is_macos
        assert isinstance(result, bool)


# ============================================================
# AI PROVIDER TESTS
# ============================================================
class TestAIProviders:
    """Test LLM provider initialization and API."""

    def test_nvidia_provider_init(self):
        from bhisma.brain.providers.nvidia import NVIDIAProvider
        provider = NVIDIAProvider(api_key="fake-key-for-test")
        assert provider.provider_name == "nvidia"
        assert provider.is_configured is True

    def test_groq_provider_init(self):
        from bhisma.brain.providers.groq import GroqProvider
        provider = GroqProvider(api_key="fake-key-for-test")
        assert provider.provider_name == "groq"

    def test_claude_provider_init(self):
        from bhisma.brain.providers.claude import ClaudeProvider
        provider = ClaudeProvider(api_key="fake-key-for-test")
        assert provider.provider_name == "claude"

    def test_huggingface_provider_init(self):
        from bhisma.brain.providers.huggingface import HuggingFaceProvider
        provider = HuggingFaceProvider(api_key="fake-key-for-test")
        assert provider.provider_name == "huggingface"

    def test_openrouter_provider_init(self):
        from bhisma.brain.providers.openrouter import OpenRouterProvider
        provider = OpenRouterProvider(api_key="fake-key-for-test")
        assert provider.provider_name == "openrouter"

    def test_gemini_provider_init(self):
        from bhisma.brain.providers.gemini import GeminiProvider
        provider = GeminiProvider(api_key="fake-key-for-test")
        assert provider.provider_name == "gemini"

    def test_provider_without_api_key(self):
        from bhisma.brain.providers.base import BaseProvider
        provider = BaseProvider()
        assert provider.is_configured is False


# ============================================================
# AI ORCHESTRATOR TESTS
# ============================================================
class TestAIOrchestrator:
    """Test AI orchestrator with fallback and consensus."""

    def test_orchestrator_init(self):
        from bhisma.brain.orchestrator import AIOrchestrator
        orch = AIOrchestrator()
        assert orch is not None

    def test_orchestrator_with_mock_providers(self):
        from bhisma.brain.orchestrator import AIOrchestrator
        orch = AIOrchestrator()
        # Should handle missing providers gracefully
        result = orch.query("test prompt", mode="fallback")
        assert result is not None or result == {}


# ============================================================
# WIFI MODULE TESTS
# ============================================================
class TestWiFiModules:
    """Test WiFi attack module interfaces."""

    def test_recon_init(self):
        from bhisma.wifi.recon import NetworkRecon
        recon = NetworkRecon()
        assert recon is not None

    def test_deauth_engine_init(self):
        from bhisma.wifi.deauth import DeauthEngine
        engine = DeauthEngine()
        assert engine is not None

    def test_harvester_init(self):
        from bhisma.wifi.harvester import HandshakeHarvester
        harvester = HandshakeHarvester()
        assert harvester is not None


# ============================================================
# CORE ENGINE TESTS
# ============================================================
class TestCoreEngine:
    """Test main attack orchestrator."""

    def test_engine_init(self):
        from bhisma.core.engine import BhismaEngine
        engine = BhismaEngine()
        assert engine is not None

    def test_state_machine_init(self):
        from bhisma.core.state_machine import AttackStateMachine
        sm = AttackStateMachine()
        assert sm is not None


# ============================================================
# TOOL MANAGEMENT TESTS
# ============================================================
class TestToolManagement:
    """Test external tool detection and management."""

    def test_registry_init(self):
        from bhisma.tools.registry import ToolRegistry
        registry = ToolRegistry()
        assert registry is not None

    def test_manager_init(self):
        from bhisma.tools.manager import ToolManager
        manager = ToolManager()
        assert manager is not None


# ============================================================
# DASHBOARD TESTS
# ============================================================
class TestDashboard:
    """Test web dashboard components."""

    def test_websocket_init(self):
        from bhisma.dashboard.websocket import DashboardWebsocket
        ws = DashboardWebsocket()
        assert ws is not None

    def test_server_import(self):
        from bhisma.dashboard.server import start_dashboard
        assert callable(start_dashboard)


# ============================================================
# DEPENDENCY TESTS
# ============================================================
class TestDependencies:
    """Test dependency manager."""

    def test_dependency_manager_init(self):
        from bhisma.utils.deps import DependencyManager
        mgr = DependencyManager()
        assert mgr is not None

    def test_check_environment(self):
        from bhisma.utils.deps import DependencyManager
        mgr = DependencyManager()
        result = mgr.check_environment()
        assert isinstance(result, dict)
        assert "pip_available" in result


# ============================================================
# SECURITY TESTS
# ============================================================
class TestSecurity:
    """Test security features and safety gates."""

    def test_safety_gate_init(self):
        from bhisma.core.autonomous.safety_gate import SafetyGate
        gate = SafetyGate()
        assert gate is not None


# ============================================================
# INTEGRATION TESTS
# ============================================================
@pytest.mark.integration
class TestIntegration:
    """Integration tests requiring full environment."""

    def test_framework_imports(self):
        """Verify all main modules can be imported."""
        import bhisma
        import bhisma.cli.main
        import bhisma.core.engine
        import bhisma.brain.orchestrator
        import bhisma.wifi.recon
        import bhisma.dashboard.server
        assert bhisma.__version__ == "3.0.0"
