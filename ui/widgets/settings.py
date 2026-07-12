"""
ui/widgets/settings.py — Application Settings Panel
=====================================================
Provides inputs for modifying theme, active model, voice speech speed/volume,
continuous listening, privacy settings, and developer mode.
"""
from __future__ import annotations

import logging
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSlider, QCheckBox, QFrame, QLineEdit, QPushButton
)
from version import APP_NAME

logger = logging.getLogger(__name__)


class SettingsWidget(QWidget):
    """
    Control preferences panel styled to match the dark theme.
    """
    settings_changed = Signal(str, object)  # Emits (setting_key, new_value)

    def __init__(self) -> None:
        super().__init__()
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignTop)

        # Title
        title = QLabel("System Settings")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #F8FAFC;")
        layout.addWidget(title)

        # Helper to construct row layouts
        def add_row(label: str, widget: QWidget) -> QHBoxLayout:
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size: 13px; color: #E2E8F0;")
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(widget)
            layout.addLayout(row)
            return row

        # 1. Model selection
        self.combo_model = QComboBox()
        self.combo_model.addItems(["Claude Sonnet 4.6 (Thinking)", "Gemini 3.5 Flash", "Ollama (Local)"])
        self.combo_model.setStyleSheet("QComboBox { background-color: #16161A; border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; padding: 4px 8px; min-width: 150px; }")
        self.combo_model.currentTextChanged.connect(lambda val: self.settings_changed.emit("model", val))
        add_row("Intelligence Model", self.combo_model)

        # 2. Theme selection
        self.combo_theme = QComboBox()
        self.combo_theme.addItems(["Dark (Vision Pro)", "Light (Minimal)", "Glassmorphism"])
        self.combo_theme.setStyleSheet("QComboBox { background-color: #16161A; border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; padding: 4px 8px; min-width: 150px; }")
        self.combo_theme.currentTextChanged.connect(lambda val: self.settings_changed.emit("theme", val))
        add_row("Color Theme", self.combo_theme)

        # 3. Speech speed (WPM)
        self.slide_speed = QSlider(Qt.Horizontal)
        self.slide_speed.setRange(120, 220)
        self.slide_speed.setValue(165)
        self.slide_speed.setFixedWidth(150)
        self.slide_speed.valueChanged.connect(lambda val: self.settings_changed.emit("speech_speed", val))
        add_row("Speech Pacing (WPM)", self.slide_speed)

        # 4. Speech volume
        self.slide_vol = QSlider(Qt.Horizontal)
        self.slide_vol.setRange(0, 100)
        self.slide_vol.setValue(80)
        self.slide_vol.setFixedWidth(150)
        self.slide_vol.valueChanged.connect(lambda val: self.settings_changed.emit("speech_volume", val / 100.0))
        add_row("Voice Volume", self.slide_vol)

        # 5. Continuous Listening Toggle
        self.chk_continuous = QCheckBox()
        self.chk_continuous.setChecked(True)
        self.chk_continuous.stateChanged.connect(lambda state: self.settings_changed.emit("continuous_listening", state == 2))
        add_row("Continuous Listening", self.chk_continuous)

        # 6. Privacy Mode
        self.chk_privacy = QCheckBox()
        self.chk_privacy.setChecked(False)
        self.chk_privacy.stateChanged.connect(lambda state: self.settings_changed.emit("privacy_mode", state == 2))
        add_row("Local Privacy Mode", self.chk_privacy)

        # 7. Developer mode
        self.chk_dev = QCheckBox()
        self.chk_dev.setChecked(False)
        self.chk_dev.stateChanged.connect(lambda state: self.settings_changed.emit("developer_mode", state == 2))
        add_row("Developer Diagnostic Logs", self.chk_dev)

        # Local API Server Info Section
        from api.config import APIConfigManager
        import socket
        
        def get_lan_ip():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                s.close()
                return ip
            except Exception:
                return "127.0.0.1"

        try:
            api_config = APIConfigManager()
            port = api_config.port
            api_key = api_config.api_key
            lan_ip = get_lan_ip()
            local_url = f"http://127.0.0.1:{port}"
            lan_url = f"http://{lan_ip}:{port}"
            pairing_link = f"http://{lan_ip}:{port}?token={api_key}"
        except Exception:
            local_url = "http://127.0.0.1:8000"
            lan_url = "http://127.0.0.1:8000"
            api_key = "Error loading key"
            pairing_link = "Error"

        # Spacer/separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet("background-color: rgba(255,255,255,0.05); margin-top: 10px; margin-bottom: 10px;")
        layout.addWidget(sep)

        # Section Header
        api_title = QLabel("Local & Mobile API Server")
        api_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #A78BFA; margin-bottom: 5px;")
        layout.addWidget(api_title)

        # Local Server URL
        url_lbl = QLabel(f"Local URL: {local_url}")
        url_lbl.setStyleSheet("font-size: 12px; color: #94A3B8;")
        layout.addWidget(url_lbl)

        # LAN Server URL
        lan_lbl = QLabel(f"LAN URL (Mobile): {lan_url}")
        lan_lbl.setStyleSheet("font-size: 12px; color: #94A3B8;")
        layout.addWidget(lan_lbl)

        # API Key Row
        key_lbl = QLineEdit(api_key)
        key_lbl.setReadOnly(True)
        key_lbl.setStyleSheet("QLineEdit { background-color: #16161A; border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; padding: 4px; color: #34D399; font-family: monospace; font-size: 11px; }")
        
        row_key = QHBoxLayout()
        row_key_lbl = QLabel("API Token:")
        row_key_lbl.setStyleSheet("font-size: 12px; color: #E2E8F0;")
        row_key.addWidget(row_key_lbl)
        row_key.addWidget(key_lbl)
        layout.addLayout(row_key)

        # Pairing Link Row
        pair_lbl = QLineEdit(pairing_link)
        pair_lbl.setReadOnly(True)
        pair_lbl.setStyleSheet("QLineEdit { background-color: #16161A; border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; padding: 4px; color: #F59E0B; font-family: monospace; font-size: 10px; }")
        
        row_pair = QHBoxLayout()
        row_pair_lbl = QLabel("Pairing Link:")
        row_pair_lbl.setStyleSheet("font-size: 12px; color: #E2E8F0;")
        row_pair.addWidget(row_pair_lbl)
        row_pair.addWidget(pair_lbl)
        layout.addLayout(row_pair)

        # Spacer/separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setFrameShadow(QFrame.Sunken)
        sep2.setStyleSheet("background-color: rgba(255,255,255,0.05); margin-top: 10px; margin-bottom: 10px;")
        layout.addWidget(sep2)

        # About Dialog Trigger
        about_btn = QPushButton(f"About {APP_NAME}")
        about_btn.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 4px;
                padding: 6px 12px;
                color: #8B5CF6;
                font-weight: bold;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #2D3748;
            }
        """)
        def show_about():
            from ui.widgets.about import AboutDialog
            dialog = AboutDialog(self)
            dialog.exec()
            
        about_btn.clicked.connect(show_about)
        
        row_about = QHBoxLayout()
        row_about.addWidget(about_btn)
        layout.addLayout(row_about)
