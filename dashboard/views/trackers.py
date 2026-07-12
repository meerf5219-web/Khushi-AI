from PySide6.QtWidgets import QWidget, QVBoxLayout, QProgressBar, QLabel, QHBoxLayout, QFrame
from PySide6.QtCore import Qt

class TrackerView(QWidget):
    """
    Displays progress bars for various domains (UPSC, Coding, Gym, Book).
    """
    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        
        self.trackers = {}
        
        # Add basic trackers
        for tracker_name in ["UPSC Syllabus", "Coding Projects", "Gym Routine", "Books Read"]:
            self._add_tracker(layout, tracker_name)
            
        self.refresh_data()
        
    def _add_tracker(self, parent_layout, name):
        frame = QFrame()
        frame.setStyleSheet("background-color: #1e1e1e; border: 1px solid #333333; border-radius: 6px; padding: 5px;")
        l = QVBoxLayout(frame)
        
        header = QHBoxLayout()
        header.addWidget(QLabel(f"<b>{name}</b>"))
        val_lbl = QLabel("0%")
        header.addWidget(val_lbl, alignment=Qt.AlignRight)
        
        l.addLayout(header)
        
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(0)
        bar.setTextVisible(False)
        l.addWidget(bar)
        
        self.trackers[name] = {"bar": bar, "lbl": val_lbl}
        parent_layout.addWidget(frame)
        
    def refresh_data(self):
        # In a real app, we'd query `engine.get_profile()` or `goals` section
        # For now, we will simulate a mock value since the backend NLP generates dynamic progress
        try:
            profile = self.engine.get_profile()
            # If the user has specific quantitative goals in profile, parse them
            pass
        except:
            pass
