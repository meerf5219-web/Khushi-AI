"""
ui/widgets/chat.py — Conversation Chat Container
===================================================
Renders user and assistant message bubbles. Supports real-time text streaming,
smooth scroll positioning, message copy-to-clipboard, and animations.
"""
from __future__ import annotations

import time
import logging
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame, QLabel,
    QTextEdit, QPushButton, QSizePolicy
)
from ui.widgets.markdown import MarkdownWidget
from ui.widgets.typing import TypingIndicatorWidget

logger = logging.getLogger(__name__)


class MessageBubble(QFrame):
    """
    Individual chat bubble widget supporting formatted text and clean styling.
    """

    def __init__(self, text: str, sender: str, timestamp: float) -> None:
        super().__init__()
        self.sender = sender
        self.timestamp = timestamp
        self._init_ui(text)

    def _init_ui(self, text: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)
        
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        # Meta Header: Sender name + Timestamp
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        sender_name = "You" if self.sender == "user" else "Khushi"
        time_str = time.strftime("%I:%M %p", time.localtime(self.timestamp))
        
        lbl_sender = QLabel(sender_name)
        lbl_sender.setStyleSheet("font-weight: bold; font-size: 11px; color: #94A3B8;")
        
        lbl_time = QLabel(time_str)
        lbl_time.setStyleSheet("font-size: 10px; color: #64748B;")
        
        header_layout.addWidget(lbl_sender)
        header_layout.addStretch()
        header_layout.addWidget(lbl_time)
        layout.addLayout(header_layout)

        # Message body widget with Markdown parser
        self.body = MarkdownWidget(text)
        layout.addWidget(self.body)

        # Stylize bubble borders & backgrounds
        if self.sender == "user":
            self.setStyleSheet("""
                MessageBubble {
                    background-color: rgba(138, 43, 226, 0.08);
                    border: 1px solid rgba(138, 43, 226, 0.15);
                    border-radius: 10px;
                }
            """)
        else:
            self.setStyleSheet("""
                MessageBubble {
                    background-color: rgba(255, 255, 255, 0.03);
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    border-radius: 10px;
                }
            """)

    def update_text(self, text: str) -> None:
        """Update the bubble text dynamically (used during streaming)."""
        self.body.set_markdown(text)


class ChatWidget(QWidget):
    """
    Scrollable conversation list managing active message bubbles.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("ChatContainer")
        self.active_stream_bubble: Optional[MessageBubble] = None
        self.typing_indicator: Optional[TypingIndicatorWidget] = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Scroll Area Setup
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(12)
        self.scroll_layout.addStretch()  # Keep widgets pinned to top

        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll)

    def show_typing(self) -> None:
        """Display animated typing dots at the bottom of the conversation layout."""
        if not self.typing_indicator:
            self.typing_indicator = TypingIndicatorWidget()
            self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, self.typing_indicator)
            self.scroll_to_bottom()

    def hide_typing(self) -> None:
        """Remove typing dots widget from list layout."""
        if self.typing_indicator:
            self.scroll_layout.removeWidget(self.typing_indicator)
            self.typing_indicator.deleteLater()
            self.typing_indicator = None

    def add_message(self, text: str, sender: str) -> None:
        """Add a static message bubble."""
        self.hide_typing()
        # Clean streaming reference if user speaks
        if sender == "user":
            self.active_stream_bubble = None

        bubble = MessageBubble(text, sender, time.time())
        # Insert before the spacer stretch at bottom
        self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, bubble)
        self.scroll_to_bottom()

    def start_streaming(self) -> None:
        """Create a new streaming bubble for tokens to write into."""
        self.hide_typing()
        self.active_stream_bubble = MessageBubble("", "assistant", time.time())
        self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, self.active_stream_bubble)
        self.scroll_to_bottom()

    def append_stream_token(self, token: str, full_text: str) -> None:
        """Update active streaming bubble in place."""
        self.hide_typing()
        if not self.active_stream_bubble:
            self.start_streaming()
        
        if self.active_stream_bubble:
            self.active_stream_bubble.update_text(full_text)
            self.scroll_to_bottom()

    def clear(self) -> None:
        """Remove all messages."""
        self.hide_typing()
        self.active_stream_bubble = None
        # Remove widgets except the final stretch spacer
        while self.scroll_layout.count() > 1:
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def scroll_to_bottom(self) -> None:
        """Position scrollbar at maximum offset."""
        # Use single shot timer to ensure widgets completed layout
        from PySide6.QtCore import QTimer
        QTimer.singleShot(25, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))
