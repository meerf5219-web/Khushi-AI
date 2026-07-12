import time
import ctypes
import logging

logger = logging.getLogger(__name__)

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint),
                ("dwTime", ctypes.c_uint)]

class IdleMonitor:
    """
    Monitors system-wide user activity (mouse, keyboard) to determine idle states.
    Uses Win32 API.
    """
    def __init__(self):
        self.lastInputInfo = LASTINPUTINFO()
        self.lastInputInfo.cbSize = ctypes.sizeof(self.lastInputInfo)
        
    def get_idle_duration(self) -> float:
        """Returns the number of seconds since the last user input."""
        try:
            ctypes.windll.user32.GetLastInputInfo(ctypes.byref(self.lastInputInfo))
            millis = ctypes.windll.kernel32.GetTickCount() - self.lastInputInfo.dwTime
            return millis / 1000.0
        except Exception as e:
            logger.debug(f"Could not retrieve idle time: {e}")
            return 0.0

class ProductivityScorer:
    """
    Looks at the active foreground window to determine if the user is working or idle/distracted.
    """
    def __init__(self):
        self.productive_titles = ["vscode", "github", "pycharm", "upsc", "study", "docs"]
        
    def is_productive_active(self, window_title: str) -> bool:
        title_lower = window_title.lower()
        for p in self.productive_titles:
            if p in title_lower:
                return True
        return False
