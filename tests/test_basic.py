"""
Basic Tests for Bhisma Framework
"""

import pytest
from bhisma.core.config import BhismaConfig
from bhisma.utils.platform import BhismaPlatform
from bhisma.brain.providers.nvidia import NVIDIAProvider


def test_config_load():
    config = BhismaConfig.load()
    assert config.framework_name == "Bhisma"
    assert config.version == "3.0.0"


def test_platform_detection():
    platform = BhismaPlatform()
    assert platform.platform_type is not None


def test_provider_initialization():
    provider = NVIDIAProvider(api_key="fake-key-for-test")
    assert provider.provider_name == "nvidia"
