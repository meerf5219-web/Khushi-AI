import os
import time
from typing import Optional
from PySide6.QtCore import QThread, Signal
from utils.resource_manager import RM
from vision.capture import ScreenCapture

class HistoryManager(QThread):
    """Background loop for timestamped screenshot history."""
    
    saved_screenshot = Signal(str) # file_path
    
    def __init__(self, interval_seconds: int = 60, retention_hours: int = 24):
        super().__init__()
        self.interval = interval_seconds
        self.retention_hours = retention_hours
        self.is_running = False
        self.history_dir = RM.logs().parent / "vision_history"
        os.makedirs(self.history_dir, exist_ok=True)
        self.capture = ScreenCapture()
        
    def run(self):
        self.is_running = True
        while self.is_running:
            try:
                self._purge_old_screenshots()
                self._save_screenshot()
            except Exception as e:
                # Log silently
                pass
            time.sleep(self.interval)
            
    def stop(self):
        self.is_running = False
        
    def _save_screenshot(self):
        filename = time.strftime("%Y%m%d_%H%M%S") + ".png"
        filepath = os.path.join(self.history_dir, filename)
        img = self.capture.capture_full_desktop()
        img.save(filepath)
        self.saved_screenshot.emit(filepath)
        
    def _purge_old_screenshots(self):
        now = time.time()
        cutoff = now - (self.retention_hours * 3600)
        for f in os.listdir(self.history_dir):
            path = os.path.join(self.history_dir, f)
            if os.path.isfile(path):
                if os.path.getmtime(path) < cutoff:
                    try:
                        os.remove(path)
                    except:
                        pass
