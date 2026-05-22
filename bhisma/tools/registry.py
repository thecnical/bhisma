"""
Tool Registry
=============
Metadata registry for all external tools Bhisma can use.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List


@dataclass
class ToolMeta:
    """Metadata for an external tool."""
    name: str
    command: str
    install_linux: Optional[str] = None
    install_macos: Optional[str] = None
    install_windows: Optional[str] = None
    purpose: str = ""
    version_flag: str = "--version"
    category: str = "general"
    ai_description: str = ""
    output_format: str = "text"


TOOL_REGISTRY: Dict[str, ToolMeta] = {
    "aircrack-ng": ToolMeta(
        name="aircrack-ng",
        command="aircrack-ng",
        install_linux="apt install -y aircrack-ng",
        install_macos="brew install aircrack-ng",
        purpose="WEP/WPA password recovery suite",
        category="wifi",
        ai_description="Cracks WEP/WPA keys from captured handshakes using statistical and dictionary attacks.",
    ),
    "airodump-ng": ToolMeta(
        name="airodump-ng",
        command="airodump-ng",
        install_linux="apt install -y aircrack-ng",
        install_macos="brew install aircrack-ng",
        purpose="802.11 packet capture and network discovery",
        category="wifi",
        ai_description="Captures WiFi beacon frames and client associations to discover networks and connected devices.",
    ),
    "aireplay-ng": ToolMeta(
        name="aireplay-ng",
        command="aireplay-ng",
        install_linux="apt install -y aircrack-ng",
        install_macos="brew install aircrack-ng",
        purpose="Packet injection and replay",
        category="wifi",
        ai_description="Injects deauthentication, fake authentication, and ARP replay packets to accelerate attacks.",
    ),
    "airmon-ng": ToolMeta(
        name="airmon-ng",
        command="airmon-ng",
        install_linux="apt install -y aircrack-ng",
        install_macos="brew install aircrack-ng",
        purpose="Monitor mode management",
        category="wifi",
        ai_description="Puts wireless interfaces into monitor mode for raw 802.11 frame capture.",
    ),
    "hcxdumptool": ToolMeta(
        name="hcxdumptool",
        command="hcxdumptool",
        install_linux="apt install -y hcxtools",
        purpose="PMKID and handshake capture",
        category="wifi",
        ai_description="Captures WPA PMKID and 4-way handshakes in a single pass without targeting specific clients.",
    ),
    "hcxpcapngtool": ToolMeta(
        name="hcxpcapngtool",
        command="hcxpcapngtool",
        install_linux="apt install -y hcxtools",
        purpose="Convert captures to hashcat format",
        category="wifi",
        ai_description="Converts pcapng captures into hashcat-compatible hash files (mode 22000).",
    ),
    "reaver": ToolMeta(
        name="reaver",
        command="reaver",
        install_linux="apt install -y reaver",
        install_macos="brew install reaver",
        purpose="WPS PIN brute-force",
        category="wifi",
        ai_description="Brute-forces WPS PINs and recovers WPA/WPA2 passphrases via Pixie Dust attack.",
    ),
    "bully": ToolMeta(
        name="bully",
        command="bully",
        install_linux="apt install -y bully",
        purpose="Alternative WPS attacker",
        category="wifi",
        ai_description="Faster WPS PIN brute-forcer with built-in Pixie Dust and NULL PIN support.",
    ),
    "mdk4": ToolMeta(
        name="mdk4",
        command="mdk4",
        install_linux="apt install -y mdk4",
        purpose="Frame injection attacks",
        category="wifi",
        ai_description="Injects beacon floods, authentication floods, and deauthentication frames.",
    ),
    "hashcat": ToolMeta(
        name="hashcat",
        command="hashcat",
        install_linux="apt install -y hashcat",
        install_macos="brew install hashcat",
        purpose="GPU-accelerated password cracking",
        category="crypto",
        ai_description="World's fastest password recovery tool using GPU acceleration for WPA/WPA2 hashes.",
    ),
    "bettercap": ToolMeta(
        name="bettercap",
        command="bettercap",
        install_linux="apt install -y bettercap",
        install_macos="brew install bettercap",
        purpose="MITM framework",
        category="mitm",
        ai_description="Swiss-army knife for MITM attacks: ARP spoofing, DNS hijacking, SSL stripping, credential harvesting.",
    ),
    "hostapd": ToolMeta(
        name="hostapd",
        command="hostapd",
        install_linux="apt install -y hostapd",
        install_macos="brew install hostapd",
        purpose="Rogue AP creation",
        category="wifi",
        ai_description="Creates software access points for evil twin, KARMA, and captive portal attacks.",
    ),
    "dnsmasq": ToolMeta(
        name="dnsmasq",
        command="dnsmasq",
        install_linux="apt install -y dnsmasq",
        install_macos="brew install dnsmasq",
        purpose="DHCP/DNS for rogue AP",
        category="network",
        ai_description="Lightweight DHCP and DNS server for rogue access point environments.",
    ),
    "tshark": ToolMeta(
        name="tshark",
        command="tshark",
        install_linux="apt install -y tshark",
        install_macos="brew install wireshark",
        purpose="Deep packet analysis",
        category="network",
        ai_description="Command-line Wireshark for automated packet dissection and filtering.",
    ),
    "macchanger": ToolMeta(
        name="macchanger",
        command="macchanger",
        install_linux="apt install -y macchanger",
        install_macos="brew install macchanger",
        purpose="MAC address spoofing",
        category="stealth",
        ai_description="Changes MAC addresses for identity obfuscation and OUI-based vendor spoofing.",
    ),
    "iw": ToolMeta(
        name="iw",
        command="iw",
        install_linux="apt install -y iw",
        purpose="Linux wireless configuration",
        category="wifi",
        ai_description="Modern Linux wireless utility for interface control and monitor mode.",
    ),
    "iwconfig": ToolMeta(
        name="iwconfig",
        command="iwconfig",
        install_linux="apt install -y wireless-tools",
        purpose="Legacy wireless configuration",
        category="wifi",
        ai_description="Legacy wireless configuration tool for compatibility.",
    ),
    "yersinia": ToolMeta(
        name="yersinia",
        command="yersinia",
        install_linux="apt install -y yersinia",
        purpose="Layer-2 attack framework",
        category="network",
        ai_description="Framework for Layer-2 protocol attacks: DHCP, STP, CDP, DTP.",
    ),
    "mitmproxy": ToolMeta(
        name="mitmproxy",
        command="mitmproxy",
        install_linux="pip install mitmproxy",
        install_macos="pip install mitmproxy",
        install_windows="pip install mitmproxy",
        purpose="Traffic interception proxy",
        category="mitm",
        ai_description="Interactive HTTPS proxy for traffic interception and modification.",
    ),
    "npcap": ToolMeta(
        name="npcap",
        command="NpcapHelper.exe",
        install_windows="https://npcap.com/dist/npcap-1.79.exe",
        purpose="Windows raw 802.11 capture driver",
        category="driver",
        ai_description="Windows packet capture driver enabling raw 802.11 frame access.",
    ),
}


def get_tool(name: str) -> Optional[ToolMeta]:
    """Get tool metadata by name."""
    return TOOL_REGISTRY.get(name)


def list_tools(category: Optional[str] = None) -> List[ToolMeta]:
    """List all tools, optionally filtered by category."""
    if category:
        return [t for t in TOOL_REGISTRY.values() if t.category == category]
    return list(TOOL_REGISTRY.values())


# Alias for compatibility
ToolRegistry = TOOL_REGISTRY


def list_categories() -> List[str]:
    """Return list of tool categories."""
    return sorted({t.category for t in TOOL_REGISTRY.values()})
