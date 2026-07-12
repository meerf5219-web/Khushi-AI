import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFormLayout
from PySide6.QtGui import QFont
from version import get_about_info, APP_NAME

class AboutDialog(QDialog):
    """
    Beautiful dynamic About Dialog for Khushi AI.
    Queries the version.py single source of truth to avoid hardcoded metadata.
    """
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_NAME}")
        self.setFixedSize(400, 380)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        
        self.setStyleSheet("""
            QDialog { background-color: #0B0F19; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; }
            QLabel { color: #E2E8F0; font-family: 'Segoe UI', Arial; }
            QPushButton { background-color: #8B5CF6; color: #fff; border: none; border-radius: 4px; padding: 6px 16px; font-weight: bold; }
            QPushButton:hover { background-color: #7C3AED; }
        """)
        
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        # Header logo and name
        header = QHBoxLayout()
        logo = QLabel("🌀")
        logo.setStyleSheet("font-size: 36px;")
        header.addWidget(logo)
        
        title_layout = QVBoxLayout()
        title = QLabel(APP_NAME)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #8B5CF6;")
        subtitle = QLabel("Desktop AI Companion")
        subtitle.setStyleSheet("font-size: 11px; color: #94A3B8;")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        
        header.addLayout(title_layout)
        header.addStretch()
        layout.addLayout(header)
        
        # Details grid
        info = get_about_info()
        
        details = QFormLayout()
        details.setSpacing(8)
        details.setLabelAlignment(Qt.AlignRight)
        
        def add_detail(label: str, val: str):
            lbl_key = QLabel(f"{label}:")
            lbl_key.setStyleSheet("font-weight: bold; color: #94A3B8; font-size: 12px;")
            lbl_val = QLabel(val)
            lbl_val.setStyleSheet("color: #F1F5F9; font-size: 12px;")
            details.addRow(lbl_key, lbl_val)

        add_detail("Current Version", info["Version"])
        add_detail("Current Generation", info["Generation"])
        add_detail("Release Name", info["ReleaseName"])
        add_detail("Python Version", info["PythonVersion"])
        add_detail("Git Commit", info["GitCommit"])
        add_detail("Build Date", info["BuildDate"])
        add_detail("Architecture", info["Architecture"])
        add_detail("Installer Version", info["InstallerVersion"])
        
        layout.addLayout(details)
        layout.addStretch()
        
        # Footer Close Button
        footer = QHBoxLayout()
        footer.addStretch()
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        footer.addWidget(btn_close)
        
        layout.addLayout(footer)
