import time
from typing import Callable, Any, Optional, Dict
from PySide6.QtCore import QThread, Signal

class VisionWorker(QThread):
    """Background worker for vision tasks (OCR, capture, detect) without blocking."""
    
    started_action = Signal(str)
    completed_action = Signal(str, object)  # action_name, result
    failed_action = Signal(str, str)        # action_name, error_msg

    def __init__(self, action_name: str, func: Callable, *args, **kwargs):
        super().__init__()
        self.action_name = action_name
        self.func = func
        self.args = args
        self.kwargs = kwargs
        
    def run(self):
        self.started_action.emit(self.action_name)
        try:
            result = self.func(*self.args, **self.kwargs)
            self.completed_action.emit(self.action_name, result)
        except Exception as e:
            self.failed_action.emit(self.action_name, str(e))
