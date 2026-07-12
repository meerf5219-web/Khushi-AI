from typing import Callable, Any
from PySide6.QtCore import QThread, Signal
import traceback

class VoiceWorker(QThread):
    """Background worker for voice companion tasks."""
    
    started_action = Signal(str)
    completed_action = Signal(str, object)
    failed_action = Signal(str, str)
    interrupted_action = Signal(str)

    def __init__(self, action_name: str, func: Callable, *args, **kwargs):
        super().__init__()
        self.action_name = action_name
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self._is_cancelled = False
        
    def cancel(self):
        self._is_cancelled = True
        
    def run(self):
        self.started_action.emit(self.action_name)
        try:
            # We pass a callback `check_cancelled` if the function supports it
            if 'check_cancelled' in self.kwargs:
                self.kwargs['check_cancelled'] = lambda: self._is_cancelled
                
            result = self.func(*self.args, **self.kwargs)
            
            if self._is_cancelled:
                self.interrupted_action.emit(self.action_name)
            else:
                self.completed_action.emit(self.action_name, result)
        except Exception as e:
            trace = traceback.format_exc()
            self.failed_action.emit(self.action_name, f"{e}\n{trace}")
