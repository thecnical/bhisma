# Bhisma v3.0.0 - Overview

## What is Bhisma?

Bhisma is an **AI-powered autonomous multi-protocol offensive WiFi framework** that combines traditional WiFi attack methodologies with modern artificial intelligence for fully automated penetration testing.

### Key Features

- **6-LLM AI Brain** — NVIDIA, Groq, Claude, HuggingFace, OpenRouter, Gemini with uncensored mode
- **Autonomous Attack Chain** — AI decides attack strategy from recon to post-exploitation
- **All Historical + New Attacks** — WEP, WPA2/3, WPS, WiFi 6, Mesh, MITM, Frame Injection
- **Behavioral Mimicry** — Traffic morphing to evade IDS/IPS detection
- **Real-time Web Dashboard** — Multi-panel interface with AI decision logs
- **Cross-Platform Tool Manager** — Auto-detect and install 20+ external tools
- **ML Engine** — Device fingerprinting, success prediction, anomaly detection
- **Stealth Suite** — MAC rotation, RF randomization, honeypot detection

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI / TUI                             │
│  (Commands: auto, recon, deauth, harvest, evil_twin, etc.) │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                     Core Engine                              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ State Machine│  │ Orchestrator │  │ Autonomous Mode  │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                     AI Brain                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Orchestrator │  │ Uncensor     │  │ 6 Agents         │  │
│  │ (Fallback)   │  │ Wrapper      │  │ (Strategist,     │  │
│  └─────────────┘  └──────────────┘  │  Analyzer, etc.)  │
│                                     └──────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              Attack Modules & Tools                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ WiFi     │ │ MITM     │ │ Injection│ │ Persistence  │  │
│  │ Recon    │ │ ARP/DNS  │ │ Beacon   │ │ Rogue DHCP   │  │
│  │ Deauth   │ │ SSL Strip│ │ Auth     │ │ Captive      │  │
│  │ Harvest  │ │ Session  │ │ RTS/CTS  │ │ Portal       │  │
│  │ Evil Twin│ │ Hijack   │ │ FragAtk  │ │ Fake RADIUS  │  │
│  │ WPS/WEP  │ │ SOCKS    │ │ QoS      │ │              │  │
│  │ WPA2/3   │ │          │ │          │ │              │  │
│  │ WiFi6/Mesh│          │ │          │ │              │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              Support Modules                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ Platform │ │ Tool     │ │ Stealth  │ │ ML Engine    │  │
│  │ Detection│ │ Manager  │ │ Evasion  │ │ Fingerprint  │  │
│  │ Monitor  │ │ Registry │ │ Honeypot │ │ Success Pred │  │
│  │ Mode     │ │ Binder   │ │ MAC Rot  │ │ Anomaly Det  │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              Web Dashboard                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ Network  │ │ Target   │ │ AI Brain │ │ Attack       │  │
│  │ Map      │ │ Tree     │ │ Log      │ │ Timeline     │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │
│  ┌──────────┐ ┌──────────┐                              │  │
│  │ Terminal │ │ System   │                              │  │
│  │ Panels   │ │ Status   │                              │  │
│  └──────────┘ └──────────┘                              │  │
└─────────────────────────────────────────────────────────────┘
```

### Attack Matrix

| Attack Type | Module | Status | Notes |
|-------------|--------|--------|-------|
| **Reconnaissance** | `wifi/recon.py` | ✅ Full | Passive/active scanning, hidden SSID |
| **Deauthentication** | `wifi/deauth.py` | ✅ Full | Silent pulse, directed, flood |
| **Handshake Harvest** | `wifi/harvester.py` | ✅ Full | PMKID, 4-way handshake, hashcat |
| **Evil Twin** | `wifi/evil_twin.py` | ✅ Full | KARMA, MANA, captive portal |
| **WPS Attacks** | `wifi/wps.py` | ✅ Full | Pixie Dust, brute-force, bully |
| **WEP Cracking** | `wifi/wep.py` | ✅ Full | PTW, chopchop, FMS, ARP replay |
| **WPA2 Attacks** | `wifi/wpa2.py` | ✅ Full | Handshake, PMKID, KRACK sim |
| **WPA3 Attacks** | `wifi/wpa3.py` | ✅ Full | Dragonblood, SAE downgrade |
| **WiFi 6** | `wifi/wifi6.py` | ✅ Full | HE capability, BSS collision |
| **Mesh Networks** | `wifi/mesh.py` | ✅ Full | Peering spoof, gateway impersonation |
| **MITM** | `mitm/*.py` | 📝 Stubs | ARP, DNS, DHCP, SSL strip |
| **Frame Injection** | `injection/*.py` | 📝 Stubs | Beacon flood, auth flood, FragAttacks |
| **Persistence** | `persistence/*.py` | 📝 Stubs | Rogue DHCP, DNS hijack, captive portal |

### Comparison with Other Tools

| Feature | Bhisma | Aircrack-ng | Wifite | Bettercap |
|---------|--------|-------------|--------|-----------|
| AI Brain | ✅ 6 LLMs | ❌ | ❌ | ❌ |
| Autonomous Mode | ✅ Full | ❌ | ⚠️ Partial | ⚠️ Partial |
| Real-time Dashboard | ✅ WebSocket | ❌ | ❌ | ✅ |
| Multi-LLM Fallback | ✅ | ❌ | ❌ | ❌ |
| Behavioral Mimicry | ✅ | ❌ | ❌ | ❌ |
| All WiFi Protocols | ✅ | ⚠️ Legacy | ⚠️ Legacy | ⚠️ Legacy |
| Cross-Platform | ✅ | ⚠️ Linux | ⚠️ Linux | ✅ |
| Tool Auto-Install | ✅ | ❌ | ❌ | ❌ |
| Uncensored AI | ✅ | N/A | N/A | N/A |

### Use Cases

1. **Automated Pentesting** — Full attack chain from recon to report
2. **WiFi Security Auditing** — Assess network vulnerability with AI analysis
3. **Red Team Operations** — Stealthy, adaptive attacks with evasion
4. **Security Research** — Test new attack methodologies with AI assistance
5. **Education** — Learn WiFi attacks with AI explanations

### Legal Disclaimer

Bhisma is designed for **authorized security testing only**. Unauthorized use is illegal. Always obtain explicit written permission before testing any network. The authors are not responsible for misuse.

---

**Next:** [Installation Guide](02-installation.md)
