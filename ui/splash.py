"""
ui/splash.py — Application Splash Screen Widget
=================================================
Visual frameless splash window showing stages of Brain model / voice initialization.
"""
from __future__ import annotations

import logging
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QLinearGradient, QColor, QPainter, QBrush, QPen
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QFrame

logger = logging.getLogger(__name__)


class SplashWindow(QWidget):
    """
    Centred loading window shown while SentenceTransformer and subsystems initialize.
    """

    def __init__(self) -> None:
        super().__init__()
        # Frameless window, stays on top during startup
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        self.setFixedSize(450, 300)
        self._init_ui()

    def _init_ui(self) -> None:
        # Background frame for styling
        background = QFrame(self)
        background.setObjectName("SplashBackground")
        background.setGeometry(0, 0, 450, 300)
        background.setStyleSheet("""
            #SplashBackground {
                background-color: #0F0F11;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
            }
        """)

        layout = QVBoxLayout(background)
        layout.setContentsMargins(30, 40, 30, 40)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignCenter)

        from version import APP_NAME, APP_VERSION, GENERATION
        
        # Pulse logo orb at top
        self.logo = QLabel("🌀")
        self.logo.setStyleSheet("font-size: 54px; margin-bottom: 10px;")
        self.logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.logo)

        # Title
        title = QLabel(APP_NAME)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFFFFF;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel(f"{APP_NAME} | {GENERATION} | Version {APP_VERSION}\nDesktop AI Companion")
        subtitle.setStyleSheet("font-size: 11px; color: #94A3B8; margin-bottom: 20px;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255, 255, 255, 0.06);
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #8A2BE2;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress)

        # Status text showing loading stage details
        self.lbl_status = QLabel("Initializing companion intelligence...")
        self.lbl_status.setStyleSheet("font-size: 11px; color: #64748B;")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_status)
        
        # Module text
        self.lbl_module = QLabel("Module: Core")
        self.lbl_module.setStyleSheet("font-size: 10px; color: #475569;")
        self.lbl_module.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_module)

    def update_progress(self, percent: int, message: str, module_name: str = "") -> None:
        """Receive state increments from LoadingWorker."""
        self.progress.setValue(percent)
        self.lbl_status.setText(message)
        if module_name:
            self.lbl_module.setText(f"Module: {module_name}")
            
        logger.info("[SPLASH] Progress %d%% — %s — [%s]", percent, message, module_name)
        
        # Subtle font updates on loading animation
        if percent == 100:
            self.lbl_status.setStyleSheet("font-size: 11px; color: #10B981; font-weight: bold;")
        self.update()

