import time
from typing import Dict, Any, Callable, Optional, List, Tuple
from PySide6.QtCore import QObject
from PIL import Image

from brain.event_bus import event_bus
from vision.workers import VisionWorker
from vision.capture import ScreenCapture
from vision.ocr import EasyOCREngine
from vision.detector import OpenCVDetector
from vision.window import WindowAnalyzer
from vision.analyzer import VisionAnalyzer
from vision.history import HistoryManager
from vision.overlay import OverlayWidget

class VisionController(QObject):
    """
    Single public API for the Computer Vision & Screen Intelligence Layer.
    All vision logic must be accessed through this controller.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.capture = ScreenCapture()
        self.ocr = EasyOCREngine()
        self.detector = OpenCVDetector()
        self.window = WindowAnalyzer()
        self.analyzer = VisionAnalyzer()
        self.history = HistoryManager()
        
        self.overlay = None # Lazy initialized if needed in UI thread
        self.privacy_mode = True # Safe by default
        self._active_workers: Dict[str, VisionWorker] = {}
        
    def _publish(self, topic: str, data: Dict[str, Any]):
        """Publish events to EventBus."""
        event_bus.publish('vision', {"topic": topic, "data": data})
        
    def _execute_async(self, action_name: str, func: Callable, *args, **kwargs) -> str:
        """Run a vision task in the background."""
        worker_id = f"{action_name}_{time.time()}"
        worker = VisionWorker(action_name, func, *args, **kwargs)
        self._active_workers[worker_id] = worker
        
        def on_started(name):
            pass
            
        def on_completed(name, result):
            self._publish(f"{name.upper()}_COMPLETED", {"result": result})
            self._cleanup_worker(worker_id)
            
        def on_failed(name, error_msg):
            self._publish(f"{name.upper()}_FAILED", {"error": error_msg})
            self._cleanup_worker(worker_id)
            
        worker.started_action.connect(on_started)
        worker.completed_action.connect(on_completed)
        worker.failed_action.connect(on_failed)
        worker.start()
        
        return worker_id
        
    def _cleanup_worker(self, worker_id: str):
        if worker_id in self._active_workers:
            self._active_workers[worker_id].deleteLater()
            del self._active_workers[worker_id]
            
    # --- Public API ---

    def analyze_active_window(self) -> str:
        """Async capture and OCR of foreground window."""
        if self.privacy_mode:
            return "Vision capture blocked due to Privacy Mode."
        self._publish("SCREEN_CAPTURED", {"target": "active_window"})
        return self._execute_async("vision_analysis", self.analyzer.analyze_active_window)

    def summarize_screen(self) -> str:
        """Async semantic summary of the active window."""
        if self.privacy_mode:
            return "Vision capture blocked due to Privacy Mode."
        self._publish("SCREEN_CAPTURED", {"target": "summarize"})
        return self._execute_async("vision_summary", self.analyzer.summarize_screen)
        
    def show_overlay(self, bboxes: List[Tuple[int, int, int, int]]):
        """Render highlights on the physical screen. Must run on main thread."""
        if self.overlay is None:
            self.overlay = OverlayWidget()
        self.overlay.show_boxes(bboxes)
        
    def hide_overlay(self):
        """Hide all screen highlights."""
        if self.overlay:
            self.overlay.hide_boxes()

    def enable_continuous_capture(self, interval_sec: int = 60, retention_hours: int = 24):
        """Enable timestamped screenshots."""
        self.privacy_mode = False
        self.history.interval = interval_sec
        self.history.retention_hours = retention_hours
        if not self.history.is_running:
            self.history.start()
            self._publish("VISION_HISTORY_STARTED", {"interval": interval_sec})
            
    def disable_continuous_capture(self):
        """Disable timestamped screenshots and enforce privacy."""
        self.privacy_mode = True
        if self.history.is_running:
            self.history.stop()
            self._publish("VISION_HISTORY_STOPPED", {})

# Singleton for router use
vision_controller = VisionController()
