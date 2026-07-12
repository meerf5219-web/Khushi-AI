"""
ui/widgets/conversation/message_widget.py — Premium Message Card
===================================================================
Individual conversation bubbles representing User and Assistant dialogs.
Provides hover actions (toolbar), metadata metrics (latency, token count, model),
editing capabilities for User turns, and modular Markdown widgets layout.
"""
from __future__ import annotations

import time
import logging
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QLineEdit
)

from ui.widgets.conversation.markdown_renderer import MarkdownRenderer
from ui.widgets.conversation.message_toolbar import MessageToolbar

logger = logging.getLogger(__name__)


class MessageWidget(QFrame):
    """
    Styled message card containing dialogue text, meta metrics, and hover action menu.
    """
    edit_submitted = Signal(str)  # Emits new text when user edits and saves message
    delete_requested = Signal(str) # Emits event_id
    pin_requested = Signal(str)    # Emits event_id

    def __init__(self, event_id: str, text: str, sender: str, timestamp: float, metadata: dict = None) -> None:
        super().__init__()
        self.event_id = event_id
        self.raw_text = text
        self.sender = sender.lower()
        self.timestamp = timestamp
        self.metadata = metadata or {}
        
        self.renderer = MarkdownRenderer()
        self.toolbar: Optional[MessageToolbar] = None
        self._edit_mode = False

        self._init_ui()

    def _init_ui(self) -> None:
        # Layout margins
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 10, 12, 10)
        self.layout.setSpacing(4)

        # Style card background based on sender
        if self.sender == "user":
            self.setStyleSheet("""
                MessageWidget {
                    background-color: rgba(138, 43, 226, 0.06);
                    border: 1px solid rgba(138, 43, 226, 0.12);
                    border-radius: 12px;
                }
            """)
        else:
            self.setStyleSheet("""
                MessageWidget {
                    background-color: rgba(255, 255, 255, 0.02);
                    border: 1px solid rgba(255, 255, 255, 0.04);
                    border-radius: 12px;
                }
            """)

        # 1. Card Header: Avatar/Sender, Timestamp, metadata (latency, etc.)
        self.header_layout = QHBoxLayout()
        self.header_layout.setContentsMargins(0, 0, 0, 0)

        avatar = "👤" if self.sender == "user" else "🌀"
        sender_name = "You" if self.sender == "user" else "Khushi"
        time_str = time.strftime("%I:%M %p", time.localtime(self.timestamp))

        lbl_sender = QLabel(f"{avatar}  {sender_name}")
        lbl_sender.setStyleSheet("font-weight: bold; font-size: 11px; color: #94A3B8;")
        self.header_layout.addWidget(lbl_sender)

        # Add latency/model tags if present (Assistant only)
        if self.sender == "assistant" and self.metadata:
            metrics_str = []
            if "model" in self.metadata:
                metrics_str.append(self.metadata["model"])
            if "total_time" in self.metadata:
                metrics_str.append(f"{self.metadata['total_time']:.2f}s")
            if "tokens" in self.metadata:
                metrics_str.append(f"{self.metadata['tokens']} tokens")
            
            if metrics_str:
                lbl_metrics = QLabel(" | ".join(metrics_str))
                lbl_metrics.setStyleSheet("font-size: 10px; color: #64748B; background-color: rgba(255,255,255,0.04); padding: 1px 6px; border-radius: 4px;")
                self.header_layout.addWidget(lbl_metrics)

        self.header_layout.addStretch()

        lbl_time = QLabel(time_str)
        lbl_time.setStyleSheet("font-size: 10px; color: #64748B;")
        self.header_layout.addWidget(lbl_time)
        self.layout.addLayout(self.header_layout)

        # 2. Main Body Container
        self.body_container = QWidget()
        self.body_layout = QVBoxLayout(self.body_container)
        self.body_layout.setContentsMargins(0, 4, 0, 4)
        self.body_layout.setSpacing(8)
        self.layout.addWidget(self.body_container)

        # Default body text display (or text editor if user edits)
        self.render_full_markdown()

        # 3. Action Toolbar (Assistant messages or hover menu)
        # We instantiate it but only show it when hovered or focused
        self.toolbar = MessageToolbar()
        self.toolbar.copy_requested.connect(self._copy_formatted)
        self.toolbar.copy_raw_requested.connect(self._copy_raw)
        self.toolbar.delete_requested.connect(lambda: self.delete_requested.emit(self.event_id))
        self.toolbar.pin_requested.connect(lambda: self.pin_requested.emit(self.event_id))
        
        # User message: add edit trigger instead of toolbar
        if self.sender == "user":
            self.btn_edit = QPushButton("✏️ Edit")
            self.btn_edit.setStyleSheet("QPushButton { font-size: 10px; color: #64748B; background: transparent; border: none; } QPushButton:hover { color: #FFFFFF; }")
            self.btn_edit.clicked.connect(self._toggle_edit)
            self.header_layout.insertWidget(self.header_layout.count() - 2, self.btn_edit)

        self.layout.addWidget(self.toolbar)
        self.toolbar.hide()

    def render_full_markdown(self) -> None:
        """Parse raw text and render modular sub-widgets inside layout."""
        self.renderer.parse_to_layout(self.raw_text, self.body_layout)

    def update_text(self, text: str) -> None:
        """Lightweight update text during token streaming."""
        self.raw_text = text
        # If there's only one child and it's a MarkdownWidget, update it directly
        if self.body_layout.count() == 1 and isinstance(self.body_layout.itemAt(0).widget(), MarkdownWidget):
            self.body_layout.itemAt(0).widget().set_markdown(text)
        else:
            self.render_full_markdown()

    # Hover detection to show action buttons pill
    def enterEvent(self, event) -> None:
        if self.toolbar:
            self.toolbar.show()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        if self.toolbar:
            self.toolbar.hide()
        super().leaveEvent(event)

    def _toggle_edit(self) -> None:
        self._edit_mode = not self._edit_mode
        if self._edit_mode:
            self.btn_edit.setText("💾 Save")
            self.edit_input = QLineEdit(self.raw_text)
            self.edit_input.setObjectName("ChatInput")
            self.edit_input.setStyleSheet("background-color: #16161A; border: 1px solid #8A2BE2; padding: 6px; border-radius: 6px;")
            
            # Remove message widgets
            while self.body_layout.count() > 0:
                child = self.body_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            self.body_layout.addWidget(self.edit_input)
        else:
            self.btn_edit.setText("✏️ Edit")
            new_text = self.edit_input.text().strip()
            if new_text and new_text != self.raw_text:
                self.raw_text = new_text
                self.edit_submitted.emit(new_text)
            self.render_full_markdown()

    def _copy_formatted(self) -> None:
        from PySide6.QtGui import QClipboard
        from PySide6.QtWidgets import QApplication
        
        # Clean markdown symbols for raw clipboard copy
        clean_text = self.raw_text.replace("```", "").replace("**", "")
        clipboard = QApplication.clipboard()
        clipboard.setText(clean_text)

    def _copy_raw(self) -> None:
        from PySide6.QtGui import QClipboard
        from PySide6.QtWidgets import QApplication
        
        clipboard = QApplication.clipboard()
        clipboard.setText(self.raw_text)
