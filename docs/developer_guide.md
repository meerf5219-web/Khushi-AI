# Khushi AI - Developer Guide

Welcome to the Khushi AI developer codebase. This document outlines the architecture, package folder structure, event bus coordination model, and packaging compilation tasks.

## 1. Project Directory Structure
- `api/`: FastAPI REST/WebSocket server routing, rate limiting, and config managers.
- `brain/`: Central cognitive hub containing emotional intelligence, pipeline nodes, intent matching, and the `WorldModel` knowledge graph engine.
- `devices/`: Hardware abstraction layer containing device registries, bluetooth scans, COM serial interfaces, and OBD-II telemetry.
- `dashboard/`: PySide6 GUI dashboard layouts, views (overview, memory, plugin managers), and PyQtGraph visualizers.
- `memory/`: Category-aware user files persistence and AES-256 backup utilities.
- `skills/`: System execution modules (applications launcher, search, volume controls, screenshooters).
- `voice/`: SAPI5/eSpeak TTS adapters and wake-word listening services.
- `tests/`: Extensive pytest unit and integration coverage.

## 2. Event Bus Communication Model
Thread-safe event publishing and subscriptions are handled via a global singleton event bus:
```python
from brain.event_bus import event_bus

# Subscribing to events
def handle_event(data):
    print("Received event details:", data)
event_bus.subscribe("MEMORY_UPDATED", handle_event)

# Publishing events
event_bus.publish("MEMORY_UPDATED", {"key": "color", "value": "green"})
```
WebSocket endpoints use dynamic event bus listener registrations, cleaning them up in connection exit loops to prevent memory leaks.

## 3. PyInstaller Executable Compilation
The executable `Khushi.exe` is compiled from `main.py` using:
```bash
.venv\Scripts\python -m PyInstaller Khushi.spec --clean --noconfirm
```
All dynamic library dependencies, custom serial modules, databases, assets, and newly added packages are registered inside the PyInstaller hidden imports section.

## 4. Test Verification
Run the pytest test suite via:
```bash
.venv\Scripts\python.exe -m pytest
```
Mock overrides for OS-level modules (e.g. `pywinauto`, `pyperclip`, `pyautogui`) are managed inside `tests/conftest.py` to enable headless test runs.
