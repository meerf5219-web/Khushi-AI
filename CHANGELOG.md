# Changelog

All notable changes to the Khushi AI project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-07-19
### Added
- **Timeline Stage Logger**: Real-time logging of stages during GUI startup.
- **Recovery Checkpoint System**: Diagnostic health checks and self-repairing config validation.
- **Micro-durations tracking**: Measures execution times in `brain/startup.py` and `brain/brain.py` to optimize latency.
- **Hardware Diagnostic Reports**: Automatic generation of `voice_report.json` and `resource_report.json` on start.
- **Thread Diagnostics**: Profiling multi-threading behavior and emitting results in `thread_report.json`.

### Changed
- Refactored `ui/app.py` to integrate startup watchdogs and load synchronization.
- Optimized exception coverage in `main.py` to write raw startup errors immediately.
- Improved fallback TTS behavior when primary device is offline.

---

## [1.0.0-rc1] - 2026-05-18
### Added
- **Dynamic Plugin Sandbox**: Isolated execution runtime for third-party scripts.
- **EasyOCR Core Integration**: High-precision screen scanning capability.
- **Web Companion API**: Initial support for browser-based automation via Playwright.

---

## [1.0.0-beta] - 2026-02-12
### Added
- **Generation 1 Release**: Complete GUI components in PySide6.
- **Intent-based Routing**: Advanced routing system dynamically processing inputs across skills.
- **Persistent SQLite memory**: Event logging into `raw_events.db`.
