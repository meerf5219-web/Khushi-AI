# Khushi AI — Visual Interface Specification & Placeholders

This document serves as a placeholder registry and visual description spec for the key screens of the **Khushi AI** application. These specs guide developers on layout, components, and design alignment.

---

## 1. Application Home (Dashboard UI)
- **Path Reference**: `assets/app_home.png`
- **Location**: Rendered via `ui/main_window.py` and `ui/widgets/sidebar.py`.
- **Layout Grid**: Two-column layout:
  - **Left Sidebar**: Sleek glassmorphic column containing vertical navigation tabs (Home, Chat, Vehicle Scan, Settings). Accent colors change dynamically on hover.
  - **Main Area (Overview)**: Welcoming dashboard with real-time hardware performance metrics (CPU gauge, Memory load line charts from `pyqtgraph`, active task queues).
- **Design Tokens**: HSL Tailwind purple accents (`#7c3aed`), dark grey backing panels (`#111827`), rounded widgets (`16px`).

---

## 2. Chat Window UI
- **Path Reference**: `assets/chat_window.png`
- **Location**: Rendered via `ui/widgets/chat.py` and bubble layout adapters.
- **Components**:
  - **Message Scroll Area**: Chat bubbles displaying conversation history. Faisal's messages align to the right (purple bubbles), Khushi's responses align to the left (dark slate bubble).
  - **Typing Status**: Waveform animations (`ui/widgets/waveform.py`) representing active listening or dynamic dots for cognitive processing.
  - **Input Bar**: Centered rounded text box with a microphone button widget. Hovering over the microphone activates a pulse glow animation.

---

## 3. Voice Assistant Overlay
- **Path Reference**: `assets/voice_assistant.png`
- **Location**: Initiated from `voice_companion/` background audio streams.
- **Visuals**:
  - A small, borderless overlay widget that rises from the taskbar when the wake word *"Khushi"* is detected.
  - Displays a high-frequency dynamic waveform visualization that shifts colors depending on voice volume and intensity.

---

## 4. Settings Panel UI
- **Path Reference**: `assets/settings_panel.png`
- **Location**: Rendered from `ui/widgets/settings.py`.
- **Fields**:
  - **Authentication Block**: Displays API keys, local token status, and the single-use pairing link.
  - **Speech Synthesizer Configuration**: Dropdown to select voices (SAPI5/eSpeak), adjust reading speed slider, and toggle voice responses.
  - **OBD-II Setup**: Device scan toggles, baud rate selection, and port selectors (COM ports).

---

## 5. Diagnostics Terminal UI
- **Path Reference**: `assets/diagnostics_terminal.png`
- **Location**: Emitted on logs inside the App local directories and PySide6 about window logs.
- **Content**:
  - Raw stream timeline logs illustrating execution duration down to the millisecond.
  - Checkpoint audits detailing the recovery states of configuration databases, models, and network links.

---

## 6. Conceptual Architecture Diagram
- **Path Reference**: `assets/architecture_diagram.png`
- **Specification**: A high-level visual representation of the cognitive request routing and multi-tier storage layers. (See the rendered Mermaid diagram in [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)).
