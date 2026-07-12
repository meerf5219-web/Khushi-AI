"""
ui/widgets/status.py — Application Status Indicator Widget
============================================================
Displays status labels (Online, Offline, Listening, Thinking, Speaking)
with animated pulsing indicator lights matching the active state.
"""
from __future__ import annotations

import logging
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame

logger = logging.getLogger(__name__)


class StatusWidget(QWidget):
    """
    Sleek status bar displaying system connectivity and active brain states.
    """

    def __init__(self) -> None:
        super().__init__()
        self._state = "listening"
        self._pulse = True
        self._pulse_tick = 0
        self._init_ui()

        # Simple timer for indicator light pulsing effect
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_pulse)
        self.timer.start(500)

    def set_state(self, state: str) -> None:
        """Modify indicator label and light color presets."""
        state = state.lower()
        if state in ("listening", "thinking", "speaking", "offline"):
            self._state = state
            
            # Match status labels
            if state == "listening":
                self.lbl_text.setText("Listening")
                self.light.setStyleSheet("background-color: #10B981; border-radius: 4px;") # Green
            elif state == "thinking":
                self.lbl_text.setText("Thinking")
                self.light.setStyleSheet("background-color: #F59E0B; border-radius: 4px;") # Amber
            elif state == "speaking":
                self.lbl_text.setText("Speaking")
                self.light.setStyleSheet("background-color: #8A2BE2; border-radius: 4px;") # Purple
            elif state == "offline":
                self.lbl_text.setText("Offline")
                self.light.setStyleSheet("background-color: #EF4444; border-radius: 4px;") # Red

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignLeft | Qt.AlignCenter)

        # Pulse light QFrame
        self.light = QFrame()
        self.light.setFixedSize(8, 8)
        self.light.setStyleSheet("background-color: #10B981; border-radius: 4px;")
        layout.addWidget(self.light)

        # Status text label
        self.lbl_text = QLabel("Listening")
        self.lbl_text.setStyleSheet("font-size: 11px; font-weight: 600; color: #94A3B8;")
        layout.addWidget(self.lbl_text)

    def _on_pulse(self) -> None:
        # Subtle blinking pulse effect on the status light for active processing states
        if self._state in ("thinking", "speaking"):
            self._pulse = not self._pulse
            if self._pulse:
                self.light.show()
            else:
                self.light.hide()
        else:
            self.light.show()
            self._pulse = True
        self.update()
