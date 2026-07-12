import time
from typing import List, Dict, Any
from pywinauto import Desktop, Application
from automation.models import RiskLevel

class WindowManager:
    """Manages application windows on the desktop (Windows-only)."""
    
    def list_windows(self) -> List[Dict[str, Any]]:
        """List all visible windows."""
        windows = Desktop(backend="uia").windows()
        result = []
        for w in windows:
            if w.window_text():
                result.append({
                    "title": w.window_text(),
                    "handle": w.handle,
                    "class_name": w.class_name()
                })
        return result

    def open_app(self, path: str) -> None:
        """Launch an application."""
        app = Application(backend="uia").start(path)
        
    def close_window(self, title: str) -> None:
        """Close a window by title."""
        app = Application(backend="uia").connect(title_re=f".*{title}.*", timeout=3)
        app.top_window().close()
        
    def focus_window(self, title: str) -> None:
        """Bring a window to the foreground."""
        app = Application(backend="uia").connect(title_re=f".*{title}.*", timeout=3)
        app.top_window().set_focus()

    def minimize_window(self, title: str) -> None:
        """Minimize a window."""
        app = Application(backend="uia").connect(title_re=f".*{title}.*", timeout=3)
        app.top_window().minimize()

    def maximize_window(self, title: str) -> None:
        """Maximize a window."""
        app = Application(backend="uia").connect(title_re=f".*{title}.*", timeout=3)
        app.top_window().maximize()
        
    def restore_window(self, title: str) -> None:
        """Restore a minimized window."""
        app = Application(backend="uia").connect(title_re=f".*{title}.*", timeout=3)
        app.top_window().restore()
