# Khushi AI — Architecture Specifications

This document outlines the core architecture, request routing pipelines, multi-tier storage engines, sandboxing models, and startup workflows of **Khushi AI**.

---

## 1. Complete Repository Folder Tree

The directory layout corresponds to a modular Python + PySide6 project:

```
project k/
├── .github/                     # GitHub communities templates
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── repository_metadata.json
├── AI/                          # Model orchestrators & semantic vectorizers
├── agents/                      # Collaborative agent patterns & routines
├── api/                         # FastAPI local web server framework
│   ├── auth.py                  # API key verify & rate limiting
│   ├── routes/                  # API endpoints (chat, vehicle diagnostics, backups)
│   └── server.py                # Uvicorn background runner wrapper
├── app/                         # App startup orchestration
├── assets/                      # Graphic templates and visual specs
│   └── visuals.md
├── automation/                  # System-level keyboard and mouse simulation
│   ├── keyboard.py
│   ├── mouse.py
│   └── window_manager.py
├── brain/                       # Cognitive orchestration layers
│   ├── brain.py                 # Core coordination pipeline
│   ├── context.py               # Input/Output execution state wrappers
│   ├── decision_engine.py       # Action routing and classification
│   ├── event_bus.py             # Pub/Sub singleton communications broker
│   ├── intent.py                # Regex & semantic keyword intent parser
│   └── startup.py               # Stage logger check and diagnostic logger
├── companion/                   # Social intelligence and personality engines
├── config/                      # Configuration managers
├── dashboard/                   # UI charts and PyQTGraph dashboard bindings
├── database/                    # SQLite database hooks
├── devices/                     # ELM327 OBD-II serial & bluetooth abstraction
├── docs/                        # Specifications and guides
│   ├── ARCHITECTURE.md          # Architecture specs (this file)
│   ├── api_documentation.md     # Client API integration details
│   ├── developer_guide.md       # Developer setups and guidelines
│   ├── TODO_PHASE2A.md          # Diagnostic phase log list
│   └── user_guide.md            # App user guides
├── examples/                    # Developer example scripts
├── memory/                      # Persistent storage managers
│   ├── manager.py               # JSON/SQLite synchronization wrapper
│   ├── notes.json               # Note persistent files
│   └── user_memory.json         # Profile states & preferences
├── planner/                     # Plan scheduling execution routines
├── plugins/                     # Extensible sandbox engine
│   ├── manager.py               # Safe plugin loading interfaces
│   ├── manifest.py              # Plugin permissions parser
│   └── sandbox.py               # Isolated runtime execute
├── providers/                   # External API wrappers (e.g. OpenWeather)
├── scripts/                     # Developer utility helpers
│   └── bootstrap.ps1
├── skills/                      # Executable intent skills
│   ├── app_skill.py             # System app launcher
│   ├── calculator_skill.py      # Equation parser
│   ├── skill_manager.py         # Registry hook for custom skills
│   └── weather_skill.py         # Weather api wrapper
├── tests/                       # Complete PyTest test suite
├── ui/                          # GUI components (views, themes, custom widgets)
│   ├── app.py                   # App QApplication startup lifecycle
│   ├── main_window.py           # Main Dashboard wrapper view
│   ├── splash.py                # Graphical startup splash loading window
│   └── theme.py                 # Theme loader
├── utils/                       # Diagnostics, profilers and update utilities
│   ├── recovery.py              # Crash recovery checks
│   └── resource_manager.py      # Disk/file permissions provisioner
├── vision/                      # Computer vision & OCR scanners
│   └── ocr.py                   # Screen optical character recognition
├── voice/                       # Speech Recognition & TTS Adaptors
└── voice_companion/             # Background voice companion service
```

---

## 2. Component Diagram

The following Mermaid diagram shows how the system modules interact:

```mermaid
graph TD
    %% Define main entry layers
    subgraph UI_Layer [User Interface Layer]
        A[QApplication / PySide6 GUI] -->|Launch| B[Splash Window]
        A -->|Render| C[Main Dashboard Window]
        C -->|User Chat| D[Chat Widget]
        C -->|Monitor| E[Performance PyQtGraph]
    end

    subgraph Voice_Layer [Voice Companion Layer]
        F[Microphone Listener] -->|Audio Stream| G[Speech Recognition]
        G -->|Text Raw Input| H[Speech Router]
        I[Speaker / TTS] <--|Speech Output| H
    end

    subgraph API_Layer [API Layer]
        J[FastAPI Server] -->|REST/WS Endpoints| K[APIServerRunner]
    end

    subgraph Brain_Layer [Cognitive Core]
        L[Intent Parser]
        M[Decision Engine]
        N[Brain Coordinator]
        O[Event Bus Singleton]

        H -->|Command Text| N
        D -->|Text Query| N
        K -->|API Request| N

        N -->|Parse Query| L
        L -->|Intent Match| M
        M -->|Select Skill| N
    end

    subgraph Skill_Layer [Executor Layer]
        P[Skill Manager]
        Q[System Automation]
        R[OCR Vision]
        S[Weather / Calc Skills]

        N -->|Route Action| P
        P -->|Execute Keyboard/Mouse| Q
        P -->|Scan Screen| R
        P -->|Calculate / Fetch| S
    end

    subgraph Storage_Layer [Memory & Persistence]
        T[Memory Manager]
        U[(user_memory.json)]
        V[(raw_events.db)]

        N -->|Read/Write Profile| T
        T -->|Sync| U
        T -->|Log Event| V
        O -->|Publish Memory Events| T
    end

    %% Styles
    classDef ui fill:#7c3aed,stroke:#fff,stroke-width:2px,color:#fff;
    classDef voice fill:#0d9488,stroke:#fff,stroke-width:2px,color:#fff;
    classDef api fill:#4b5563,stroke:#fff,stroke-width:2px,color:#fff;
    classDef brain fill:#2563eb,stroke:#fff,stroke-width:2px,color:#fff;
    classDef skill fill:#ea580c,stroke:#fff,stroke-width:2px,color:#fff;
    classDef store fill:#16a34a,stroke:#fff,stroke-width:2px,color:#fff;

    class A,B,C,D,E ui;
    class F,G,H,I voice;
    class J,K api;
    class L,M,N,O brain;
    class P,Q,R,S skill;
    class T,U,V store;
```

---

## 3. Core Request Flow

The pipeline handles query processing in a synchronized sequence:

```
[Raw Query (Text/Voice/API)] 
          │
          ▼
[brain/context.py: Context Object Created]
          │
          ▼
[brain/intent.py: Regex/Semantic Parser] ─────► [No Intent Match] ─────► [AI Pipeline / LLM fallback]
          │                                                                           │
          ▼ (Intent Identified)                                                       │
[brain/decision_engine.py: Router]                                                    │
          │                                                                           │
          ▼                                                                           ▼
[skills/skill_manager.py: Skill Exec] ◄───────────────────────────────────────────────┘
          │
          ▼
[memory/manager.py: Event logged in raw_events.db]
          │
          ▼
[response_composer: Final response output returned] ──► [ui/chat.py] & [voice/speaker.py]
```

---

## 4. Sandboxed Plugin Architecture

Khushi AI permits dynamic custom plugin loading while securing system access:
- **Sandbox Environment**: All custom python scripts are executed within a separate execution thread under isolated runtimes (`plugins/sandbox.py`).
- **Permission Check**: The `PluginManifest` specifies which resource layers (e.g. `filesystem_write`, `network_out`) the plugin requests. Access attempts without explicit permission trigger safe errors.

---

## 5. Multi-Tier Memory Architecture

The database structures memory into three layers:
1. **SQLite (`database/raw_events.db`)**: Log of all inputs, system actions, and response timestamps.
2. **JSON Profiles (`memory/user_memory.json`)**: Flat-file key-value storage mapping user settings, categories, and custom task records.
3. **World Model (`memory/world_model.json`)**: Graph-based node map depicting semantic connections between entities (e.g. `"Faisal"` -> `"lives in"` -> `"India"`).

---

## 6. System Startup Sequence

During initialization, the bootstrapper logs detailed timelines:

1. **Instrumentation**: Imports `utils.instrumentation` immediately to patch python I/O and capture logs.
2. **Provisioning**: The `ResourceManager` creates missing directories (`screenshots/`, `downloads/`, `logs/`).
3. **Self-Healing**: `CrashRecoverySystem` validates the JSON schema of memory and repairs corrupted database indexes.
4. **GUI Centering**: PySide6 launches, drawing the `SplashWindow` to block user commands until systems warm up.
5. **Thread Spawn**: Background threads start Uvicorn (FastAPI) and listen for speech wakewords.
6. **TTS Activation**: Welcomes user and opens `MainWindow`.
