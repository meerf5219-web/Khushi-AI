"""
ui/widgets/conversation/thinking_indicator.py — Visual Brain Thinking Animation
================================================================================
Displays an animated pulsing dot progress message "Khushi is thinking..."
shown while the Brain processes queries.
"""
from __future__ import annotations

import logging
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel

logger = logging.getLogger(__name__)


class ThinkingIndicator(QWidget):
    """
    Animated widget shown during the latency phase before the first stream token.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setFixedHeight(30)
        self._dots = 0
        self._init_ui()

        # Update animation ticks every 400ms
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_tick)
        self.timer.start(400)

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignLeft | Qt.AlignCenter)

        self.lbl_text = QLabel("Khushi is thinking")
        self.lbl_text.setStyleSheet("font-size: 13px; color: #94A3B8; font-style: italic;")
        
        self.lbl_dots = QLabel("●")
        self.lbl_dots.setStyleSheet("font-size: 14px; color: #8A2BE2;")

        layout.addWidget(self.lbl_text)
        layout.addWidget(self.lbl_dots)

    def _on_tick(self) -> None:
        self._dots = (self._dots + 1) % 4
        
        # Build dot patterns: "●", "●●", "●●●", or empty
        dot_str = "●" * self._dots
        if not dot_str:
            dot_str = " "
            
        self.lbl_dots.setText(dot_str)
        self.update()

    def stop(self) -> None:
        """Stop animation timer."""
        self.timer.stop()
