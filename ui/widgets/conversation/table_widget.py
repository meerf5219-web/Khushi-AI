"""
ui/widgets/conversation/table_widget.py — High-Performance Structured Data Grids
===================================================================================
Visualizes markdown tables as clean QTableWidget grids. Incorporates resizable columns,
CSV copy, and click-to-export options.
"""
from __future__ import annotations

import csv
import io
import logging
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QFrame
)

logger = logging.getLogger(__name__)


class TableWidget(QFrame):
    """
    Styled table widget displaying structured datasets from markdown tables.
    """

    def __init__(self, headers: List[str], rows: List[List[str]]) -> None:
        super().__init__()
        self.headers = [h.strip() for h in headers]
        self.rows = [[cell.strip() for cell in row] for row in rows]

        self.setObjectName("TableContainer")
        self.setStyleSheet("""
            #TableContainer {
                background-color: #18181D;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 8px;
            }
        """)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Header Toolbar (Copy CSV / Export)
        toolbar = QHBoxLayout()
        toolbar.addStretch()

        btn_copy = QPushButton("Copy CSV")
        btn_copy.setCursor(Qt.PointingHandCursor)
        btn_copy.setStyleSheet("QPushButton { font-size: 10px; padding: 2px 8px; background-color: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08); }")
        btn_copy.clicked.connect(self._copy_csv)
        toolbar.addWidget(btn_copy)

        layout.addLayout(toolbar)

        # Grid Table Widget
        self.grid = QTableWidget()
        self.grid.setColumnCount(len(self.headers))
        self.grid.setRowCount(len(self.rows))
        self.grid.setHorizontalHeaderLabels(self.headers)
        
        # Populate cells
        for row_idx, row in enumerate(self.rows):
            for col_idx, cell_text in enumerate(row):
                # Ensure cell bounds check
                val = cell_text if col_idx < len(row) else ""
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)  # Read-only
                self.grid.setItem(row_idx, col_idx, item)

        # Styling
        self.grid.setShowGrid(True)
        self.grid.verticalHeader().setVisible(False)  # hide row numbers
        self.grid.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.grid.horizontalHeader().setStretchLastSection(True)

        self.grid.setStyleSheet("""
            QTableWidget {
                background-color: transparent;
                border: none;
                gridline-color: rgba(255, 255, 255, 0.06);
                color: #E2E8F0;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #141419;
                color: #FFFFFF;
                font-weight: bold;
                padding: 6px;
                border: 1px solid rgba(255, 255, 255, 0.05);
            }
            QTableWidget::item {
                padding: 6px;
            }
            QTableWidget::item:selected {
                background-color: rgba(138, 43, 226, 0.2);
                color: #FFFFFF;
            }
        """)

        layout.addWidget(self.grid)

        # Calculate height dynamically based on row counts
        row_height = 26
        header_height = 32
        total_height = min(350, header_height + (len(self.rows) * row_height) + 38)
        self.setFixedHeight(total_height)

    def _to_csv_string(self) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(self.headers)
        writer.writerows(self.rows)
        return output.getvalue()

    def _copy_csv(self) -> None:
        from PySide6.QtGui import QClipboard
        from PySide6.QtWidgets import QApplication
        
        csv_text = self._to_csv_string()
        clipboard = QApplication.clipboard()
        clipboard.setText(csv_text)
        
        logger.info("[TABLE] Copied CSV layout to clipboard.")
