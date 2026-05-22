# Installation Guide

## System Requirements

### Minimum Requirements
- **OS:** Linux (Kali/Ubuntu/Debian recommended), macOS, or Windows
- **Python:** 3.8 or higher
- **RAM:** 4GB minimum, 8GB recommended
- **Storage:** 2GB free space
- **Wireless Adapter:** Monitor mode capable (for Linux)

### Recommended for Full Functionality
- **OS:** Kali Linux 2023+ or Ubuntu 22.04+
- **Wireless Adapter:** Alfa AWUS036NHA, TP-Link TL-WN722N, or similar
- **RAM:** 16GB for ML features
- **GPU:** NVIDIA GPU (optional, for local ML models)

## Quick Install (Linux)

```bash
# Clone repository
git clone https://github.com/bhisma/bhisma.git
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

## Quick Install (macOS)

```bash
# Clone repository
git clone https://github.com/bhisma/bhisma.git
cd bhisma

# Install system dependencies
brew install python3 pip

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

## Quick Install (Windows)

```bash
# Clone repository
git clone https://github.com/bhisma/bhisma.git
cd bhisma

# Install Python 3.8+ from python.org
# Install Npcap from https://npcap.com (check "Install Npcap in WinPcap API-compatible Mode")

# Create virtual environment
python -m venv C:\Users\%USERNAME%\.bhisma\venv
C:\Users\%USERNAME%\.bhisma\venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install Bhisma
pip install -e .

# Run setup
bhisma setup --install-python
```

## Detailed Installation

### 1. System Dependencies

#### Linux (Debian/Ubuntu)
```bash
sudo apt update
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    gcc \
    make \
    libssl-dev \
    libffi-dev \
    aircrack-ng \
    iw \
    macchanger \
    hostapd \
    dnsmasq \
    bettercap \
    hashcat
```

#### Linux (RHEL/CentOS/Fedora)
```bash
sudo dnf install -y \
    python3 \
    python3-pip \
    git \
    gcc \
    make \
    openssl-devel \
    libffi-devel \
    aircrack-ng \
    iw \
    macchanger
```

#### macOS
```bash
brew install python3 pip aircrack-ng macchanger
```

#### Windows
- Install Python 3.8+ from [python.org](https://python.org)
- Install Npcap from [npcap.com](https://npcap.com) — **check "Install Npcap in WinPcap API-compatible Mode"**
- Install Git from [git-scm.com](https://git-scm.com)

### 2. Python Dependencies

Bhisma's `requirements.txt` includes:

```
click>=8.1.0          # CLI framework
rich>=13.0.0          # Terminal formatting
pydantic>=2.0.0       # Data validation
pyyaml>=6.0           # Config parsing
httpx>=0.24.0         # HTTP client
fastapi>=0.100.0      # Web framework
uvicorn>=0.23.0       # ASGI server
jinja2>=3.1.0         # Template engine
websockets>=11.0      # WebSocket support
questionary>=2.0.0    # TUI prompts
scikit-learn>=1.3.0   # ML library
numpy>=1.24.0         # Numerical computing
joblib>=1.3.0         # Parallel processing
scapy>=2.5.0          # Packet manipulation
psutil>=5.9.0         # System monitoring
```

Install with:
```bash
pip install -r requirements.txt
```

### 3. External Tools

Bhisma can auto-install most tools via `bhisma tools install`. However, manual installation is recommended for Linux:

```bash
# WiFi tools
sudo apt install -y aircrack-ng hcxtools reaver bully mdk4

# MITM tools
sudo apt install -y bettercap mitmproxy

# Cracking
sudo apt install -y hashcat john

# Network tools
sudo apt install -y hostapd dnsmasq freeradius tshark
```

### 4. Monitor Mode Setup

#### Linux
```bash
# Check wireless interfaces
iw dev

# Enable monitor mode (using airmon-ng)
sudo airmon-ng start wlan0

# Or manually
sudo ip link set wlan0 down
sudo iw dev wlan0 set type monitor
sudo ip link set wlan0 up
```

#### macOS
```bash
# macOS has limited monitor mode support
# Use airport utility for passive sniffing
sudo /System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -z
```

#### Windows
- Npcap handles monitor mode in userspace
- No manual setup required
- Ensure Npcap is installed with "WinPcap API-compatible Mode"

### 5. API Key Configuration

Bhisma requires at least one LLM API key for AI features:

```bash
# Run setup TUI
bhisma setup

# Or manage keys directly
bhisma keys --add
bhisma keys --list
bhisma keys --test
```

Supported providers:
- **NVIDIA** — [build.nvidia.com](https://build.nvidia.com)
- **Groq** — [console.groq.com](https://console.groq.com)
- **Claude (Anthropic)** — [console.anthropic.com](https://console.anthropic.com)
- **HuggingFace** — [huggingface.co](https://huggingface.co)
- **OpenRouter** — [openrouter.ai](https://openrouter.ai)
- **Gemini (Google)** — [makersuite.google.com](https://makersuite.google.com)

### 6. Verification

```bash
# Check installation
bhisma --version

# Check dependencies
bhisma tools check

# Test AI connection
bhisma keys --test

# Test adapter detection
bhisma recon --list-adapters
```

## Troubleshooting

### Python Permission Errors
```bash
# Use --user flag
pip install --user -r requirements.txt

# Or use virtual environment
python3 -m venv ~/.bhisma/venv
source ~/.bhisma/venv/bin/activate
pip install -r requirements.txt
```

### Missing System Packages
```bash
# Install via setup command
bhisma setup --install-system

# Or manually (Debian/Ubuntu)
sudo apt install -y python3 python3-pip python3-venv git gcc make libssl-dev libffi-dev
```

### Monitor Mode Issues (Linux)
```bash
# Kill interfering processes
sudo airmon-ng check kill

# Try alternative method
sudo ip link set wlan0 down
sudo iw dev wlan0 set type monitor
sudo ip link set wlan0 up
```

### Npcap Issues (Windows)
- Uninstall Npcap
- Reinstall with "WinPcap API-compatible Mode" checked
- Restart computer

### Import Errors
```bash
# Ensure in virtual environment
source ~/.bhisma/venv/bin/activate  # Linux/macOS
C:\Users\%USERNAME%\.bhisma\venv\Scripts\activate  # Windows

# Reinstall in development mode
pip install -e .
```

## Uninstallation

```bash
# Uninstall package
pip uninstall bhisma

# Remove virtual environment
rm -rf ~/.bhisma/venv

# Remove config and data
rm -rf ~/.bhisma
```

---

**Next:** [Usage Guide](03-usage.md)
