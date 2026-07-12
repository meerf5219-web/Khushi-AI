from typing import Dict, Any, Optional
from vision.capture import ScreenCapture
from vision.ocr import EasyOCREngine
from vision.detector import OpenCVDetector
from vision.window import WindowAnalyzer

class VisionAnalyzer:
    """Orchestrates capture, OCR, and element detection to build a semantic screen representation."""
    
    def __init__(self):
        self.capture = ScreenCapture()
        self.ocr = EasyOCREngine()
        self.detector = OpenCVDetector()
        self.window = WindowAnalyzer()
        
    def analyze_active_window(self) -> Dict[str, Any]:
        """Capture the foreground window and extract text and elements."""
        active_win = self.window.get_active_window()
        if not active_win:
            return {"error": "No active window found."}
            
        region = active_win["bbox"] # (left, top, width, height)
        image = self.capture.capture_region(region)
        
        full_text, bboxes = self.ocr.extract_text(image)
        elements = self.detector.detect_elements(image)
        
        return {
            "window_title": active_win["title"],
            "window_class": active_win["class_name"],
            "text": full_text,
            "ocr_bboxes": bboxes,
            "elements": elements
        }
        
    def summarize_screen(self) -> str:
        """Helper for LLM intents: Returns a structured text summary of the screen."""
        data = self.analyze_active_window()
        if "error" in data:
            return data["error"]
            
        summary = f"Foreground Application: {data['window_title']}\n"
        summary += f"Extracted Text:\n{data['text']}\n"
        return summary
