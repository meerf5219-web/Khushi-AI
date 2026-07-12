import cv2
import numpy as np
from PIL import Image
from typing import List, Dict, Any
from vision.interfaces import UIElementDetector

class OpenCVDetector(UIElementDetector):
    """Detects UI elements and visual patterns using OpenCV template matching."""
    
    def detect_elements(self, image: Image.Image) -> List[Dict[str, Any]]:
        # In a full implementation, this might run contours or YOLO.
        # For now, it provides the skeleton.
        return []

    def visual_search(self, image: Image.Image, template_path: str, threshold: float = 0.8) -> List[Dict[str, int]]:
        """
        Search for a visual template inside the given image.
        Returns a list of bounding boxes (left, top, width, height).
        """
        img_gray = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2GRAY)
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        
        if template is None:
            raise FileNotFoundError(f"Template image not found: {template_path}")
            
        w, h = template.shape[::-1]
        
        res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        
        results = []
        for pt in zip(*loc[::-1]):
            results.append({
                "left": int(pt[0]),
                "top": int(pt[1]),
                "width": int(w),
                "height": int(h)
            })
            
        return results
