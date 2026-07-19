# Release Notes — Khushi AI v4.15 "Autonomous Companion"

We are proud to announce the release of **Khushi AI v4.15 "Autonomous Companion"**. This update focuses on system robustness, automatic recovery, diagnostic reporting, and detailed execution profiling.

---

## What's New in v4.15

### 🛡️ Crash Recovery & Diagnostics Framework
We've added a robust diagnostic layers that runs silently during application startup to detect missing or corrupted directories, invalid configuration schemas, and offline devices:
- **Timeline Logging**: Traces exact initialization times for different subsystems (UI, Voice synthesis, Local API Server, and Cognitive layers).
- **Auto-Recovery**: If resources are missing, the `CrashRecoverySystem` provisions directories or falls back to safe states automatically.
- **Detailed Log Dump**: If an unhandled exception prevents launch, details are immediately saved to `startup_error.log` and presented to the user inside a critical alert box.

### ⏱️ Performance Profiling Reports
Khushi now outputs JSON-structured performance records within the `logs/` directory on every successful startup. These files can help developers inspect and optimize loading phases:
- `startup_report.json`
- `thread_report.json`
- `voice_report.json`
- `resource_report.json`

### 🗣️ Intelligent TTS & Audio Fallbacks
Improved mic and speaker discovery ensures that configuration changes do not crash the app. The assistant gracefully falls back to basic voice modes if advanced devices are disconnected.

---

## How to Upgrade

To upgrade your local copy to v4.15:

1. Pull the latest commits:
   ```bash
   git pull origin main
   ```
2. Activate your virtual environment:
   ```powershell
   .venv\Scripts\activate
   ```
3. Update standard dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Verify your install is healthy by running the test suite:
   ```powershell
   pytest
   ```
