import cv2
import numpy as np
import pytesseract
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

# Configure Tesseract path if needed (Windows often needs this)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class OCREngine:
    def __init__(self):
        pass

    def process_image(self, image_bytes):
        """
        Takes raw image bytes, pre-processes with OpenCV, and runs Tesseract.
        """
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # 1. Preprocessing
        processed_img = self._preprocess(img)
        
        # 2. OCR
        # Assume English for now, can extend to multi-lang
        text = pytesseract.image_to_string(processed_img, lang='eng')
        
        # 3. Confidence check (simple)
        data = pytesseract.image_to_data(processed_img, output_type=pytesseract.Output.DICT)
        avg_conf = np.mean([int(c) for c in data['conf'] if c != '-1'])
        
        return {
            "text": text,
            "confidence": avg_conf
        }

    def _preprocess(self, image):
        # Grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Binarization (Adaptive Thresholding)
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Deskewing (Simple)
        coords = np.column_stack(np.where(thresh > 0))
        angle = cv2.minAreaRect(coords)[-1]
        
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
            
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(thresh, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        
        return rotated
