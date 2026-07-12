"""
ui/widgets/typing.py — Chat Typing Indicator Widget
===================================================
Draws a Siri/Apple-style typing indicator containing three bouncing dots
with smooth anti-aliased geometry drawing.
"""
from __future__ import annotations

import math
import logging
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QBrush
from PySide6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class TypingIndicatorWidget(QWidget):
    """
    Pulsing chat indicator displaying three bouncing dots.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setFixedSize(60, 24)
        
        self._phase = 0.0
        
        # 60 FPS animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_tick)
        self.timer.start(16)

    def _on_tick(self) -> None:
        self._phase += 0.12
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Completely transparent background
        painter.fillRect(event.rect(), Qt.transparent)

        # Dot properties
        dot_radius = 4.0
        spacing = 14.0
        center_x = self.width() / 2.0
        center_y = self.height() / 2.0

        # Draw 3 bouncing dots using phase offsets
        for i in range(3):
            # Phase offset for wave effect (left to right)
            offset = i * 1.0
            y_bounce = math.sin(self._phase - offset) * 5.0
            
            # Position calculations
            x = center_x + (i - 1) * spacing
            y = center_y + y_bounce

            # Pulse opacity based on height
            alpha = int(150 + 105 * math.sin(self._phase - offset))
            color = QColor(138, 43, 226, alpha)  # Purple
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(x - dot_radius, y - dot_radius, dot_radius * 2.0, dot_radius * 2.0)
