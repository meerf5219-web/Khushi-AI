"""
ui/widgets/sidebar.py — Left Navigation Sidebar
=================================================
Contains navigation triggers for Chat, Memory, Knowledge, Projects, Goals,
Timeline, Plugins, Files, Settings, System, Developer views.
Uses smooth QPropertyAnimation for subtle hover expansions.
"""
from __future__ import annotations

import logging
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolButton, QLabel, QFrame

logger = logging.getLogger(__name__)


class SidebarWidget(QWidget):
    """
    Sleek navigation sidebar with icons representing Khushi's modular panels.
    """
    view_changed = Signal(str)  # Emits the target view identifier on click

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("SidebarContainer")
        self.setFixedWidth(70)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        # Logo at top
        logo = QLabel("🌀")
        logo.setStyleSheet("font-size: 28px; margin-bottom: 20px;")
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

        # Sidebar navigation configuration (unicode representation, internal name, tooltip)
        items = [
            ("💬", "chat", "Conversation"),
            ("🧠", "memory", "Personal Memory"),
            ("📚", "knowledge", "Knowledge Base"),
            ("🛠️", "projects", "Projects Planner"),
            ("🎯", "goals", "Active Goals"),
            ("📅", "timeline", "Life Timeline"),
            ("🔌", "plugins", "Subsystems"),
            ("📁", "files", "File Manager"),
            ("🖥️", "system", "System Telemetry"),
            ("⚙️", "settings", "Preferences"),
        ]

        self.buttons: dict[str, QToolButton] = {}

        for emoji, name, tooltip in items:
            btn = QToolButton()
            btn.setText(emoji)
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            btn.setIconSize(QSize(24, 24))
            btn.setCursor(Qt.PointingHandCursor)
            
            # Match stylesheet formatting
            btn.setStyleSheet("""
                QToolButton {
                    font-size: 20px;
                    border-radius: 8px;
                    padding: 8px;
                    background-color: transparent;
                }
                QToolButton:hover {
                    background-color: rgba(255, 255, 255, 0.08);
                }
                QToolButton:checked {
                    background-color: rgba(255, 255, 255, 0.15);
                    border-left: 3px solid #8A2BE2;
                }
            """)
            
            # Bind events
            btn.clicked.connect(lambda checked, n=name: self._on_clicked(n))
            layout.addWidget(btn)
            self.buttons[name] = btn

        # Default select Chat
        if self.buttons:
            self.buttons["chat"].setChecked(True)

    def _on_clicked(self, active_name: str) -> None:
        # Guarantee mutual exclusion manually
        for name, btn in self.buttons.items():
            btn.setChecked(name == active_name)
        
        logger.info("[SIDEBAR] Switched view to: %s", active_name)
        self.view_changed.emit(active_name)
