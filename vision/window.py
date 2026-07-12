from typing import Dict, Any, List, Optional
from pywinauto import Desktop
import pywinauto

class WindowAnalyzer:
    """Understands window properties and hierarchy using UIA."""
    
    def __init__(self):
        # We only use this for read-only analysis
        pass

    def get_active_window(self) -> Optional[Dict[str, Any]]:
        """Return properties of the foreground window."""
        windows = Desktop(backend="uia").windows()
        for w in windows:
            if w.is_active():
                rect = w.rectangle()
                return {
                    "title": w.window_text(),
                    "class_name": w.class_name(),
                    "bbox": (rect.left, rect.top, rect.width(), rect.height()),
                    "is_dialog": w.is_dialog()
                }
        return None

    def list_all_windows(self) -> List[Dict[str, Any]]:
        """List all visible windows with their bounding boxes."""
        windows = Desktop(backend="uia").windows()
        result = []
        for w in windows:
            if w.is_visible() and w.window_text():
                rect = w.rectangle()
                result.append({
                    "title": w.window_text(),
                    "class_name": w.class_name(),
                    "bbox": (rect.left, rect.top, rect.width(), rect.height()),
                    "is_dialog": w.is_dialog()
                })
        return result
