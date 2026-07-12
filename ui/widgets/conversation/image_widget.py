"""
ui/widgets/conversation/image_widget.py — Visual Diagram and OCR Image Widget
=============================================================================
Responsive image widget that presents system diagrams, screenshots, or local figures
with rounded corners and scale-to-fit styling.
"""
from __future__ import annotations

import os
import logging
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame

logger = logging.getLogger(__name__)


class ImageWidget(QFrame):
    """
    Renders pictures, drawings, diagrams, or generated image graphs inside chat flows.
    """

    def __init__(self, file_path_or_data: str) -> None:
        super().__init__()
        self.path = file_path_or_data
        
        self.setObjectName("ImageContainer")
        self.setStyleSheet("""
            #ImageContainer {
                background-color: #16161A;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                padding: 4px;
            }
        """)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Image label displaying QPixmap
        self.lbl_img = QLabel()
        self.lbl_img.setAlignment(Qt.AlignCenter)
        self.lbl_img.setStyleSheet("border-radius: 6px;")

        # Set default size
        self.lbl_img.setMinimumSize(100, 100)

        if os.path.exists(self.path):
            pixmap = QPixmap(self.path)
            if not pixmap.isNull():
                # Scale smoothly to fit widget container bounds
                scaled_pixmap = pixmap.scaled(
                    450, 300,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.lbl_img.setPixmap(scaled_pixmap)
            else:
                self.lbl_img.setText(f"[Invalid Image File: {os.path.basename(self.path)}]")
        else:
            self.lbl_img.setText(f"[Image File Not Found: {os.path.basename(self.path)}]")

        layout.addWidget(self.lbl_img)
