from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame
from PySide6.QtCore import Qt

class DashboardOverview(QWidget):
    """
    Shows high-level metrics: Active Missions, Memory Usage, Agent Status.
    """
    def __init__(self, brain=None, parent=None):
        super().__init__(parent)
        self.brain = brain
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        
        title = QLabel("<h2>Khushi AI Overview</h2>")
        layout.addWidget(title)
        
        metrics_layout = QHBoxLayout()
        
        self.mem_lbl = self._create_card("Total Memories", "0")
        metrics_layout.addWidget(self.mem_lbl)
        
        self.status_lbl = self._create_card("Agent Status", "Idle")
        metrics_layout.addWidget(self.status_lbl)
        
        self.prediction_lbl = self._create_card("Prediction Confidence", "0%")
        metrics_layout.addWidget(self.prediction_lbl)
        
        layout.addLayout(metrics_layout)
        
        self.refresh_data()
        
    def _create_card(self, title: str, initial_value: str) -> QWidget:
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet("background-color: #1e1e1e; border: 1px solid #333333; border-radius: 8px; padding: 10px;")
        l = QVBoxLayout(card)
        l.addWidget(QLabel(f"<span style='color: #8c9eff;'>{title}</span>"))
        
        val_lbl = QLabel(f"<h2>{initial_value}</h2>")
        l.addWidget(val_lbl)
        
        card.value_label = val_lbl # attach for easy updating
        return card

    def refresh_data(self):
        if not self.brain:
            return
            
        # Try to pull memory stats
        try:
            timeline = self.brain.cie.get_timeline()
            self.mem_lbl.value_label.setText(f"<h2>{len(timeline)}</h2>")
        except:
            pass
