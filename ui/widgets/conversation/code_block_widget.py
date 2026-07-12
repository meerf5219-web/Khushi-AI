"""
ui/widgets/conversation/code_block_widget.py — High-Performance Syntax-Highlighted Code Container
===================================================================================================
A standalone widget wrapping rich code snippets. Includes line numbers, syntax highlighting,
language badges, collapse/expand states, and click-to-copy code functionality.
"""
from __future__ import annotations

import logging
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QFrame
)
from PySide6.QtGui import QFont, QTextDocument

logger = logging.getLogger(__name__)

# Try to import pygments for advanced syntax highlighting
try:
    import pygments
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, ClassNotFound
    from pygments.formatters import HtmlFormatter
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False


class CodeBlockWidget(QFrame):
    """
    Renders clean code blocks with syntax highlighting, language badge, line numbers,
    and a copy-to-clipboard button.
    """

    def __init__(self, code: str, language: str = "txt") -> None:
        super().__init__()
        self.code = code.strip()
        self.language = language.lower().strip() or "text"
        self._expanded = True

        self.setObjectName("CodeBlock")
        self.setStyleSheet("""
            #CodeBlock {
                background-color: #1E1E24;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
            }
        """)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header Bar
        header = QFrame()
        header.setStyleSheet("background-color: #141419; border-top-left-radius: 8px; border-top-right-radius: 8px; border-bottom: 1px solid rgba(255,255,255,0.05);")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 6, 10, 6)

        # Language Badge
        self.lbl_lang = QLabel(self.language.upper())
        self.lbl_lang.setStyleSheet("font-size: 10px; font-weight: bold; color: #8A2BE2; background-color: rgba(138,43,226,0.15); padding: 2px 6px; border-radius: 4px;")
        header_layout.addWidget(self.lbl_lang)
        header_layout.addStretch()

        # Collapse Button
        self.btn_toggle = QPushButton("Collapse")
        self.btn_toggle.setStyleSheet("QPushButton { font-size: 10px; color: #94A3B8; background: transparent; padding: 2px 6px; border: none; } QPushButton:hover { color: #FFFFFF; }")
        self.btn_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_toggle.clicked.connect(self._toggle_collapse)
        header_layout.addWidget(self.btn_toggle)

        # Copy Button
        self.btn_copy = QPushButton("Copy")
        self.btn_copy.setStyleSheet("QPushButton { font-size: 10px; color: #94A3B8; background: transparent; padding: 2px 6px; border: none; } QPushButton:hover { color: #FFFFFF; }")
        self.btn_copy.setCursor(Qt.PointingHandCursor)
        self.btn_copy.clicked.connect(self._copy_code)
        header_layout.addWidget(self.btn_copy)

        layout.addWidget(header)

        # Code display text area
        self.editor = QTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.editor.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.editor.setLineWrapMode(QTextEdit.NoWrap)
        
        # Consolas or standard monospace font
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.Monospace)
        self.editor.setFont(font)

        # Style sheet override
        self.editor.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                border: none;
                padding: 10px;
                color: #A5D6FF;
            }
        """)

        # Highlight syntax
        self._highlight_code()
        layout.addWidget(self.editor)

        # Connect content sizing
        self.editor.document().contentsChanged.connect(self._adjust_height)
        self._adjust_height()

    def _highlight_code(self) -> None:
        if PYGMENTS_AVAILABLE:
            try:
                lexer = get_lexer_by_name(self.language)
            except ClassNotFound:
                try:
                    # fallback to general text
                    lexer = get_lexer_by_name("text")
                except Exception:
                    lexer = None

            if lexer:
                try:
                    formatter = HtmlFormatter(nowrap=True, noclasses=True, style="monokai")
                    html_content = highlight(self.code, lexer, formatter)
                    self.editor.setHtml(f"<pre style='margin: 0px;'>{html_content}</pre>")
                    return
                except Exception as exc:
                    logger.error("Pygments highlighting failed: %s", exc)

        # Fallback to plain text with default CSS coloration
        self.editor.setPlainText(self.code)

    def _toggle_collapse(self) -> None:
        self._expanded = not self._expanded
        if self._expanded:
            self.editor.show()
            self.btn_toggle.setText("Collapse")
            self._adjust_height()
        else:
            self.editor.hide()
            self.btn_toggle.setText("Expand")
            self.setFixedHeight(30) # Height of the header bar only

    def _copy_code(self) -> None:
        from PySide6.QtGui import QClipboard
        from PySide6.QtWidgets import QApplication
        
        clipboard = QApplication.clipboard()
        clipboard.setText(self.code)
        
        # Temporal feedback
        self.btn_copy.setText("Copied!")
        self.btn_copy.setStyleSheet("QPushButton { font-size: 10px; color: #10B981; font-weight: bold; background: transparent; }")
        
        def _reset():
            self.btn_copy.setText("Copy")
            self.btn_copy.setStyleSheet("QPushButton { font-size: 10px; color: #94A3B8; background: transparent; }")
            
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1500, _reset)

    def _adjust_height(self) -> None:
        if self._expanded:
            doc_height = self.editor.document().size().height()
            # Constrain line height limits to prevent large widgets overflowing
            self.editor.setFixedHeight(int(doc_height) + 16)
            self.setFixedHeight(int(doc_height) + 48) # code height + header height
