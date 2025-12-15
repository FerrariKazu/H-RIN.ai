"""
Multi-engine PDF Processing Pipeline
Supports: text PDFs, scanned PDFs, hybrid PDFs, and various document types
Uses fallback mechanisms for robustness and NO mock data
"""

import fitz  # PyMuPDF
import cv2
import numpy as np
import logging
import pytesseract
from PIL import Image
import io
import re
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Any
import os
import shutil
from collections import Counter
from datetime import datetime

# PDF extraction libraries
from pdfminer.high_level import extract_text, extract_pages
from pdfminer.layout import LAParams, LTTextContainer, LTChar, LTFigure, LTCurve
from pypdf import PdfReader
import camelot

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Complete extraction result from PDF"""
    raw_text: str
    blocks: List[Dict] = None
    layout: Dict = None
    confidence: float = 0.0
    engine_used: str = ""
    needs_ocr: bool = False
    language_detected: str = "en"
    processing_time: float = 0.0
    tables: List[Dict] = None
    metadata: Dict = None
    logs: List[str] = None

    def to_dict(self):
        return asdict(self)


class DocumentTypeDetector:
    """Detect document type and quality"""
    
    @staticmethod
    def detect(file_path: str) -> Dict[str, Any]:
        """
        Detect document type:
        - text_native: Digital text PDF
        - scanned: Image-based PDF
        - hybrid: Mix of text and images
        - structured: Tables, forms, etc.
        """
        doc = fitz.open(file_path)
        detection_results = {
            "type": "unknown",
            "confidence": 0.0,
            "has_text": False,
            "has_images": False,
            "page_count": len(doc),
            "text_density": 0.0,
            "image_density": 0.0,
        }
        
        text_pages = 0
        image_pages = 0
        total_text_chars = 0
        
        for page_num, page in enumerate(doc):
            text = page.get_text()
            total_text_chars += len(text)
            
            if len(text.strip()) > 100:  # Significant text
                text_pages += 1
                detection_results["has_text"] = True
            
            # Check for images
            image_list = page.get_images()
            if image_list:
                image_pages += 1
                detection_results["has_images"] = True
        
        doc.close()
        
        # Determine type
        text_ratio = text_pages / max(detection_results["page_count"], 1)
        image_ratio = image_pages / max(detection_results["page_count"], 1)
        
        if text_ratio > 0.8:
            detection_results["type"] = "text_native"
            detection_results["confidence"] = text_ratio
        elif image_ratio > 0.8:
            detection_results["type"] = "scanned"
            detection_results["confidence"] = image_ratio
        elif text_ratio > 0.2 and image_ratio > 0.2:
            detection_results["type"] = "hybrid"
            detection_results["confidence"] = 0.7
        else:
            detection_results["type"] = "scanned"
            detection_results["confidence"] = 0.5
        
        detection_results["text_density"] = text_ratio
        detection_results["image_density"] = image_ratio
        
        return detection_results


class OCRProcessor:
    """OCR with fallback mechanisms"""
    
    def __init__(self):
        self.dpi = 300
        self.tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        self.tesseract_available = self._check_tesseract()
        
        if self.tesseract_available:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
            logger.info(f"Tesseract OCR initialized at {self.tesseract_path}")
        else:
            logger.warning("Tesseract OCR not found - OCR fallback will be skipped")
    
    def _check_tesseract(self) -> bool:
        """Check if Tesseract is available"""
        try:
            # Check if file exists at the expected path
            if os.path.exists(self.tesseract_path):
                return True
            # Check if tesseract is in system PATH
            return shutil.which('tesseract') is not None
        except Exception as e:
            logger.debug(f"Tesseract check failed: {e}")
            return False
    
    def process_image(self, image: Image.Image, lang: str = "en") -> Dict:
        """
        Process image with Tesseract OCR
        """
        if not self.tesseract_available:
            logger.warning("Tesseract not available, skipping OCR")
            return {
                "text": "",
                "confidence": 0.0,
                "language": lang,
                "success": False,
                "error": "Tesseract not installed"
            }
        
        try:
            # Preprocess image
            img_array = np.array(image)
            processed = self._preprocess(img_array)
            
            # OCR with timeout
            config = f'--oem 3 --psm 6 -l {lang}'
            text = pytesseract.image_to_string(processed, config=config, timeout=10)
            
            # Get confidence
            data = pytesseract.image_to_data(
                processed, 
                output_type=pytesseract.Output.DICT,
                config='--oem 3',
                timeout=10
            )
            
            confidences = [int(c) for c in data['conf'] if c != '-1']
            avg_confidence = np.mean(confidences) / 100 if confidences else 0.0
            
            return {
                "text": text,
                "confidence": avg_confidence,
                "language": lang,
                "success": True
            }
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "language": lang,
                "success": False,
                "error": str(e)
            }

    def _preprocess(self, image: np.ndarray) -> Image.Image:
        """Preprocess image for better OCR accuracy"""
        # Grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Increase contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        contrasted = clahe.apply(denoised)
        
        # Adaptive threshold
        thresh = cv2.adaptiveThreshold(
            contrasted, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)
        
        return Image.fromarray(cleaned)


class PDFProcessor:
    """Main PDF processing pipeline"""
    
    def __init__(self):
        self.ocr_processor = OCRProcessor()
        self.logs = []
    
    def process(self, file_path: str) -> ExtractionResult:
        """
        Process PDF with multi-engine approach
        NO MOCK DATA - all output is from the actual PDF
        """
        start_time = datetime.now()
        self.logs = []
        
        try:
            # Step 1: Detect document type
            self._log(f"Starting PDF processing: {file_path}")
            doc_type = DocumentTypeDetector.detect(file_path)
            self._log(f"Document type: {doc_type['type']} (confidence: {doc_type['confidence']:.2f})")
            
            # Step 2: Extract with multiple engines
            extraction = self._extract_multi_engine(file_path, doc_type)
            
            # Step 3: If quality is poor, apply OCR
            if extraction["confidence"] < 0.5 or doc_type["type"] in ["scanned", "hybrid"]:
                self._log("Low confidence detected, applying OCR fallback")
                ocr_result = self._apply_ocr(file_path)
                
                if ocr_result["confidence"] > extraction["confidence"]:
                    extraction = ocr_result
                    extraction["needs_ocr"] = True
            
            # Step 4: Extract tables
            tables = self._extract_tables(file_path)
            if tables:
                extraction["tables"] = tables
                self._log(f"Extracted {len(tables)} tables")
            
            # Step 5: Get metadata
            extraction["metadata"] = self._get_metadata(file_path)
            
            # Create result
            result = ExtractionResult(
                raw_text=extraction.get("text", ""),
                blocks=extraction.get("blocks", []),
                layout=extraction.get("layout", {}),
                confidence=extraction.get("confidence", 0.0),
                engine_used=extraction.get("engine", "unknown"),
                needs_ocr=extraction.get("needs_ocr", False),
                processing_time=(datetime.now() - start_time).total_seconds(),
                tables=extraction.get("tables", []),
                metadata=extraction.get("metadata", {}),
                logs=self.logs
            )
            
            self._log(f"Processing complete in {result.processing_time:.2f}s")
            return result
            
        except Exception as e:
            self._log(f"ERROR: {str(e)}", level="ERROR")
            return ExtractionResult(
                raw_text="",
                confidence=0.0,
                engine_used="error",
                processing_time=(datetime.now() - start_time).total_seconds(),
                logs=self.logs
            )
    
    def _extract_multi_engine(self, file_path: str, doc_type: Dict) -> Dict:
        """Extract using multiple engines and merge results"""
        engines_results = []
        
        # Engine 1: PyMuPDF (best for layout)
        try:
            pymupdf_result = self._extract_pymupdf(file_path)
            engines_results.append(pymupdf_result)
            self._log(f"PyMuPDF: {len(pymupdf_result.get('text', ''))} chars, confidence {pymupdf_result['confidence']:.2f}")
        except Exception as e:
            self._log(f"PyMuPDF failed: {e}")
        
        # Engine 2: pdfminer.six (best for text ordering)
        try:
            pdfminer_result = self._extract_pdfminer(file_path)
            engines_results.append(pdfminer_result)
            self._log(f"pdfminer: {len(pdfminer_result.get('text', ''))} chars, confidence {pdfminer_result['confidence']:.2f}")
        except Exception as e:
            self._log(f"pdfminer failed: {e}")
        
        # Engine 3: pypdf (metadata + raw)
        try:
            pypdf_result = self._extract_pypdf(file_path)
            engines_results.append(pypdf_result)
            self._log(f"pypdf: {len(pypdf_result.get('text', ''))} chars, confidence {pypdf_result['confidence']:.2f}")
        except Exception as e:
            self._log(f"pypdf failed: {e}")
        
        # Merge results (use highest confidence)
        if not engines_results:
            return {"text": "", "confidence": 0.0, "engine": "none"}
        
        best_result = max(engines_results, key=lambda x: x.get("confidence", 0))
        best_result["engine"] = "merged"
        
        # Merge texts intelligently
        texts = [r.get("text", "") for r in engines_results if r.get("text")]
        if texts:
            best_result["text"] = self._merge_texts(texts)
        
        return best_result
    
    def _extract_pymupdf(self, file_path: str) -> Dict:
        """Extract using PyMuPDF with layout info"""
        doc = fitz.open(file_path)
        texts = []
        blocks = []
        
        for page_num, page in enumerate(doc):
            text = page.get_text()
            texts.append(text)
            
            # Get blocks with layout info
            page_blocks = page.get_text("dict")["blocks"]
            for block in page_blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            blocks.append({
                                "text": span["text"],
                                "page": page_num,
                                "bbox": span.get("bbox", []),
                                "font_size": span.get("size", 0),
                                "font": span.get("font", "")
                            })
        
        doc.close()
        
        raw_text = "\n".join(texts)
        confidence = 0.95 if raw_text and len(raw_text) > 100 else 0.0
        
        return {
            "text": raw_text,
            "blocks": blocks,
            "confidence": confidence,
            "engine": "pymupdf"
        }
    
    def _extract_pdfminer(self, file_path: str) -> Dict:
        """Extract using pdfminer for detailed text ordering"""
        try:
            text = extract_text(file_path)
            confidence = 0.90 if text and len(text) > 100 else 0.0
            
            return {
                "text": text,
                "confidence": confidence,
                "engine": "pdfminer"
            }
        except Exception as e:
            self._log(f"pdfminer extraction failed: {e}")
            return {"text": "", "confidence": 0.0, "engine": "pdfminer"}
    
    def _extract_pypdf(self, file_path: str) -> Dict:
        """Extract using pypdf for raw text and metadata"""
        try:
            reader = PdfReader(file_path)
            texts = []
            
            for page in reader.pages:
                texts.append(page.extract_text())
            
            text = "\n".join(texts)
            confidence = 0.85 if text and len(text) > 100 else 0.0
            
            return {
                "text": text,
                "confidence": confidence,
                "engine": "pypdf"
            }
        except Exception as e:
            self._log(f"pypdf extraction failed: {e}")
            return {"text": "", "confidence": 0.0, "engine": "pypdf"}
    
    def _apply_ocr(self, file_path: str) -> Dict:
        """Apply OCR fallback for scanned documents"""
        doc = fitz.open(file_path)
        ocr_texts = []
        total_confidence = 0
        
        for page_num, page in enumerate(doc):
            try:
                # Render page to image
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), dpi=self.ocr_processor.dpi)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # OCR
                ocr_result = self.ocr_processor.process_image(img)
                ocr_texts.append(ocr_result["text"])
                total_confidence += ocr_result["confidence"]
                
                self._log(f"OCR page {page_num + 1}: confidence {ocr_result['confidence']:.2f}")
            except Exception as e:
                self._log(f"OCR failed on page {page_num + 1}: {e}")
        
        doc.close()
        
        raw_text = "\n".join(ocr_texts)
        avg_confidence = total_confidence / len(ocr_texts) if ocr_texts else 0.0
        
        return {
            "text": raw_text,
            "confidence": avg_confidence,
            "engine": "ocr",
            "needs_ocr": True
        }
    
    def _extract_tables(self, file_path: str) -> List[Dict]:
        """Extract tables using camelot with tabula fallback"""
        tables = []
        
        try:
            # Try camelot
            camelot_tables = camelot.read_pdf(file_path, pages='all')
            for i, table in enumerate(camelot_tables):
                tables.append({
                    "index": i,
                    "data": table.df.to_dict(orient='records'),
                    "engine": "camelot",
                    "accuracy": table.accuracy
                })
            
            if tables:
                self._log(f"Camelot extracted {len(tables)} tables")
                return tables
        except Exception as e:
            self._log(f"Camelot failed: {e}, trying tabula")
        
        try:
            # Try tabula fallback
            import tabula
            tabula_tables = tabula.read_pdf(file_path, pages='all', multiple_tables=True)
            for i, table_df in enumerate(tabula_tables):
                tables.append({
                    "index": i,
                    "data": table_df.to_dict(orient='records'),
                    "engine": "tabula"
                })
            
            if tables:
                self._log(f"Tabula extracted {len(tables)} tables")
        except Exception as e:
            self._log(f"Tabula also failed: {e}")
        
        return tables
    
    def _merge_texts(self, texts: List[str]) -> str:
        """Intelligently merge texts from multiple engines"""
        # Use the longest text as base (usually best)
        if not texts:
            return ""
        
        texts = [t for t in texts if t and len(t.strip()) > 10]
        if not texts:
            return ""
        
        # Prefer longest extracted text
        longest = max(texts, key=len)
        
        # Clean up formatting
        lines = longest.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Normalize multiple spaces
                line = re.sub(r'\s+', ' ', line)
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _get_metadata(self, file_path: str) -> Dict:
        """Extract PDF metadata"""
        try:
            doc = fitz.open(file_path)
            metadata = doc.metadata or {}
            
            file_stats = os.stat(file_path)
            metadata['file_size_bytes'] = file_stats.st_size
            metadata['file_size_mb'] = file_stats.st_size / (1024 * 1024)
            metadata['page_count'] = len(doc)
            
            doc.close()
            return metadata
        except Exception as e:
            self._log(f"Metadata extraction failed: {e}")
            return {}
    
    def _log(self, message: str, level: str = "INFO"):
        """Add to logs"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.logs.append(log_entry)
        
        if level == "ERROR":
            logger.error(message)
        else:
            logger.info(message)


# Backward compatibility
PDFParser = PDFProcessor
