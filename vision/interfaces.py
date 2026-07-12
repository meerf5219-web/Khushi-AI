from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
from PIL import Image

class OCREngine(ABC):
    """Abstract interface for pluggable OCR engines."""
    
    @abstractmethod
    def extract_text(self, image: Image.Image) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Extract text from an image.
        Returns:
            Tuple[str, List[Dict]]: (full_text, list_of_bounding_boxes_with_confidence)
        """
        pass

class UIElementDetector(ABC):
    """Abstract interface for UI Element detection."""
    
    @abstractmethod
    def detect_elements(self, image: Image.Image) -> List[Dict[str, Any]]:
        """
        Detect UI elements from an image (or screen).
        Returns a list of elements with their bounding boxes and types.
        """
        pass
