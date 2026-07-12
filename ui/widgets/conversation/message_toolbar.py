"""
ui/widgets/conversation/message_toolbar.py — Hover Action Toolbar Widget
========================================================================
Floating menu appearing over message cards. Supports Copy, Pin, Delete, and Export.
"""
from __future__ import annotations

import logging
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton

logger = logging.getLogger(__name__)


class MessageToolbar(QWidget):
    """
    Sleek row of action icons displayed on message bubble hover.
    """
    copy_requested = Signal()
    copy_raw_requested = Signal()
    delete_requested = Signal()
    pin_requested = Signal()
    export_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._pinned = False
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignRight)

        # Style layout container to look like floating pill bar
        self.setStyleSheet("""
            QWidget {
                background-color: #1A1A1E;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 6px;
            }
            QPushButton {
                font-size: 11px;
                padding: 3px 6px;
                background-color: transparent;
                border: none;
                border-radius: 4px;
                color: #94A3B8;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.06);
                color: #FFFFFF;
            }
        """)

        # 1. Copy Formatted
        self.btn_copy = QPushButton("📋 Copy")
        self.btn_copy.setToolTip("Copy formatted text")
        self.btn_copy.setCursor(Qt.PointingHandCursor)
        self.btn_copy.clicked.connect(self.copy_requested.emit)
        layout.addWidget(self.btn_copy)

        # 2. Copy Raw Markdown
        self.btn_copy_raw = QPushButton("📄 MD")
        self.btn_copy_raw.setToolTip("Copy raw markdown text")
        self.btn_copy_raw.setCursor(Qt.PointingHandCursor)
        self.btn_copy_raw.clicked.connect(self.copy_raw_requested.emit)
        layout.addWidget(self.btn_copy_raw)

        # 3. Pin Message
        self.btn_pin = QPushButton("📌 Pin")
        self.btn_pin.setToolTip("Pin this message")
        self.btn_pin.setCursor(Qt.PointingHandCursor)
        self.btn_pin.clicked.connect(self._on_pin_clicked)
        layout.addWidget(self.btn_pin)

        # 4. Delete
        self.btn_delete = QPushButton("🗑️ Delete")
        self.btn_delete.setToolTip("Delete this message")
        self.btn_delete.setCursor(Qt.PointingHandCursor)
        self.btn_delete.clicked.connect(self.delete_requested.emit)
        layout.addWidget(self.btn_delete)

    def _on_pin_clicked(self) -> None:
        self._pinned = not self._pinned
        if self._pinned:
            self.btn_pin.setText("📌 Pinned")
            self.btn_pin.setStyleSheet("QPushButton { color: #8A2BE2; font-weight: bold; }")
        else:
            self.btn_pin.setText("📌 Pin")
            self.btn_pin.setStyleSheet("QPushButton { color: #94A3B8; }")
        self.pin_requested.emit()
