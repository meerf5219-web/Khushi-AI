# 💜 Khushi AI — Autonomous Desktop Companion

[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![Framework: PySide6](https://img.shields.io/badge/UI-PySide6-darkgreen.svg)](https://pyside.org)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-violet.svg)](CONTRIBUTING.md)

Khushi AI is a professional, modular, voice-activated desktop assistant and autonomous companion built on PySide6 and Python. Designed to run locally on your system, Khushi acts as an intelligent layer between you and your machine, integrating persistent memory, custom skills, voice interaction, and desktop automation into a seamless experience.

---

## 🚀 Key Features

- 🗣️ **Natural Voice Interaction**: High-fidelity speech recognition and custom Text-to-Speech (TTS) engine, with automatic fallback systems.
- 🧠 **Persistent Memory System**: A sophisticated multi-tier memory system utilizing SQLite (`raw_events.db`), user profiles (`user_memory.json`), and a conceptual `world_model.json`.
- ⚙️ **Modular Skills Engine**: Dynamic intent routing for seamless activation of plugins and custom capabilities.
- 🖥️ **Desktop Automation**: System-level controls for volume, screen brightness, clipboard management, screenshots, keyboard emulation, and mouse control.
- 🔍 **File Search & Retrieval**: Instantly searches common user folders (Desktop, Documents, Downloads, etc.) for requested files.
- 🌤️ **Weather & Calculator Tools**: Extensible weather API client with provider abstraction and a robust algebraic/percentage calculator engine.
- 👁️ **Computer Vision & OCR**: Active screen capture, overlay drawing, and high-performance Optical Character Recognition (OCR) powered by OpenCV and EasyOCR.
- 🔌 **Dynamic Plugin System**: Sandboxed execution runtime allowing developers to write third-party modules safely.

---

## 📁 System Architecture & Directory Structure

Here is a conceptual overview of how Khushi AI is organized:

```
project k/
├── .github/                   # GitHub community configuration, templates & metadata
├── AI/                        # Core AI intelligence and model orchestration
├── agents/                    # Multi-agent collaboration frameworks
├── api/                       # Local FastAPI web server routes and runners
├── app/                       # Startup orchestrators and system initializers
├── assets/                    # Graphical resources, icons, and theme assets
├── automation/                # Mouse, keyboard, and OS interface controllers
├── brain/                     # Intent router, event bus, decision engine, context pipeline
├── companion/                 # Social/emotional behavior & personality management
├── config/                    # Global app configuration and JSON files
├── dashboard/                 # System statistics tracking and reporting
├── database/                  # SQLite storage targets
├── devices/                   # External device bridges (e.g., OBD integrations)
├── memory/                    # Persistent storage managers, world model, user profiles
├── planner/                   # Task scheduling and execution strategies
├── plugins/                   # Developer sandbox and third-party SDK
├── providers/                 # API integrations (e.g., weather providers)
├── skills/                    # Python-based intent executors (e.g., calculator, weather, notes)
├── tests/                     # Comprehensive PyTest test suite
├── ui/                        # PySide6 desktop views, custom widgets, styling, and splash screen
├── utils/                     # Resource management, recovery, and logging utilities
├── vision/                    # OCR engines, camera control, capture tools, and screen overlays
└── voice/                     # Audio capture (mic listeners) and voice synthesis (speakers)
```

---

## 🛠️ Requirements & System Dependencies

Before installing, ensure your development machine meets the following criteria:

- **Operating System**: Windows (tested on Windows 10/11)
- **Python**: version 3.10 to 3.12 (standard packages depend on Windows APIs)
- **PortAudio**: Needed for speech recognition and microphone streams (`pyaudio`).

---

## 📦 Installation

To get a local copy of Khushi AI up and running, follow these steps:

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/khushi-ai.git
cd khushi-ai
```

### 2. Set Up a Virtual Environment
We recommend using Python's built-in virtual environment (`venv`):
```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Python Dependencies
Install the required packages listed in `requirements.txt`:
```powershell
pip install -r requirements.txt
```

---

## 🚦 Quick Start

To launch the desktop interface:

```powershell
python main.py
```

### 🛠️ Debug Mode
To run the assistant with detailed logging enabled and startup diagnostics:
```powershell
python main.py --debug
```

During startup, Khushi will:
1. Verify system resources and database health.
2. Initialize PySide6 and display a splash loading screen.
3. Warm up the speech synthesis engine.
4. Welcome you back and stand ready to assist.

---

## 📸 Screenshots & Interface Visuals

*Below is a placeholder indicating where user-interface screenshots reside:*

```
[ Splash Loading Screen ] ──> [ Main Assistant Workspace ] ──> [ Active Automation Overlay ]
       (ui/splash.py)                 (ui/main_window.py)                (ui/widgets/)
```
All runtime screenshots taken by the assistant are saved in the `screenshots/` directory.

---

## 🗺️ Development Roadmap

- [x] **Phase 1: Foundation**: Basic desktop GUI, PySide6 wrappers, local SQLite databases.
- [x] **Phase 2: Intent-based Core**: Dynamic voice recognition and skill managers.
- [x] **Phase 2A (Current)**: Diagnostic framework implementation (Timeline logging, recovery checkpoints, system health reporting).
- [ ] **Phase 3: Deep Vision integration**: Real-time object recognition and screen overlay interaction.
- [ ] **Phase 4: cloud-synchronized model sync**: Enable remote companion control via mobile endpoints.

---

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

Please refer to the [CONTRIBUTING.md](CONTRIBUTING.md) file for setup steps, testing workflows, and branching strategies.

---

## 📜 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

---

## ❓ FAQ

#### Q: Which voice engine does Khushi use?
A: Khushi defaults to the Windows native TTS engine (via `pyttsx3`) for speed and reliability, but falls back to a python-native helper stream in case of device configuration issues.

#### Q: Where are my notes and conversation logs stored?
A: All notes are stored in `memory/notes.json` and system profiles are kept in `memory/user_memory.json` locally on your system.

#### Q: How can I write custom skills?
A: You can easily add a python file in the `skills/` folder implementing the standard skill interface and register it via `skills/skill_manager.py`.

#### Q: Does it require an internet connection?
A: Core tasks like calculating, clipboard control, screenshots, and local file searches are completely offline. Network queries like web searching and weather reports require an active internet connection.
