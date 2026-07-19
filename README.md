# 💜 Khushi AI — Autonomous Desktop Companion

<div align="center">
  
  ```
   _  ___               _     _      _   ___ 
  | |/ / |__  _   _ ___| |__ (_)    / \ |_ _|
  | ' /| '_ \| | | / __| '_ \| |   / _ \ | | 
  | . \| | | | |_| \__ \ | | | |  / ___ \| | 
  |_|\_\_| |_|\__,_|___/_| |_|_| /_/   \_\___|
  ```
  
  *Your Offline-First, Privacy-Preserving Intelligent Desktop Orchestrator & Autonomous Assistant*
  
  [![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
  [![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
  [![Framework: PySide6](https://img.shields.io/badge/UI-PySide6-darkgreen.svg)](https://pyside.org)
  [![Build Target: Windows](https://img.shields.io/badge/OS-Windows%2010%20%2F%2011-blue.svg)](https://microsoft.com/windows)
  [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-violet.svg)](CONTRIBUTING.md)

</div>

---

## 📖 Introduction & Why This Project Exists

Most modern virtual assistants and AI companions depend entirely on cloud APIs, transmitting your keystrokes, voice recordings, and personal data to remote servers. This introduces latency, breaks when offline, and compromises privacy.

**Khushi AI** is designed to solve this. It is a desktop assistant that runs locally on your machine, leveraging offline-first components (like local Speech-to-Text and native Windows Text-to-Speech) alongside system-level control layers. It functions as an intelligent interface between you and your operating system—automating workflows, executing tasks, and preserving memory without exposing your personal information to the internet.

---

## 🚀 Core Features

- 🗣️ **Intelligent Voice Routing**: High-fidelity local voice recording (`voice/listener.py`) coupled with a fast SAPI5/eSpeak TTS wrapper (`voice/speaker.py`).
- 🧠 **Dynamic Intent Matching**: Intent-based keyword parsing and regex matching that maps user commands to target modules.
- ⚙️ **OS & UI Automation**: Safe simulation of mouse movements (`automation/mouse.py`), key presses (`automation/keyboard.py`), clipboard manipulation, and active window management.
- 📁 **System Skill Integrations**: Launching programs, mathematical operations, local notes tracking, and recursive file scanning in desktop environments.
- 🔌 **Sandboxed Plugin SDK**: Run third-party extensions in isolated runtime threads (`plugins/sandbox.py`) with permissions checks.
- 📈 **Performance Dashboard**: Real-time system resource tracking (CPU, RAM, Battery) with interactive charting inside the PySide6 application.
- 🔒 **Encrypted Memory Backup**: AES-256 (Fernet) backup utility to secure logs, profile settings, and notes using PBKDF2 cryptography.
- 🚗 **OBD-II Vehicle Telemetry**: Native scanner support for ELM327 Bluetooth/USB adapters to read real-time engine codes, speed, load, and coolant metrics.

---

## 🛠️ System Requirements & Setup

- **Operating System**: Windows 10 or 11 (due to `comtypes` and `pywin32` dependencies).
- **Python**: version 3.10 to 3.12.
- **PortAudio**: Ensure your computer has audio inputs and outputs active.

---

## 📦 Installation

Initialize your developer environment using our bootstrap script or perform it manually:

### Automatic Bootstrap (PowerShell)
```powershell
.\scripts\bootstrap.ps1
```

### Manual Installation
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/meerf5219-web/Khushi-AI.git
   cd Khushi-AI
   ```
2. **Create & Activate Virtual Environment**:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. **Install Requirements**:
   ```powershell
   pip install -r requirements.txt
   ```

---

## 🚦 Quick Start

To launch the desktop interface:
```powershell
python main.py
```

### Debug & Diagnostic Logs
To run the assistant with real-time timeline logging and debug consoles:
```powershell
python main.py --debug
```

---

## 📁 Repository Directory Structure

```
Khushi-AI/
├── .github/                   # GitHub Issue/PR Templates & Metadata
├── AI/                        # Machine learning model adapters
├── agents/                    # Collaborative agent logic & patterns
├── api/                       # Local FastAPI web server endpoints & routes
├── app/                       # Program launch orchestrators
├── assets/                    # Graphic files, visual specs & layout spec sheets
│   └── visuals.md
├── automation/                # Emulation helpers (Keyboard, mouse, window active)
├── brain/                     # Cognitive intent-matching & request pipelines
├── companion/                 # Personality management & dialogue systems
├── docs/                      # Extensive specifications & API guides
│   ├── ARCHITECTURE.md        # Technical architecture specifications
│   ├── api_documentation.md   # API endpoint documentation
│   ├── developer_guide.md     # Code guidelines and testing
│   ├── TODO_PHASE2A.md        # Startup diagnostics work list
│   └── user_guide.md          # User manual and mobile pairing instructions
├── examples/                  # Standard implementation code blocks
├── memory/                    # SQLite, WorldModel, and JSON profile sync
├── planner/                   # Strategy templates & action scheduling
├── plugins/                   # Safe custom extension loader SDK
├── providers/                 # API client integrations
├── scripts/                   # Developer bootstrap helper files
├── skills/                    # Functional intent skills (calc, screenshot, weather)
├── tests/                     # Standard unit/integration pytest files
├── ui/                        # PySide6 components, stylesheet styling, widgets
├── utils/                     # System profiling, recovery, & updater files
├── vision/                    # Screen scanners and EasyOCR adapters
└── voice/                     # Audio interfaces (speaker, listener)
```

For a detailed walkthrough of each directory and system module, refer to the [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) guide.

---

## ⚙️ Configuration & Environment Variables

Settings are configured via the in-app **Settings panel** (`ui/widgets/settings.py`) or manually via configuration files under `memory/user_memory.json`.

| Parameter | Type | Default | Description |
| --------- | ---- | ------- | ----------- |
| `theme` | String | `"dark"` | Application window styling (`dark`, `purple`). |
| `tts_rate` | Integer | `150` | Words-per-minute speed of SAPI5 speech synthesis. |
| `api_port` | Integer | `8000` | Local port binding for Uvicorn REST API server. |
| `paired_clients` | List | `[]` | List of paired mobile client fingerprints. |

---

## 🖼️ Application Interfaces (Screenshots)

Refer to [assets/visuals.md](assets/visuals.md) for detailed descriptions, component breakdowns, and path references for our key user interfaces:
- **Application Home**: Central dashboard metrics and system resources.
- **Chat Window**: Multi-bubble dialog container with waveform animations.
- **Voice Assistant**: Standby mode overlays with frequency charts.
- **Settings**: System configurations, OBD-II toggles, and client keys.
- **Terminal View**: Real-time thread diagnostics and recovery checkpoints.

---

## 🏗️ System Architecture

Khushi AI uses an event-driven, decoupled system architecture:
- **Intent Router**: Passes parsed input strings directly to the registered skill managers.
- **Pub/Sub Bus**: A thread-safe EventBus singleton coordinates cognitive nodes.
- **AES-256 Storage**: Flat-file JSON buffers sync memory to disk, backed up on command.

Read the full architecture spec at **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**.

---

## 🗺️ Project Roadmap

- **v1.0.x (Current stable)**: Core PySide6 dashboard, diagnostics timeline, and standard open-source documentation package.
- **v1.1.x (Automation)**: Enhanced OCR visual overlays, isolated dynamic plugin installers.
- **v1.2.x (Mobile Pairing)**: Encrypted LAN WebSocket streams with paired React Native clients.
- **v2.0.x (Cognitive Core)**: Local LLM integration (llama.cpp) for total offline chat processing.

See details in **[ROADMAP.md](ROADMAP.md)**.

---

## ❓ FAQ & Troubleshooting

### Q: Why does the app fail to start on `pyaudio`?
**A**: Ensure PortAudio is installed on your OS. For Windows, pip wheels usually package it, but you may need to grant microphonic access in Windows Settings under Privacy -> Microphone.

### Q: How do I resolve startup crash loops?
**A**: Run the recovery tool check to clean corrupted memory files:
```powershell
python -c "from utils.recovery import CrashRecoverySystem; CrashRecoverySystem().run_health_check_and_repair()"
```

### Q: How can I access the API from my local network?
**A**: Toggle "Allow LAN access" in Settings, which binds the FastAPI server to `0.0.0.0`. Use the autogenerated Pairing Link to pair mobile clients.

---

## 🤝 Contributing

Contributions are what make the open-source community an amazing place to learn and build. Read our **[CONTRIBUTING.md](CONTRIBUTING.md)** guidelines to get started.

---

## 🔒 Security

We prioritize user security and data privacy. To report vulnerabilities, refer to **[SECURITY.md](SECURITY.md)**.

---

## 👥 Credits & Contact

- **Lead Developer**: Faisal
- **Contributors**: The Khushi AI Open Source Contributors
- **Inspirations**: Contributor Covenant, Contributor guidelines, and Python PySide6 projects.

---

## 📜 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more details.
