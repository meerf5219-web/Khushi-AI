"""
ui/widgets/conversation/stream_renderer.py — Smooth Stream Token Renderer
===========================================================================
Displays incoming tokens inside message bubbles. Optimizes rendering by showing
a single light text stream container with a blinking cursor during active streaming,
then swapping it with the full parsed Markdown layout when generation finishes.
"""
from __future__ import annotations

import logging
from PySide6.QtCore import QObject, Signal
from ui.widgets.conversation.typing_indicator import TypingCursorBlinker

logger = logging.getLogger(__name__)


class StreamRenderer(QObject):
    """
    Manages the active text stream inside a target MessageBubble.
    """

    def __init__(self, message_bubble: Any) -> None:
        super().__init__()
        self.bubble = message_bubble
        self.raw_text = ""
        self.blinker = TypingCursorBlinker(500)
        self.blinker.cursor_changed.connect(self._on_cursor_blink)

    def append_token(self, token: str, full_text: str) -> None:
        """Add a token to the stream buffer and update text view."""
        self.raw_text = full_text
        self._update_display(self.raw_text + "┃")

    def _on_cursor_blink(self, cursor_char: str) -> None:
        # Append blinking cursor to active stream
        self._update_display(self.raw_text + cursor_char)

    def _update_display(self, text_with_cursor: str) -> None:
        try:
            # Render light markdown to the body directly
            self.bubble.update_text(text_with_cursor)
        except Exception as exc:
            logger.error("Error updating stream display: %s", exc)

    def finalize(self) -> None:
        """Stop cursor blinker and parse full Markdown layout blocks."""
        self.blinker.stop()
        try:
            # Trigger modular parsing on bubble body
            self.bubble.body.set_markdown(self.raw_text)
            
            # Now trigger full multi-layout render inside bubble (if applicable)
            if hasattr(self.bubble, "render_full_markdown"):
                self.bubble.render_full_markdown()
        except Exception as exc:
            logger.error("Error finalizing stream: %s", exc)
