import pyautogui
from typing import Optional, Tuple, List, Dict, Any
from automation.ocr_engine import EasyOCREngine, OCREngine
from PIL import Image

class OCRAutomation:
    """Manages screenshot and OCR operations."""
    
    def __init__(self, engine: Optional[OCREngine] = None):
        # Default to EasyOCR if none provided
        self.engine = engine or EasyOCREngine()
        
    def capture_screen(self, region: Optional[Tuple[int, int, int, int]] = None) -> Image.Image:
        """
        Capture the screen.
        region is (left, top, width, height)
        """
        return pyautogui.screenshot(region=region)
        
    def extract_text(self, region: Optional[Tuple[int, int, int, int]] = None) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Capture screen (or region) and extract text.
        Returns:
            (full_text, bounding_boxes_with_confidence)
        """
        image = self.capture_screen(region)
        
        # Save image temporarily to pass to EasyOCR
        import tempfile
        import os
        
        fd, temp_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        
        try:
            image.save(temp_path)
            return self.engine.extract_text(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
