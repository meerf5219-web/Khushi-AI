from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen, QColor
from typing import List, Tuple

class OverlayWidget(QWidget):
    """Transparent click-through overlay for rendering bounding boxes."""
    
    def __init__(self):
        super().__init__()
        # Set window flags for transparency, frameless, stay on top, click-through
        self.setWindowFlags(
            Qt.Window |
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.WindowTransparentForInput |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.bboxes: List[Tuple[int, int, int, int]] = []
        
    def show_boxes(self, bboxes: List[Tuple[int, int, int, int]]):
        """Show list of boxes (left, top, width, height)."""
        self.bboxes = bboxes
        # In a real multi-monitor setup, this needs to span the virtual desktop.
        # For prototype, assume it's moved to cover the whole screen.
        self.update()
        self.show()

    def hide_boxes(self):
        """Clear all bounding boxes."""
        self.bboxes = []
        self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        pen = QPen(QColor(255, 0, 0, 200))
        pen.setWidth(3)
        painter.setPen(pen)
        
        for (x, y, w, h) in self.bboxes:
            painter.drawRect(x, y, w, h)
            
        painter.end()
