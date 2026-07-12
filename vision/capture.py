from typing import Optional, Tuple, Dict, Any, List
import mss
from PIL import Image

class ScreenCapture:
    """Handles multi-monitor screen capture using mss."""
    
    def __init__(self):
        self.sct = mss.mss()
        
    def get_monitors(self) -> List[Dict[str, int]]:
        """Return dimensions of all monitors. The first monitor in the list is the 'All Monitors' virtual display."""
        return self.sct.monitors
        
    def capture_full_desktop(self) -> Image.Image:
        """Capture the entire virtual desktop spanning all monitors."""
        monitor = self.sct.monitors[0]
        sct_img = self.sct.grab(monitor)
        return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        
    def capture_monitor(self, monitor_index: int = 1) -> Image.Image:
        """Capture a specific monitor (1-indexed)."""
        monitor = self.sct.monitors[monitor_index]
        sct_img = self.sct.grab(monitor)
        return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        
    def capture_region(self, region: Tuple[int, int, int, int]) -> Image.Image:
        """
        Capture a specific region of the screen.
        region: (left, top, width, height)
        """
        left, top, width, height = region
        bbox = {"left": left, "top": top, "width": width, "height": height}
        sct_img = self.sct.grab(bbox)
        return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
