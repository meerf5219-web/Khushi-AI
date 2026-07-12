"""
ui/widgets/conversation/conversation_search.py — Conversational Search Widget
=============================================================================
A toolbar that filters and navigates previous messages based on user query inputs,
speaker selectors, dates, or pinned parameters.
"""
from __future__ import annotations

import logging
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QComboBox, QPushButton, QLabel, QFrame
)

logger = logging.getLogger(__name__)


class ConversationSearchWidget(QFrame):
    """
    Search toolbar widget supporting filtering and signal emissions.
    """
    search_changed = Signal(str, dict)  # Emits (query, filter_options)
    clear_search = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("SearchToolbar")
        self.setStyleSheet("""
            #SearchToolbar {
                background-color: #141419;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }
            QLineEdit {
                background-color: #18181D;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 4px;
                padding: 4px 8px;
                color: #FFFFFF;
            }
            QComboBox {
                background-color: #18181D;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 4px;
                padding: 4px 6px;
                color: #FFFFFF;
            }
            QPushButton {
                font-size: 11px;
                padding: 4px 10px;
                background-color: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 4px;
                color: #94A3B8;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.08);
                color: #FFFFFF;
            }
        """)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 6, 15, 6)
        layout.setSpacing(8)

        # Search icon label
        icon = QLabel("🔍")
        layout.addWidget(icon)

        # Text input field
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("Search keyword in chat...")
        self.input_search.textChanged.connect(self._on_search_modified)
        layout.addWidget(self.input_search)

        # Filter option dropdown
        self.combo_filter = QComboBox()
        self.combo_filter.addItems(["All Messages", "User Only", "Assistant Only", "Pinned Only"])
        self.combo_filter.currentTextChanged.connect(lambda: self._on_search_modified())
        layout.addWidget(self.combo_filter)

        # Clear Button
        self.btn_clear = QPushButton("Clear")
        self.btn_clear.clicked.connect(self._clear_search)
        layout.addWidget(self.btn_clear)

    def _on_search_modified(self, text: str = "") -> None:
        query = self.input_search.text().strip()
        filt = self.combo_filter.currentText()
        
        options = {
            "user_only": filt == "User Only",
            "assistant_only": filt == "Assistant Only",
            "pinned_only": filt == "Pinned Only"
        }
        
        self.search_changed.emit(query, options)

    def _clear_search(self) -> None:
        self.input_search.clear()
        self.combo_filter.setCurrentIndex(0)
        self.clear_search.emit()
