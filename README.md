<div align="center">

# 🔥 BHISMA v3.0.0

### AI-Powered Autonomous Multi-Protocol Offensive WiFi Framework

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-red.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey.svg)](https://github.com/bhisma-team/bhisma)
[![AI](https://img.shields.io/badge/AI-6%20LLMs-purple.svg)](docs/01-overview.md)

```
 ██░ ██ ▓██   ██▓▄▄▄       █     █░
▓██░ ██▒ ▒██  ██▒▒████▄    ▓█░ █ ░█░▒
▒██▀▀██░  ▒██ ██░▒██  ▀█▄  ▒█░ █ ░█ ░
░▓█ ░██   ░ ▐██▓░░██▄▄▄▄██ ░█░ █ ░█ ░
░▓█▒░██▒ ░ ██▒▓░ ▓█   ▓██▒░░██▒██▓ ░
 ▒ ░░▒░▒  ██▒▒▒  ▒▒   ▒▒▒░ ░ ▓░▒ ▒  ░
```

**Fully autonomous WiFi penetration testing with 6-LLM AI brain, behavioral mimicry, and real-time web dashboard.**

[Features](#-features) • [Installation](#-installation) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Attack Matrix](#-attack-matrix)

</div>

---

## ✨ Features

### 🧠 AI-Powered Intelligence
- **6-LLM Multi-Provider Brain** — NVIDIA, Groq, Claude, HuggingFace, OpenRouter, Gemini
- **Uncensored Mode** — Prompt injection bypass for full technical disclosure
- **AI Agents** — Strategist, Analyzer, Decider, Researcher, Reporter, Coder
- **Consensus Mode** — Query 2+ LLMs for reliable decisions
- **Automatic Fallback** — Seamless provider switching on quota/errors

### 🚀 Autonomous Operations
- **One-Command Attack Chain** — `bhisma auto` handles everything
- **Smart Target Selection** — AI vulnerability scoring and prioritization
- **Adaptive Strategy** — AI adjusts tactics based on real-time results
- **Background Daemon** — Scheduled attacks with rule engine
- **Safety Gate** — Whitelist/blacklist protection

### 🎯 Complete WiFi Arsenal
- **Historical Attacks** — WEP, WPA2, WPA3, WPS (all variants)
- **Modern Attacks** — WiFi 6/6E, Mesh Networks, FragAttacks
- **Deauthentication** — Silent pulse, directed, flood, fake
- **Evil Twin** — Basic, KARMA, MANA, captive portal
- **MITM Suite** — ARP, DNS, DHCP, SSL strip, session hijack
- **Frame Injection** — Beacon flood, auth flood, RTS/CTS, QoS

### 🛡️ Stealth & Evasion
- **Behavioral Mimicry** — Traffic morphing to match target profiles
- **MAC Rotation** — Vendor OUI-consistent randomization
- **RF Randomization** — Transmit power and timing variation
- **Honeypot Detection** — ML-based identification
- **IDS Evasion** — Timing jitter, fragmentation, rate randomization

### 📊 Real-Time Dashboard
- **Multi-Panel Interface** — Network map, target tree, AI logs, timeline
- **Live Terminal Streams** — Real-time tool output
- **System Monitoring** — CPU, memory, interface status
- **AI Decision Logs** — Transparent reasoning display
- **WebSocket Updates** — Instant event propagation

### 🔧 Tool Management
- **Auto-Detection** — Identify installed tools automatically
- **Auto-Installation** — Install 20+ external tools with one command
- **AI-Enhanced Parsing** — Tool output analysis by AI
- **Cross-Platform** — Linux, macOS, Windows support

### 🤖 Machine Learning
- **Device Fingerprinting** — Identify devices from traffic patterns
- **Success Prediction** — Estimate attack success probability
- **Anomaly Detection** — Detect suspicious network behavior
- **Timing Prediction** — Optimize attack timing

---

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- Wireless adapter with monitor mode (Linux) or Npcap (Windows)
- At least one LLM API key

### Quick Install (Linux)

```bash
# Clone repository
git clone https://github.com/bhisma-team/bhisma.git
cd bhisma

# Install system dependencies
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git gcc make libssl-dev libffi-dev

# Create virtual environment
python3 -m venv ~/.bhisma/venv
source ~/.bhisma/venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Bhisma
pip install -e .

# Run setup
bhisma setup --install-python
```

### Quick Install (macOS)

```bash
git clone https://github.com/bhisma-team/bhisma.git
cd bhisma
brew install python3 pip
python3 -m venv ~/.bhisma/venv
source ~/.bhisma/venv/bin/activate
pip install -r requirements.txt
pip install -e .
bhisma setup --install-python
```

### Quick Install (Windows)

```bash
git clone https://github.com/bhisma-team/bhisma.git
cd bhisma
# Install Python 3.8+ from python.org
# Install Npcap from https://npcap.com (WinPcap compatible mode)
python -m venv C:\Users\%USERNAME%\.bhisma\venv
C:\Users\%USERNAME%\.bhisma\venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
bhisma setup --install-python
```

### Detailed Installation

See [Installation Guide](docs/02-installation.md) for detailed instructions, troubleshooting, and system-specific setup.

---

## 🚀 Quick Start

### 1. Configure API Keys

```bash
bhisma setup
```

Follow the TUI to add at least one LLM API key:
- **NVIDIA** — [build.nvidia.com](https://build.nvidia.com)
- **Groq** — [console.groq.com](https://console.groq.com)
- **Claude** — [console.anthropic.com](https://console.anthropic.com)
- **HuggingFace** — [huggingface.co](https://huggingface.co)
- **OpenRouter** — [openrouter.ai](https://openrouter.ai)
- **Gemini** — [makersuite.google.com](https://makersuite.google.com)

### 2. Autonomous Mode

```bash
# Enable monitor mode and run full autonomous attack
sudo airmon-ng start wlan0
bhisma auto --iface wlan0mon --band 2.4,5 --timeout 30
```

**What happens:**
1. Adapter detection and monitor mode verification
2. WiFi reconnaissance (passive + active scanning)
3. AI target selection based on vulnerability score
4. Attack chain execution (deauth → harvest → crack → mitm)
5. Real-time dashboard updates at `http://127.0.0.1:8080`
6. Automated report generation

### 3. Individual Attacks

```bash
# Reconnaissance
bhisma recon --iface wlan0mon --duration 60

# Deauthentication (silent pulse)
bhisma deauth --target AA:BB:CC:DD:EE:FF --iface wlan0mon --silent

# Handshake harvesting
bhisma harvest --target AA:BB:CC:DD:EE:FF --iface wlan0mon --duration 120

# WPS Pixie Dust
bhisma wps --target AA:BB:CC:DD:EE:FF --iface wlan0mon --pixie

# Evil Twin with captive portal
bhisma evil-twin --target AA:BB:CC:DD:EE:FF --iface wlan0mon --portal
```

### 4. Web Dashboard

```bash
# Launch dashboard only
bhisma dashboard --port 8080
```

Open `http://127.0.0.1:8080` for:
- 🗺️ Network Map with target visualization
- 🌳 Target Tree with vulnerability scores
- 🧠 AI Brain Log with real-time decisions
- 📈 Attack Timeline with phase-by-phase progress
- 💻 Terminal Panels with live tool output
- ⚙️ System Status (CPU, memory, interface, AI providers)

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Overview](docs/01-overview.md) | Features, architecture, comparison with other tools |
| [Installation](docs/02-installation.md) | Detailed installation guide for all platforms |
| [Usage](docs/03-usage.md) | Complete CLI command reference and examples |
| [Architecture](docs/04-architecture.md) | System architecture, module details, data flow |

---

## 🎯 CLI Commands

### Core Commands
```bash
bhisma setup              # First-time setup
bhisma keys --add         # Add API keys
bhisma keys --test        # Test provider connections
bhisma auto --iface wlan0 # Fully autonomous mode
bhisma dashboard          # Launch web dashboard
```

### Reconnaissance
```bash
bhisma recon --iface wlan0 --duration 60           # Passive scan
bhisma recon --iface wlan0 --active --bands 2.4,5   # Active scan
bhisma recon --list-adapters                       # List adapters
```

### Attacks
```bash
bhisma deauth --target AA:BB:CC:DD:EE:FF --iface wlan0 --silent
bhisma harvest --target AA:BB:CC:DD:EE:FF --iface wlan0
bhisma evil-twin --target AA:BB:CC:DD:EE:FF --iface wlan0 --karma
bhisma wps --target AA:BB:CC:DD:EE:FF --iface wlan0 --pixie
bhisma wep --target AA:BB:CC:DD:EE:FF --iface wlan0
```

### Tools & System
```bash
bhisma tools check         # Check installed tools
bhisma tools install       # Auto-install missing tools
bhisma daemon start        # Start background daemon
bhisma report --format markdown --output report.md
```

---

## 🗡️ Attack Matrix

### Reconnaissance
- ✅ Passive/Active Scanning
- ✅ Hidden SSID Discovery
- ✅ MAC Fingerprinting
- ✅ Traffic Analysis
- ✅ Client Device Profiling
- ✅ Vulnerability Scoring

### Authentication Attacks
- ✅ **WEP** — FMS, KoreK chopchop, PTW, ARP replay
- ✅ **WPA2** — 4-way handshake, PMKID, KRACK
- ✅ **WPA3** — Dragonblood, SAE downgrade, reflection
- ✅ **WPS** — Pixie Dust, brute-force, NULL PIN, bully

### Deauthentication
- ✅ Silent Pulse (AI-predictive timing)
- ✅ Directed Deauth
- ✅ Disassociation Flood
- ✅ Fake Deauth with MAC spoofing

### Rogue AP
- ✅ Basic Evil Twin
- ✅ KARMA Attack
- ✅ MANA Attack
- ✅ Captive Portal Phishing
- ✅ RADIUS Impersonation
- ✅ Behavioral Mimicry

### MITM
- 📝 ARP Spoofing
- 📝 DNS Hijacking
- 📝 Rogue DHCP
- 📝 SSL Stripping
- 📝 Session Hijacking
- 📝 SOCKS Proxy Pivot

### Frame Injection
- 📝 Beacon Flood
- 📝 Auth/Assoc Flood
- 📝 RTS/CTS Flood
- 📝 Probe Response Flood
- 📝 QoS Exploitation
- 📝 FragAttacks

### Modern Protocols
- ✅ WiFi 6/6E — BSS collision, OFDMA manipulation
- ✅ Mesh Networks — Peering spoof, gateway impersonation
- 📝 Bluetooth Reconnaissance
- 📝 Zigbee Sniffing
- 📝 RFID Reading

**Legend:** ✅ Fully Implemented | 📝 Stub/Placeholder

---

## 🏗️ Architecture

```
bhisma/
├── cli/              # Click-based CLI interface
├── tui/              # Single TUI (API key manager)
├── brain/            # Multi-LLM AI orchestrator
│   ├── providers/    # 6 LLM backends (NVIDIA, Groq, Claude, HF, OpenRouter, Gemini)
│   ├── agents/       # Strategist, Analyzer, Decider, Researcher, Reporter, Coder
│   ├── orchestrator.py  # Multi-provider fallback & consensus
│   ├── uncensor.py   # Prompt injection for uncensored mode
│   └── memory.py     # Conversation memory management
├── core/             # Framework orchestration
│   ├── engine.py     # Main attack orchestrator
│   ├── state_machine.py  # Attack lifecycle FSM
│   ├── fingerprint.py    # Behavioral fingerprinting
│   ├── mimicry.py        # Traffic mimicry engine
│   └── autonomous/       # Daemon, scheduler, rules, orchestrator
├── wifi/             # WiFi attack modules
│   ├── recon.py      # Reconnaissance
│   ├── deauth.py     # Deauthentication
│   ├── harvester.py  # Handshake/PMKID harvesting
│   ├── evil_twin.py  # Rogue AP attacks
│   ├── wps.py        # WPS attacks
│   ├── wep.py        # WEP cracking
│   ├── wpa2.py       # WPA2 attacks
│   ├── wpa3.py       # WPA3 attacks
│   ├── wifi6.py      # WiFi 6 exploitation
│   ├── mesh.py       # Mesh network attacks
│   └── channel_sync.py  # Channel synchronization
├── mitm/             # MITM attack modules
├── injection/        # Frame injection modules
├── persistence/      # Post-exploitation modules
├── radio/            # Non-WiFi radio protocols
├── intel/            # Intelligence gathering
├── ml/               # Machine learning engine
├── stealth/          # Evasion & detection avoidance
├── tools/            # External tool management
│   ├── registry.py   # Tool metadata registry
│   ├── manager.py    # Auto-detect & install
│   └── binder.py     # Tool execution with AI analysis
├── dashboard/        # Web dashboard
│   ├── server.py     # FastAPI server
│   ├── websocket.py  # WebSocket manager
│   └── templates/   # Dashboard UI
└── utils/            # Utility functions
    ├── constants.py  # Global constants
    ├── platform.py   # Platform detection
    ├── helpers.py    # Helper functions
    └── deps.py       # Dependency management
```

See [Architecture Documentation](docs/04-architecture.md) for detailed module descriptions and data flow.

---

## 🤖 AI Providers

Bhisma supports 6 LLM providers with automatic fallback:

| Provider | Model | Strength | Status |
|----------|-------|---------|--------|
| NVIDIA | Llama 3.1, Mixtral | Fast, open models | ✅ |
| Groq | Llama 3.1, Mixtral | Ultra-fast inference | ✅ |
| Claude | Claude 3.5 Sonnet | Best reasoning | ✅ |
| HuggingFace | Custom models | Full control | ✅ |
| OpenRouter | 100+ models | Variety | ✅ |
| Gemini | Gemini 1.5 Pro | Multimodal | ✅ |

### Uncensored Mode

All providers support uncensored mode via prompt injection:
- System prompt overrides
- Provider-specific bypass techniques
- Roleplay framing
- DAN-style jailbreaks

**Note:** Use responsibly and only for authorized security testing.

---

## 📊 Comparison

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
| MITM Suite | 📝 Stubs | ❌ | ❌ | ✅ |
| Frame Injection | 📝 Stubs | ✅ | ❌ | ✅ |

---

## 🛡️ Security & Safety

### Legal Disclaimer

**Bhisma is designed for authorized security testing only.** Unauthorized use is illegal. Always obtain explicit written permission before testing any network. The authors are not responsible for misuse.

### Safety Features

- **Whitelist/Blacklist** — Prevent attacks on protected networks
- **Target Validation** — Verify target before engagement
- **Autonomous Safeguards** — Time limits and phase validation
- **Encrypted Keys** — AES-256 encrypted API key storage

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📝 License

MIT License — See [LICENSE](LICENSE) for details.

**For authorized security testing and educational purposes only.**

---

## 🙏 Acknowledgments

- **aircrack-ng** — WiFi security auditing
- **Scapy** — Packet manipulation
- **FastAPI** — Modern web framework
- **Rich** — Terminal formatting
- All LLM providers for their APIs

---

## 📞 Support

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/bhisma-team/bhisma/issues)
- 💬 [Discussions](https://github.com/bhisma-team/bhisma/discussions)

---

<div align="center">

**⭐ Star this repo if you find it useful!**

Made with ❤️ by the Bhisma Team

</div>
