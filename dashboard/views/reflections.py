from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QTextEdit, QLabel
from PySide6.QtCore import Qt

class ReflectionView(QWidget):
    """
    Displays Daily, Weekly, and Monthly reflections from the Companion Memory Engine.
    """
    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        
        self.daily_text = QTextEdit()
        self.daily_text.setReadOnly(True)
        self.tabs.addTab(self.daily_text, "Daily")
        
        self.weekly_text = QTextEdit()
        self.weekly_text.setReadOnly(True)
        self.tabs.addTab(self.weekly_text, "Weekly")
        
        self.monthly_text = QTextEdit()
        self.monthly_text.setReadOnly(True)
        self.tabs.addTab(self.monthly_text, "Monthly")
        
        layout.addWidget(self.tabs)
        self.refresh_data()
        
    def refresh_data(self):
        try:
            import time
            now_text = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            reflection = self.engine.get_reflection(now_text=now_text)
            
            self.daily_text.setPlainText(reflection.get("daily", {}).get("natural_summary", "No daily reflections yet."))
            self.weekly_text.setPlainText(reflection.get("weekly", {}).get("natural_summary", "No weekly reflections yet."))
            self.monthly_text.setPlainText(reflection.get("monthly", {}).get("natural_summary", "No monthly reflections yet."))
        except Exception as e:
            self.daily_text.setPlainText(f"Error loading reflections: {e}")
