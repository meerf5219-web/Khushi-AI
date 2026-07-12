"""
ui/widgets/waveform.py — Animated Waveform Visualization Widget
================================================================
Draws a 60 FPS hardware-accelerated vector waveform inside a custom paintEvent.
Visualizes states: Idle (breathing line), Listening (active sine waves),
Thinking (pulsing breathing orb), and Speaking (dynamic voice waves).
"""
from __future__ import annotations

import math
import logging
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QLinearGradient, QPainterPath
from PySide6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class WaveformWidget(QWidget):
    """
    Siri-like translucent waveform animator using anti-aliased vector paths.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setFixedHeight(80)
        self.setObjectName("WaveformWidget")
        
        # State: "idle", "listening", "thinking", "speaking"
        self._state = "idle"
        self._phase = 0.0
        self._amplitude = 0.05
        self._target_amplitude = 0.05
        
        # 60 FPS animation timer (16ms interval)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_animation)
        self.timer.start(16)

    def set_state(self, state: str) -> None:
        """Modify the active waveform visual state."""
        state = state.lower()
        if state in ("idle", "listening", "thinking", "speaking", "offline"):
            self._state = state
            
            # Map target amplitude bounds
            if state == "idle":
                self._target_amplitude = 0.05
            elif state == "listening":
                self._target_amplitude = 0.35
            elif state == "thinking":
                self._target_amplitude = 0.15
            elif state == "speaking":
                self._target_amplitude = 0.55
            elif state == "offline":
                self._target_amplitude = 0.01
            
            logger.debug("[WAVEFORM] Switched visual state to: %s", state)

    def set_amplitude(self, amp: float) -> None:
        """Manually drive voice amplitude (from mic input)."""
        self._target_amplitude = max(0.01, min(1.0, amp))

    def _update_animation(self) -> None:
        # Interpolate amplitude for smooth transitions
        self._amplitude += (self._target_amplitude - self._amplitude) * 0.15
        
        # Advance wave phase
        speed = 0.12 if self._state == "speaking" else 0.08
        if self._state == "thinking":
            speed = 0.04
        self._phase += speed
        
        # Request a paintEvent redraw
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        width = self.width()
        height = self.height()
        mid_y = height / 2.0

        # Paint background (completely transparent QWidget, inherits QFrame container styling)
        painter.fillRect(event.rect(), Qt.transparent)

        # Draw a pulsing circle orb if state is "thinking" (Vision Pro styling)
        if self._state == "thinking":
            self._draw_thinking_orb(painter, width, height, mid_y)
            return

        # Determine colors based on active state
        if self._state == "listening":
            # Emerald green gradient
            color_accent = QColor(16, 185, 129, 140)   # #10B981
            color_mid = QColor(6, 182, 212, 100)       # #06B6D4
        elif self._state == "speaking":
            # Purple / Magenta gradient
            color_accent = QColor(138, 43, 226, 180)   # Violet
            color_mid = QColor(244, 63, 94, 120)       # #F43F5E
        else:
            # Idle/Offline: clean dark grey
            color_accent = QColor(148, 163, 184, 50)   # Greyish
            color_mid = QColor(100, 116, 139, 30)

        # Draw 3 overlapping sine waves with distinct phases, widths, and frequencies
        self._draw_sine_wave(painter, width, mid_y, self._phase, self._amplitude, color_accent, 2.5, 1.0)
        self._draw_sine_wave(painter, width, mid_y, self._phase * 1.5 + 2.0, self._amplitude * 0.7, color_mid, 1.5, 1.8)
        self._draw_sine_wave(painter, width, mid_y, self._phase * 0.8 + 4.0, self._amplitude * 0.5, color_accent, 1.0, 0.7)

    def _draw_sine_wave(
        self,
        painter: QPainter,
        width: float,
        mid_y: float,
        phase: float,
        amp: float,
        color: QColor,
        pen_width: float,
        freq_multiplier: float,
    ) -> None:
        path = QPainterPath()
        path.moveTo(0, mid_y)
        
        max_amplitude_px = 30.0 * amp
        
        # Compute coordinates across screen columns
        for x in range(0, int(width) + 1, 4):
            # Normalization scale (0.0 to 1.0)
            norm_x = x / width
            # Sine wave frequency profile
            omega = (norm_x * math.pi * 2.0 * freq_multiplier) + phase
            
            # Envelope constraint (taper values near margins so wave hits 0 at edges)
            envelope = math.sin(norm_x * math.pi)
            
            y = mid_y + (math.sin(omega) * max_amplitude_px * envelope)
            path.lineTo(x, y)

        pen = QPen(color, pen_width)
        painter.setPen(pen)
        painter.drawPath(path)

    def _draw_thinking_orb(self, painter: QPainter, width: float, height: float, mid_y: float) -> None:
        """Vision Pro glowing breathing indicator."""
        pulse = (math.sin(self._phase) + 1.0) / 2.0  # 0.0 to 1.0
        radius = 16 + (4 * pulse)
        
        # Center coordinates
        center_x = width / 2.0
        
        # Outer soft glow
        glow_grad = QLinearGradient(center_x - radius*2, mid_y - radius*2, center_x + radius*2, mid_y + radius*2)
        glow_grad.setColorAt(0.0, QColor(138, 43, 226, 40))
        glow_grad.setColorAt(1.0, QColor(244, 63, 94, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(glow_grad))
        painter.drawEllipse(center_x - radius*2, mid_y - radius*2, radius*4, radius*4)
        
        # Inner solid core
        core_grad = QLinearGradient(center_x - radius, mid_y - radius, center_x + radius, mid_y + radius)
        core_grad.setColorAt(0.0, QColor(138, 43, 226, 220))
        core_grad.setColorAt(1.0, QColor(244, 63, 94, 180))
        painter.setBrush(QBrush(core_grad))
        painter.drawEllipse(center_x - radius, mid_y - radius, radius*2, radius*2)
