import fitz  # PyMuPDF
import pdfplumber
from pdfminer.high_level import extract_text as miner_text
from pdfminer.layout import LAParams
import logging
import os
try:
    import camelot
except ImportError:
    camelot = None

logger = logging.getLogger(__name__)

class PDFParser:
    def __init__(self):
        self.strategies = {
            "pymupdf": self._extract_pymupdf,
            "pdfminer": self._extract_pdfminer,
            "camelot": self._extract_tables
        }

    def process(self, file_path):
        """
        Master extraction logic.
        Returns: {
            "text": str,
            "tables": list,
            "meta": dict,
            "images": list (of bytes)
        }
        """
        logger.info(f"Processing PDF: {file_path}")
        
        # 1. Basic Text Extraction (PyMuPDF - Fast)
        text_pymupdf = self._extract_pymupdf(file_path)
        
        # 2. Detailed Layout Extraction (PDFMiner - Slow but precise)
        # We assume if PyMuPDF returns very little text, we might need OCR (handled by OCR engine)
        if len(text_pymupdf.strip()) < 50:
            logger.warning("Low text content detected. Marking for OCR.")
            return {"text": "", "needs_ocr": True, "images": self._extract_images(file_path)}

        # 3. Table Extraction (Camelot)
        tables = []
        if camelot:
            try:
                # Lattice is better for bordered tables
                tables = camelot.read_pdf(file_path, pages='all', flavor='lattice')
                tables = [t.df.to_dict() for t in tables]
            except Exception as e:
                logger.error(f"Camelot table extraction failed: {e}")

        return {
            "text": text_pymupdf,
            "tables": tables,
            "needs_ocr": False,
            "meta": self._get_metadata(file_path),
            "images": self._extract_images(file_path)
        }

    def _extract_pymupdf(self, path):
        doc = fitz.open(path)
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        return text

    def _extract_pdfminer(self, path):
        # Good for ensuring reading order in complex layouts
        laparams = LAParams()
        return miner_text(path, laparams=laparams)

    def _extract_tables(self, path):
        pass # Handled in main process

    def _get_metadata(self, path):
        doc = fitz.open(path)
        return doc.metadata

    def _extract_images(self, path):
        # Extract images for OCR or display
        doc = fitz.open(path)
        images = []
        for page in doc:
            pix = page.get_pixmap()
            img_data = pix.tobytes("png")
            images.append(img_data)
        return images
