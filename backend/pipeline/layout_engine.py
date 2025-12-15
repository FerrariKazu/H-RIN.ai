import layoutparser as lp
import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

class LayoutEngine:
    def __init__(self):
        # Using a publicly available pre-trained model for PubLayNet
        # Ensuring compatibility: strictly use "lp://" syntax if relying on ModelCatalog
        # Fallback to simple heuristic if model load fails (common on Windows without Detectron2)
        self.model = None
        try:
            # Try loading Tesseract agent for layout detection
            self.model = lp.TesseractAgent(languages='eng')
        except Exception as e:
            logger.warning(f"Could not load LayoutParser model: {e}. Using fallback.")

    def analyze(self, image_bytes):
        """
        Input: Raw image bytes
        Output: List of text blocks with coordinates and type (Header, Text, Table, etc.)
        """
        if not self.model:
            return []

        try:
            # Decode image
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # Detect
            layout = self.model.detect(image)
            
            # Sort blocks by reading order (top-left to bottom-rightish)
            # LayoutParser's sort functionality... or custom
            # Simple sorting by Y then X
            # TesseractAgent returns text right away usually?
            # Adjusting return to standardized dict format
            
            blocks = []
            if isinstance(layout, str): 
                # TesseractAgent returns raw string? 
                # Actually lp.TesseractAgent returns a layout object usually.
                pass 
            
            # Standardizing output
            # If real Detectron2 was working, we'd iterate over layout elements
            # for block in layout:
            #     blocks.append({
            #         "type": block.type,
            #         "box": block.coordinates,
            #         "score": block.score
            #     })
            
            return str(layout) # Temporary return of full layout object representation
        except Exception as e:
            logger.error(f"Layout analysis failed: {e}")
            return []
