from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class OCREngine(ABC):
    """Abstract interface for OCR engines."""
    
    @abstractmethod
    def extract_text(self, image_path_or_bytes: Any) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Extract text from an image.
        Returns:
            Tuple[str, List[Dict]]: (full_text, list_of_bounding_boxes_with_confidence)
        """
        pass

class EasyOCREngine(OCREngine):
    """EasyOCR implementation."""
    
    def __init__(self, langs: List[str] = ['en']):
        self.langs = langs
        self._reader = None
        
    def _get_reader(self):
        if self._reader is None:
            logger.info("Initializing EasyOCR reader (this may take a moment)...")
            import easyocr
            self._reader = easyocr.Reader(self.langs, gpu=False)  # Using CPU by default for broader compatibility
        return self._reader
        
    def extract_text(self, image_path_or_bytes: Any) -> Tuple[str, List[Dict[str, Any]]]:
        reader = self._get_reader()
        # detail=1 returns (bbox, text, prob)
        results = reader.readtext(image_path_or_bytes, detail=1)
        
        full_text_parts = []
        bboxes = []
        for bbox, text, prob in results:
            full_text_parts.append(text)
            bboxes.append({
                "bbox": bbox,
                "text": text,
                "confidence": prob
            })
            
        full_text = " ".join(full_text_parts)
        return full_text, bboxes
