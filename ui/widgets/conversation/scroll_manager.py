"""
ui/widgets/conversation/scroll_manager.py — Smart Auto-Scroll Controller
========================================================================
Manages QScrollArea scrolling offsets during real-time speech token arrival.
If the user scrolls upward manually to read previous content, auto-scrolling is
temporarily paused. It resumes only when the scrollbar returns near the bottom.
"""
from __future__ import annotations

import logging
from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QScrollArea

logger = logging.getLogger(__name__)


class ScrollManager(QObject):
    """
    Auto-scroll controller tracking scroll position and range adjustments.
    """

    def __init__(self, scroll_area: QScrollArea) -> None:
        super().__init__()
        self.scroll = scroll_area
        self.bar = self.scroll.verticalScrollBar()
        self._user_scrolled_up = False
        
        # Track previous maximum to detect range changes
        self._prev_max = self.bar.maximum()
        
        # Listen to value and range signals
        self.bar.valueChanged.connect(self._on_value_changed)
        self.bar.rangeChanged.connect(self._on_range_changed)

    def _on_value_changed(self, value: int) -> None:
        max_val = self.bar.maximum()
        # If scroll index is more than 35 pixels away from bottom, assume user scrolled up
        if max_val - value > 35:
            self._user_scrolled_up = True
        else:
            self._user_scrolled_up = False

    def _on_range_changed(self, min_val: int, max_val: int) -> None:
        # Triggered when layout adds widgets or height expands
        if not self._user_scrolled_up:
            # User is at the bottom, so follow the expansion
            self.scroll_to_bottom()
        self._prev_max = max_val

    def scroll_to_bottom(self) -> None:
        """Position scrollbar slider at the bottom of the document."""
        # Use single-shot timer for layout completion safety
        QTimer.singleShot(16, self._force_scroll)

    def _force_scroll(self) -> None:
        self.bar.setValue(self.bar.maximum())

    def reset_scroll_lock(self) -> None:
        """Force-enable auto-scroll alignment."""
        self._user_scrolled_up = False
        self.scroll_to_bottom()
