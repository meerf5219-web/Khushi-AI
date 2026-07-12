"""
ui/widgets/conversation/markdown_renderer.py — Modular Markdown Parser & Visualizer
====================================================================================
Splits raw markdown strings into structured components. Standard text/paragraphs
render as QLabels/QTextBrowser widgets, while tables, code blocks, and diagrams
render as interactive, custom QWidgets.
"""
from __future__ import annotations

import re
import logging
from typing import List, Tuple
from PySide6.QtWidgets import QWidget, QVBoxLayout

from ui.widgets.markdown import MarkdownWidget
from ui.widgets.conversation.code_block_widget import CodeBlockWidget
from ui.widgets.conversation.table_widget import TableWidget
from ui.widgets.conversation.image_widget import ImageWidget

logger = logging.getLogger(__name__)


class MarkdownRenderer:
    """
    Parses complex markdown into a list of styled PySide6 QWidgets.
    """

    def parse_to_layout(self, markdown_text: str, parent_layout: QVBoxLayout) -> None:
        """
        Parse raw markdown text and insert representative widgets into parent_layout.
        """
        # Clear existing layout children
        while parent_layout.count() > 0:
            child = parent_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not markdown_text:
            return

        # Step 1: Split by code blocks (```language ... ```)
        # Using regex to find triple backtick blocks
        parts = re.split(r"(```[a-zA-Z]*\n[\s\S]*?\n```)", markdown_text)
        
        for part in parts:
            part = part.strip()
            if not part:
                continue

            if part.startswith("```"):
                # Extract language and code content
                lines = part.split("\n")
                lang = lines[0].replace("```", "").strip() or "text"
                code = "\n".join(lines[1:-1])
                
                widget = CodeBlockWidget(code, lang)
                parent_layout.addWidget(widget)
            else:
                # Step 2: Parse table blocks and image links from text segment
                self._parse_non_code_block(part, parent_layout)

    def _parse_non_code_block(self, text: str, layout: QVBoxLayout) -> None:
        lines = text.split("\n")
        idx = 0
        text_buffer = []

        while idx < len(lines):
            line = lines[idx].strip()

            # Check if this line starts a table block
            if line.startswith("|") and idx + 1 < len(lines) and re.match(r"^\|\s*[:\-]+\s*\|", lines[idx + 1].strip()):
                # Flush text buffer first
                if text_buffer:
                    layout.addWidget(MarkdownWidget("\n".join(text_buffer)))
                    text_buffer = []

                # Parse table
                table_widget, next_idx = self._parse_table_block(lines, idx)
                if table_widget:
                    layout.addWidget(table_widget)
                idx = next_idx
                continue

            # Check for image block tag: ![alt](path)
            img_match = re.search(r"!\[(.*?)\]\((.*?)\)", line)
            if img_match:
                # Flush text buffer first
                if text_buffer:
                    layout.addWidget(MarkdownWidget("\n".join(text_buffer)))
                    text_buffer = []
                
                # Render image container
                path = img_match.group(2)
                layout.addWidget(ImageWidget(path))
                idx += 1
                continue

            # Standard paragraph line
            text_buffer.append(lines[idx])
            idx += 1

        # Flush remaining text buffer
        if text_buffer:
            layout.addWidget(MarkdownWidget("\n".join(text_buffer)))

    def _parse_table_block(self, lines: List[str], start_idx: int) -> Tuple[Optional[TableWidget], int]:
        """
        Parses consecutive table rows and returns (TableWidget, next_line_index).
        """
        try:
            # Header
            header_row = lines[start_idx]
            headers = [cell.strip() for cell in header_row.split("|")[1:-1]]
            
            # Skip separator line (start_idx + 1)
            idx = start_idx + 2
            rows = []
            
            while idx < len(lines):
                row_line = lines[idx].strip()
                if not row_line.startswith("|"):
                    break
                
                row_cells = [cell.strip() for cell in row_line.split("|")[1:-1]]
                rows.append(row_cells)
                idx += 1
                
            return TableWidget(headers, rows), idx
        except Exception as exc:
            logger.error("Failed to parse table block starting at line %d: %s", start_idx, exc)
            return None, start_idx + 1
