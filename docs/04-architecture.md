# Architecture

## System Architecture

Bhisma follows a modular, layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ CLI (Click)  │  │ TUI (Rich)   │  │ Web Dashboard    │  │
│  │ commands.py  │  │ key_manager  │  │ FastAPI + WS     │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                      Core Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Engine       │  │ State Machine│  │ Config           │  │
│  │ engine.py    │  │ state_machine│  │ config.py        │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Fingerprint  │  │ Mimicry      │  │ Autonomous       │  │
│  │ fingerprint  │  │ mimicry      │  │ daemon/scheduler │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                      AI Brain                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Orchestrator │  │ Uncensor     │  │ Memory           │  │
│  │ orchestrator │  │ uncensor     │  │ memory           │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Provider     │  │ Agents       │  │ Fallback Chain   │  │
│  │ base + 6     │  │ 6 agents     │  │ NVIDIA→Groq→...  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   Attack Modules                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ WiFi         │  │ MITM         │  │ Injection        │  │
│  │ recon/deauth │  │ arp/dns/ssl  │  │ beacon/auth/frag │  │
│  │ harvest/evil │  │ dhcp/session │  │ rtscts/probe     │  │
│  │ wps/wep/wpa  │  │ socks        │  │ qos              │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Persistence  │  │ Radio        │  │ Intel            │  │
│  │ rogue/dhcp   │  │ bluetooth    │  │ predictor/scorer │  │
│  │ dns/captive  │  │ zigbee/rfid  │  │ topology/cloud   │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  Support Modules                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Platform     │  │ Tools        │  │ Stealth          │  │
│  │ platform     │  │ registry/    │  │ evasion/honeypot │  │
│  │ detection    │  │ manager/     │  │ mac/rf           │  │
│  │ monitor mode │  │ binder       │  │                  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ ML Engine    │  │ Utils        │  │ Constants        │  │
│  │ fingerprint  │  │ helpers      │  │ constants        │  │
│  │ predict/det  │  │ deps         │  │                  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Module Details

### CLI Layer (`cli/`)

**Purpose:** User-facing command interface

**Components:**
- `main.py` — Click group and entry point
- `commands.py` — All subcommands (auto, recon, deauth, etc.)

**Key Commands:**
- `bhisma auto` — Autonomous mode
- `bhisma recon` — WiFi reconnaissance
- `bhisma deauth` — Deauthentication attacks
- `bhisma harvest` — Handshake/PMKID harvesting
- `bhisma evil-twin` — Rogue AP attacks
- `bhisma wps` — WPS attacks
- `bhisma keys` — API key management
- `bhisma tools` — Tool management
- `bhisma dashboard` — Web dashboard

### TUI Layer (`tui/`)

**Purpose:** Terminal-based UI for configuration

**Components:**
- `key_manager.py` — Encrypted API key storage and management

**Features:**
- Add/update/remove API keys
- Test provider connections
- List configured providers
- Encrypted storage (AES-256)

### Core Layer (`core/`)

**Purpose:** Framework orchestration and state management

**Components:**

#### `engine.py` — Main Orchestrator
- Manages attack sessions
- Executes attack phases
- Coordinates AI recommendations
- Integrates all attack modules

#### `state_machine.py` — Attack Lifecycle
- Defined phases: `IDLE` → `RECON` → `SELECT` → `ATTACK` → `POST` → `REPORT`
- State transitions with validation
- Event-driven state changes

#### `config.py` — Configuration Management
- YAML-based configuration
- Default values
- Runtime updates

#### `fingerprint.py` — Behavioral Fingerprinting
- Analyzes beacon/data frames
- Computes timing statistics
- Detects honeypot anomalies

#### `mimicry.py` — Traffic Mimicry
- Generates timing parameters
- Morphs attack traffic
- Matches target profiles

#### `autonomous/` — Autonomous Mode
- `daemon.py` — Background process controller
- `scheduler.py` — Time-aware attack scheduling
- `rules.py` — YAML-based rule engine
- `target_queue.py` — Priority target queue
- `safety_gate.py` — Whitelist/blacklist gate
- `orchestrator.py` — Autonomous attack chain executor

### AI Brain (`brain/`)

**Purpose:** Multi-LLM orchestration with uncensored mode

**Components:**

#### `orchestrator.py` — Multi-LLM Orchestrator
- Provider fallback chain
- Consensus mode (2+ LLMs)
- Memory management
- Uncensor wrapper integration

#### `uncensor.py` — Prompt Injection
- System prompt overrides
- Provider-specific bypasses
- Roleplay framing
- DAN-style jailbreaks

#### `memory.py` — Conversation Memory
- Turn-by-turn storage
- Context window management
- History formatting

#### `providers/` — LLM Provider Implementations
- `base.py` — Abstract base class
- `nvidia.py` — NVIDIA API
- `groq.py` — Groq API
- `claude.py` — Anthropic Claude
- `huggingface.py` — HuggingFace Inference
- `openrouter.py` — OpenRouter API
- `gemini.py` — Google Gemini

#### `agents/` — AI Agents
- `strategist.py` — Attack strategy generation
- `analyzer.py` — Tool output analysis
- `decider.py` — Real-time decision making
- `researcher.py` — Vulnerability research
- `reporter.py` — Report generation
- `coder.py` — Code generation

### WiFi Modules (`wifi/`)

**Purpose:** WiFi-specific attack implementations

**Components:**
- `recon.py` — Reconnaissance (passive/active scanning)
- `deauth.py` — Deauthentication attacks
- `harvester.py` — Handshake/PMKID harvesting
- `evil_twin.py` — Rogue AP attacks
- `wps.py` — WPS attacks
- `wep.py` — WEP cracking
- `wpa2.py` — WPA2 attacks
- `wpa3.py` — WPA3 attacks
- `wifi6.py` — WiFi 6 exploitation
- `mesh.py` — Mesh network attacks
- `channel_sync.py` — Channel synchronization

### MITM Modules (`mitm/`)

**Purpose:** Man-in-the-middle attacks

**Components:**
- `arp.py` — ARP spoofing
- `dns.py` — DNS hijacking
- `dhcp.py` — DHCP exhaustion/rogue
- `ssl_strip.py` — SSL stripping
- `traffic_intercept.py` — Traffic interception
- `session_hijack.py` — Session hijacking
- `socks_proxy.py` — SOCKS proxy pivot

### Injection Modules (`injection/`)

**Purpose:** Frame injection attacks

**Components:**
- `beacon_flood.py` — Beacon flood
- `auth_flood.py` — Authentication flood
- `rts_cts_flood.py` — RTS/CTS flood
- `probe_flood.py` — Probe response flood
- `qos_exploit.py` — QoS exploitation
- `fragattack.py` — FragAttacks

### Persistence Modules (`persistence/`)

**Purpose:** Post-exploitation persistence

**Components:**
- `rogue_ap.py` — Rogue AP manager
- `rogue_dhcp.py` — Rogue DHCP server
- `dns_hijack.py` — DNS hijacker
- `captive_portal.py` — Captive portal
- `radius_fake.py` — Fake RADIUS server

### Radio Modules (`radio/`)

**Purpose:** Non-WiFi radio protocols

**Components:**
- `bluetooth.py` — Bluetooth reconnaissance
- `zigbee.py` — Zigbee sniffing
- `rfid.py` — RFID reading

### Intel Modules (`intel/`)

**Purpose:** Intelligence gathering

**Components:**
- `predictor.py` — Client behavior prediction
- `scorer.py` — AP vulnerability scoring
- `topology.py` — Network topology mapping
- `cloud.py` — Cloud intelligence

### ML Modules (`ml/`)

**Purpose:** Machine learning features

**Components:**
- `device_fingerprint.py` — Device fingerprinting
- `success_predictor.py` — Attack success prediction
- `anomaly_detector.py` — Anomaly detection
- `timing_predictor.py` — Timing prediction
- `auto_trainer.py` — Model auto-training

### Stealth Modules (`stealth/`)

**Purpose:** Evasion and detection avoidance

**Components:**
- `evasion.py` — IDS evasion techniques
- `honeypot_detect.py` — Honeypot detection
- `mac_manager.py` — MAC rotation
- `rf_randomizer.py` — RF signature randomization

### Tools (`tools/`)

**Purpose:** External tool management

**Components:**
- `registry.py` — Tool metadata registry
- `manager.py` — Auto-detect and install
- `binder.py` — Tool execution with AI analysis

### Dashboard (`dashboard/`)

**Purpose:** Web-based monitoring interface

**Components:**
- `server.py` — FastAPI server
- `websocket.py` — WebSocket manager
- `templates/index.html` — Dashboard UI

### Utils (`utils/`)

**Purpose:** Utility functions

**Components:**
- `constants.py` — Global constants
- `platform.py` — Platform detection
- `helpers.py` — Helper functions
- `deps.py` — Dependency management

## Data Flow

### Autonomous Attack Flow

```
User Command (CLI)
    ↓
BhismaEngine.init_session()
    ↓
ReconManager.scan_networks()
    ↓
TargetQueue.add_targets()
    ↓
Strategist Agent.query() → AI Plan
    ↓
Decider Agent.query() → Next Phase
    ↓
Engine.execute_phase()
    ↓
[Phase-specific module]
    ↓
ToolBinder.execute() → External Tool
    ↓
Analyzer Agent.query() → Tool Output Analysis
    ↓
Dashboard WebSocket Broadcast
    ↓
Next Phase Decision
    ↓
[Repeat until success or failure]
    ↓
Reporter Agent.query() → Final Report
```

### AI Query Flow

```
User/Module Request
    ↓
LLMOrchestrator.query()
    ↓
UncensorWrapper.wrap()
    ├── System Override
    ├── Provider-specific Bypass
    └── Compliance Suffix
    ↓
Memory.get_formatted_history()
    ↓
Provider.chat()
    ├── NVIDIA (primary)
    ├── Groq (fallback 1)
    ├── Claude (fallback 2)
    └── ...
    ↓
AIResponse
    ├── Text
    ├── Provider
    ├── Model
    └── Consensus (if enabled)
    ↓
Memory.add_turn()
    ↓
Dashboard Broadcast
```

### Dashboard WebSocket Flow

```
Module Event
    ↓
DashboardWebsocket.broadcast()
    ├── Type (target, ai_log, timeline, tool_output)
    └── Data
    ↓
WebSocket Server
    ↓
Browser Client
    ├── handleMessage()
    ├── Update UI
    └── Render
```

## Configuration

### Config Structure (`config.yaml`)

```yaml
ai:
  enable_ai_brain: true
  primary_provider: groq
  fallback_chain: [nvidia, groq, claude, huggingface, openrouter, gemini]
  uncensor_mode: true
  consensus_mode: false
  max_tokens: 2048
  temperature: 0.7

tools:
  auto_install: true
  check_on_start: true

wifi:
  default_interface: wlan0
  bands: ["2.4", "5"]
  dwell_time: 0.5
  silent_deauth_enabled: true
  channel_hop_enabled: true

mitm:
  enabled: false
  ssl_strip: false
  dns_hijack: false

dashboard:
  enabled: true
  port: 8080
  host: "127.0.0.1"
  auto_open: true

autonomous:
  enabled: false
  max_duration: 3600
  safety_enabled: true
  whitelist: []
  blacklist: []

stealth:
  mac_rotation: true
  rf_randomization: true
  timing_jitter: true
  honeypot_detection: true
```

## State Management

### Attack Session State

```python
{
    "session_id": str,
    "start_time": datetime,
    "end_time": Optional[datetime],
    "current_phase": str,
    "target": Dict[str, Any],
    "phases_completed": List[str],
    "phases_failed": List[str],
    "results": Dict[str, Any],
    "status": str,
}
```

### AI Memory State

```python
{
    "turns": List[Dict[str, str]],
    "max_turns": int,
    "context_window": int,
}
```

## Error Handling

### Provider Fallback Chain

```
Primary Provider (Groq)
    ↓ [Quota/Error]
Fallback 1 (NVIDIA)
    ↓ [Quota/Error]
Fallback 2 (Claude)
    ↓ [Quota/Error]
Fallback 3 (HuggingFace)
    ↓ [Quota/Error]
Fallback 4 (OpenRouter)
    ↓ [Quota/Error]
Fallback 5 (Gemini)
    ↓ [All Failed]
ProviderError Exception
```

### Tool Execution Fallback

```
Primary Tool (aircrack-ng)
    ↓ [Not Found/Failed]
Alternative Tool (hashcat)
    ↓ [Not Found/Failed]
AI Suggestion
    ↓ [Failed]
Manual Intervention Required
```

## Security Considerations

### API Key Storage
- Encrypted with AES-256
- Stored in `~/.bhisma/keys.enc`
- User-provided passphrase

### Network Safety
- Safety gate whitelist/blacklist
- Target validation
- Autonomous mode safeguards

### Dashboard Security
- Localhost binding by default
- No authentication (local use only)
- WebSocket message validation

---

**Next:** [API Reference](05-api-reference.md)
