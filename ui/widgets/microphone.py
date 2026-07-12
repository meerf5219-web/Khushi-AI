"""
ui/widgets/microphone.py — Microphone Toggle Widget
=====================================================
Custom toggle button visualizer representing the microphone status
(Active/Listening vs. Muted/Offline).
"""
from __future__ import annotations

import logging
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QPushButton

logger = logging.getLogger(__name__)


class MicrophoneWidget(QPushButton):
    """
    Microphone toggle switch control styled with active green / muted red states.
    """
    toggled_state = Signal(bool)  # Emits True if mic active, False if muted

    def __init__(self) -> None:
        super().__init__()
        self._active = True
        self.setFixedSize(50, 50)
        self.setCursor(Qt.PointingHandCursor)
        self._update_style()
        self.clicked.connect(self._on_clicked)

    def is_active(self) -> bool:
        return self._active

    def set_active(self, active: bool) -> None:
        self._active = active
        self._update_style()

    def _on_clicked(self) -> None:
        self._active = not self._active
        logger.info("[MIC WIDGET] Toggled active state to: %s", self._active)
        self._update_style()
        self.toggled_state.emit(self._active)

    def _update_style(self) -> None:
        if self._active:
            # Active Listening style: Green background with microphone emoji
            self.setText("🎙️")
            self.setStyleSheet("""
                QPushButton {
                    background-color: #10B981;
                    border: none;
                    border-radius: 25px;
                    font-size: 22px;
                }
                QPushButton:hover {
                    background-color: #059669;
                }
            """)
            self.setToolTip("Microphone Active — Click to mute")
        else:
            # Muted style: Red background with slash mic
            self.setText("🔇")
            self.setStyleSheet("""
                QPushButton {
                    background-color: #EF4444;
                    border: none;
                    border-radius: 25px;
                    font-size: 20px;
                }
                QPushButton:hover {
                    background-color: #DC2626;
                }
            """)
            self.setToolTip("Microphone Muted — Click to unmute")
        self.update()
