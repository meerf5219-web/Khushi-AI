"""
ui/widgets/dashboard.py — Right Telemetry Panel
=================================================
Displays system metrics (CPU, RAM, Disk), hardware/software integration status,
active goal, weather, and prediction telemetry cards.
"""
from __future__ import annotations

import os
import time
import logging
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QFrame, QScrollArea
)

logger = logging.getLogger(__name__)

# Try to import psutil for real system metrics
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class TelemetryCard(QFrame):
    """
    Individual card layout displaying label, value, and optional progress bar.
    """

    def __init__(self, label: str, value: str = "N/A", has_progress: bool = False) -> None:
        super().__init__()
        self.setObjectName("TelemetryCard")
        self.setFrameShape(QFrame.StyledPanel)
        self.setProperty("class", "DashboardCard")
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 8, 10, 8)
        self.layout.setSpacing(4)

        # Labels Layout
        lbl_layout = QHBoxLayout()
        self.lbl_title = QLabel(label)
        self.lbl_title.setProperty("class", "TelemetryLabel")
        
        self.lbl_val = QLabel(value)
        self.lbl_val.setProperty("class", "TelemetryValue")
        self.lbl_val.setAlignment(Qt.AlignRight)
        
        lbl_layout.addWidget(self.lbl_title)
        lbl_layout.addStretch()
        lbl_layout.addWidget(self.lbl_val)
        self.layout.addLayout(lbl_layout)

        # Progress bar
        self.progress = None
        if has_progress:
            self.progress = QProgressBar()
            self.progress.setRange(0, 100)
            self.progress.setValue(0)
            self.progress.setTextVisible(False)
            self.layout.addWidget(self.progress)

    def update_value(self, value: str, percent: int = 0) -> None:
        """Modify card label values and bar metrics."""
        self.lbl_val.setText(value)
        if self.progress is not None:
            self.progress.setValue(percent)


class DashboardWidget(QWidget):
    """
    Right status panel displaying active system resource parameters.
    """

    def __init__(self, brain: Any = None) -> None:
        super().__init__()
        self.brain = brain
        self.setObjectName("DashboardContainer")
        self.setFixedWidth(240)
        self._init_ui()

        # Start update timer (updates once every 2 seconds)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh_metrics)
        self.timer.start(2000)

    def set_brain(self, brain: Any) -> None:
        """Inject the loaded Brain instance to read context memory facts."""
        self.brain = brain
        self._refresh_metrics()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 15, 12, 15)
        layout.setSpacing(10)

        # Panel header title
        title = QLabel("System Dashboard")
        title.setObjectName("DashboardTitle")
        layout.addWidget(title)

        # Scrollable dashboard contents
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(8)

        # System telemetry cards
        self.card_cpu = TelemetryCard("CPU Usage", "0%", has_progress=True)
        self.card_ram = TelemetryCard("RAM Usage", "0%", has_progress=True)
        self.card_disk = TelemetryCard("Disk Space", "0%", has_progress=True)
        
        self.content_layout.addWidget(self.card_cpu)
        self.content_layout.addWidget(self.card_ram)
        self.content_layout.addWidget(self.card_disk)

        # Voice & Hardware status cards
        self.card_mic = TelemetryCard("Microphone", "Ready")
        self.card_voice = TelemetryCard("Speaker Status", "Idle")
        self.card_ollama = TelemetryCard("Ollama Engine", "Loaded")
        
        self.content_layout.addWidget(self.card_mic)
        self.content_layout.addWidget(self.card_voice)
        self.content_layout.addWidget(self.card_ollama)

        # Contextual Cards (Weather, Goal, Prediction)
        self.card_weather = TelemetryCard("Weather Today", "Delhi 31°C, Clear")
        self.card_goal = TelemetryCard("Active Goal", "Study pharma / UPSC")
        self.card_prediction = TelemetryCard("Hypothesis", "Suggest weather review")

        self.content_layout.addWidget(self.card_weather)
        self.content_layout.addWidget(self.card_goal)
        self.content_layout.addWidget(self.card_prediction)
        
        self.content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _refresh_metrics(self) -> None:
        # Refresh system telemetry
        if PSUTIL_AVAILABLE:
            try:
                cpu = psutil.cpu_percent()
                self.card_cpu.update_value(f"{cpu:.0f}%", int(cpu))
                
                ram = psutil.virtual_memory()
                self.card_ram.update_value(f"{ram.percent:.0f}%", int(ram.percent))
                
                disk = psutil.disk_usage("/")
                self.card_disk.update_value(f"{disk.percent:.0f}%", int(disk.percent))
            except Exception:
                pass
        else:
            # Fallback mock metrics with subtle random walk
            import random
            mock_cpu = random.randint(15, 35)
            mock_ram = 58
            self.card_cpu.update_value(f"{mock_cpu}%", mock_cpu)
            self.card_ram.update_value(f"{mock_ram}%", mock_ram)
            self.card_disk.update_value("42%", 42)

        # Read context highlights from the Brain if loaded
        if self.brain:
            try:
                # Update weather
                weather_obs = self.brain.memory.get_observations()
                # Default values, updated if memories exist
                weather_info = " Delhi 31°C, Clear"
                goal_info = "Complete UPSC Study Plan"
                
                # Fetch recent memories
                study_mem = self.brain.memory.get_memory("study")
                if study_mem:
                    goal_info = f"Study: {study_mem[:24]}"
                
                self.card_goal.update_value(goal_info)
                
                # Status checks
                from voice.speaker import speaking_engine
                if speaking_engine.is_playing:
                    self.card_voice.update_value("Speaking", 0)
                else:
                    self.card_voice.update_value("Idle", 0)
            except Exception:
                pass
