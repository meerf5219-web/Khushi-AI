"""
ui/widgets/conversation/typing_indicator.py — Cursor Blinker Helper
=====================================================================
A simple state container representing the blinking cursor ("|") appended
during stream processing.
"""
from __future__ import annotations

import logging
from PySide6.QtCore import QObject, QTimer, Signal

logger = logging.getLogger(__name__)


class TypingCursorBlinker(QObject):
    """
    Blinks a cursor character '|' periodically.
    """
    cursor_changed = Signal(str)  # Emits '|' or ''

    def __init__(self, interval_ms: int = 500) -> None:
        super().__init__()
        self._state = True
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._toggle)
        self.timer.start(interval_ms)

    def _toggle(self) -> None:
        self._state = not self._state
        cursor_char = "┃" if self._state else ""
        self.cursor_changed.emit(cursor_char)

    def stop(self) -> None:
        """Stop blink timer."""
        self.timer.stop()
