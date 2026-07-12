import os
import tempfile
import logging
from typing import List, Dict, Any, Tuple
from PIL import Image

from vision.interfaces import OCREngine

logger = logging.getLogger(__name__)

class EasyOCREngine(OCREngine):
    """EasyOCR implementation for Vision OCR."""
    
    def __init__(self, langs: List[str] = None):
        self.langs = langs or ['en']
        self._reader = None
        
    def _get_reader(self):
        if self._reader is None:
            logger.info("[VISION] Initializing EasyOCR reader...")
            import easyocr
            # CPU is preferred for compatibility across various hardware, but we can enable GPU if available.
            self._reader = easyocr.Reader(self.langs, gpu=False)
        return self._reader
        
    def extract_text(self, image: Image.Image) -> Tuple[str, List[Dict[str, Any]]]:
        reader = self._get_reader()
        
        fd, temp_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        
        try:
            image.save(temp_path)
            # detail=1 returns (bbox, text, prob)
            results = reader.readtext(temp_path, detail=1)
            
            full_text_parts = []
            bboxes = []
            for bbox, text, prob in results:
                full_text_parts.append(text)
                bboxes.append({
                    "bbox": bbox, # [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
                    "text": text,
                    "confidence": prob
                })
                
            full_text = " ".join(full_text_parts)
            return full_text, bboxes
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
