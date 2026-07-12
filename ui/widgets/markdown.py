"""
ui/widgets/markdown.py — Rich Text Markdown Parser
===================================================
Uses PySide6 QTextEdit with native Qt6 Markdown rendering engine.
Applies clean CSS stylings for code blocks, lists, bold text, and headers.
"""
from __future__ import annotations

import logging
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import QTextEdit, QFrame

logger = logging.getLogger(__name__)


class MarkdownWidget(QTextEdit):
    """
    Read-only text widget that parses and renders markdown string content natively.
    """

    def __init__(self, text: str = "") -> None:
        super().__init__()
        self.setReadOnly(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setLineWrapMode(QTextEdit.WidgetWidth)
        
        # Transparent background and padding adjustments
        self.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)

        # Set default text style sheet for document formatting
        doc = self.document()
        doc.setDefaultStyleSheet("""
            p { line-height: 140%; color: #E2E8F0; }
            h1, h2, h3 { color: #FFFFFF; font-weight: bold; margin-top: 10px; margin-bottom: 5px; }
            h1 { font-size: 16px; }
            h2 { font-size: 14px; }
            h3 { font-size: 13px; }
            code { 
                font-family: Consolas, "Courier New", monospace;
                background-color: rgba(255, 255, 255, 0.08); 
                border-radius: 4px;
                padding: 2px 4px;
                color: #A5D6FF;
            }
            pre {
                font-family: Consolas, "Courier New", monospace;
                background-color: #16161A;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 6px;
                padding: 8px;
                margin-top: 8px;
                margin-bottom: 8px;
            }
            ul, ol { margin-left: 15px; padding-left: 0px; }
            li { color: #E2E8F0; margin-bottom: 2px; }
            a { color: #8A2BE2; text-decoration: none; }
        """)

        # Enable text interaction (copying text)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)

        if text:
            self.set_markdown(text)

        # Connect document resizing to widget height adjustment
        doc.contentsChanged.connect(self._adjust_height)

    def set_markdown(self, text: str) -> None:
        """Render markdown text."""
        # Convert simple triple-backtick markdown blocks to HTML pre tags to ensure proper styling
        processed_text = self._preprocess_code_blocks(text)
        self.setMarkdown(processed_text)
        self._adjust_height()

    def _preprocess_code_blocks(self, text: str) -> str:
        """Replace code blocks with styled versions if needed."""
        # Qt6 setMarkdown() handles backticks well, but we make sure they format cleanly
        return text

    def _adjust_height(self) -> None:
        """Resize widget height dynamically to fit its scroll document height."""
        # This prevents scrollbars inside the bubble itself
        doc_height = self.document().size().height()
        # Add a tiny safety padding
        self.setFixedHeight(int(doc_height) + 8)
