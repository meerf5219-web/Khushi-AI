# Khushi AI - User Guide

This guide explains how to install, configure, pair, and run Khushi AI on your computer and smart devices.

## 1. Installation Setup
To install Khushi AI dynamically on your Windows machine:
1. Run `installer.py` (or compile it as `Installer.exe` and execute).
2. Choose your preferred installation folder (defaults to `%LocalAppData%\Khushi`).
3. Toggle options to "Create Desktop Shortcut" and "Run at Startup".
4. Click **Install**.
5. Once complete, click **Finish** to launch the companion assistant.

## 2. Desktop Settings & API Server
When launched, Khushi runs a secure, local API server to connect with desktop extensions or mobile clients.
- Open **Settings** from the dashboard sidebar.
- Observe:
  - **Local URL**: `http://127.0.0.1:8000` (used for local queries).
  - **LAN URL**: `http://192.168.x.x:8000` (used for pairing external mobile clients).
  - **API Token**: A secure, auto-generated cryptographically random key.
  - **Pairing Link**: A single-use config string containing the LAN IP and token.

## 3. Mobile Companion Sync
1. Launch the React Native companion app on your phone.
2. If not paired, paste the **Pairing Link** (or enter the LAN URL and API Token manually) and click **Pair and Connect**.
3. Once paired, you can:
   - View desktop system CPU, memory, and battery telemetry.
   - Adjust volume, mute, or lock your computer remotely.
   - Download or upload shared files and camera photos.
   - Synchronize clipboard buffers and tasks.
   - Stream voice commands directly to the desktop brain.

## 4. Protected Backups
To secure your memory history from data corruption:
- Use the backup command via chat or client endpoints:
  - Backups are encrypted with **AES-256 (Fernet)** based on a user-provided password and PBKDF2 salt.
  - Active configurations can be exported or restored securely, preventing data loss by validating file hashes before replacement.

## 5. Vehicle Diagnostics scan
- Connect an ELM327 USB or Bluetooth adapter to your vehicle.
- Open vehicle settings to scan for devices.
- Once connected, read real-time telemetry (Coolant Temperature, Engine Load, Engine RPM, Vehicle Speed) or retrieve diagnostic trouble codes (DTCs).
