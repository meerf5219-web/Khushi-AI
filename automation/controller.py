import time
from typing import Dict, Any, Callable, Optional, Tuple
from PySide6.QtCore import QObject

from automation.models import RiskLevel
from automation.utils import publish_event
from automation.workers import AutomationWorker

from automation.window_manager import WindowManager
from automation.mouse import MouseAutomation
from automation.keyboard import KeyboardAutomation
from automation.filesystem import FileSystemAutomation
from automation.system import SystemAutomation
from automation.ocr import OCRAutomation

class AutomationController(QObject):
    """
    Single public API for the Desktop Automation Layer.
    All automation logic must be accessed through this controller.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = WindowManager()
        self.mouse = MouseAutomation()
        self.keyboard = KeyboardAutomation()
        self.fs = FileSystemAutomation()
        self.system = SystemAutomation()
        self.ocr = OCRAutomation()
        
        self._active_workers: Dict[str, AutomationWorker] = {}
        
    def execute(self, action_id: str, action_name: str, risk_level: RiskLevel, func: Callable, *args, **kwargs) -> str:
        """
        Execute an automation function in a background worker.
        Returns the action_id to allow cancellation or tracking.
        """
        worker = AutomationWorker(action_name, func, *args, **kwargs)
        self._active_workers[action_id] = worker
        
        start_time = time.time()
        
        def on_started(name):
            publish_event(name, "Started", risk_level, {"args": args, "kwargs": kwargs})
            
        def on_completed(name, result):
            duration = (time.time() - start_time) * 1000
            publish_event(name, "Completed", risk_level, {"result": result}, duration_ms=duration)
            self._cleanup_worker(action_id)
            
        def on_failed(name, error_msg):
            duration = (time.time() - start_time) * 1000
            publish_event(name, "Failed", risk_level, {}, error=error_msg, duration_ms=duration)
            self._cleanup_worker(action_id)
            
        def on_cancelled(name):
            duration = (time.time() - start_time) * 1000
            publish_event(name, "Cancelled", risk_level, {}, duration_ms=duration)
            self._cleanup_worker(action_id)
            
        worker.started_action.connect(on_started)
        worker.completed_action.connect(on_completed)
        worker.failed_action.connect(on_failed)
        worker.cancelled_action.connect(on_cancelled)
        
        worker.start()
        return action_id
        
    def cancel(self, action_id: str) -> bool:
        """Attempt to cancel a running action."""
        if action_id in self._active_workers:
            self._active_workers[action_id].cancel()
            return True
        return False
        
    def _cleanup_worker(self, action_id: str):
        if action_id in self._active_workers:
            self._active_workers[action_id].deleteLater()
            del self._active_workers[action_id]

# Singleton instance for router use
automation_controller = AutomationController()
