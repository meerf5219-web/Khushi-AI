import time
from typing import Callable, Any, Optional
from PySide6.QtCore import QThread, Signal

class AutomationWorker(QThread):
    """Background worker to execute automation tasks without blocking UI/Brain."""
    
    # Signals
    started_action = Signal(str)
    completed_action = Signal(str, object)  # action_name, result
    failed_action = Signal(str, str)        # action_name, error_msg
    cancelled_action = Signal(str)
    
    started = Signal()
    progress = Signal(int, str)
    finished = Signal(str, object)
    error = Signal(str)

    def __init__(self, action_name: str, func: Callable, *args, **kwargs):
        super().__init__()
        self.action_name = action_name
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self._is_cancelled = False
        
    def cancel(self):
        """Request cancellation (best effort for blocking calls)."""
        self._is_cancelled = True

    def run(self):
        self.started.emit()
        self.started_action.emit(self.action_name)
        if self._is_cancelled:
            self.cancelled_action.emit(self.action_name)
            self.finished.emit(self.action_name, None)
            return
            
        try:
            self.progress.emit(30, f"Executing action {self.action_name}...")
            result = self.func(*self.args, **self.kwargs)
            self.progress.emit(100, f"Completed action {self.action_name}.")
            if self._is_cancelled:
                self.cancelled_action.emit(self.action_name)
                self.finished.emit(self.action_name, None)
            else:
                self.completed_action.emit(self.action_name, result)
                self.finished.emit(self.action_name, result)
        except Exception as e:
            err_msg = str(e)
            self.error.emit(err_msg)
            if self._is_cancelled:
                self.cancelled_action.emit(self.action_name)
            else:
                self.failed_action.emit(self.action_name, err_msg)
