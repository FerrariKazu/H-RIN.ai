import fitz  # PyMuPDF
import logging
import pytesseract
from PIL import Image
import io
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams, LTTextContainer, LTChar, LTAnno
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.converter import PDFPageAggregator
import dateutil.parser as date_parser
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class TextBlock:
    """Represents a block of text with formatting information"""
    text: str
    bbox: Tuple[float, float, float, float]  # x0, y0, x1, y1
    font_size: float
    font_name: str
    is_bold: bool
    page_num: int


@dataclass
class ResumeSection:
    """Represents a detected section in a resume"""
    title: str
    content: str
    start_page: int
    confidence: float


class EnhancedPDFParser:
    """
    Enhanced PDF parser optimized for resumes, CVs, and structured documents.
    Features:
    - Layout-aware text extraction
    - Section detection
    - Contact information extraction
    - Smart OCR fallback
    - Font and formatting analysis
    """
    
    # Common resume section headers
    SECTION_PATTERNS = {
        'contact': r'\b(contact|email|phone|address|linkedin|github)\b',
        'summary': r'\b(summary|profile|objective|about|overview)\b',
        'experience': r'\b(experience|employment|work\s*history|professional\s*experience)\b',
        'education': r'\b(education|academic|qualifications|degrees?)\b',
        'skills': r'\b(skills|competencies|expertise|technologies|technical\s*skills)\b',
        'projects': r'\b(projects|portfolio|work\s*samples)\b',
        'certifications': r'\b(certifications?|licenses?|accreditations?)\b',
        'awards': r'\b(awards?|honors?|achievements?|recognition)\b',
        'publications': r'\b(publications?|papers?|research)\b',
        'languages': r'\b(languages?|linguistic)\b',
        'references': r'\b(references?)\b'
    }
    
    # Contact information patterns
    CONTACT_PATTERNS = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        'linkedin': r'linkedin\.com/in/[\w-]+',
        'github': r'github\.com/[\w-]+',
        'url': r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
    }
    
    def __init__(self, min_text_threshold: int = 100, dpi: int = 300):
        self.min_text_threshold = min_text_threshold
        self.dpi = dpi
        self.text_blocks: List[TextBlock] = []
        
    def process(self, file_path: str) -> Dict:
        """
        Main processing method with comprehensive extraction
        """
        logger.info(f"Processing PDF: {file_path}")
        
        # Extract text with layout information
        text_blocks = self._extract_with_layout(file_path)
        self.text_blocks = text_blocks
        
        # Get raw text
        raw_text = "\n".join(block.text for block in text_blocks) if text_blocks else ""
        
        # Check if OCR is needed
        needs_ocr = len(raw_text.strip()) < self.min_text_threshold
        
        if needs_ocr:
            logger.warning("Low-text PDF detected → OCR fallback")
            ocr_text = self._ocr_pdf(file_path)
            raw_text = ocr_text
            text_blocks = []  # OCR doesn't preserve layout
        
        # Normalize text
        normalized_text = self._normalize(raw_text)
        
        # Detect if it's a resume
        is_resume, resume_confidence = self._is_resume_advanced(normalized_text)
        
        # Extract structured information
        result = {
            "raw_text": normalized_text,
            "needs_ocr": needs_ocr,
            "meta": self._get_metadata(file_path),
            "is_resume": is_resume,
            "resume_confidence": resume_confidence,
            "page_count": self._get_page_count(file_path)
        }
        
        # If it's a resume, extract additional structured data
        if is_resume:
            result.update({
                "sections": self._detect_sections(normalized_text, text_blocks),
                "contact_info": self._extract_contact_info(normalized_text),
                "dates": self._extract_dates(normalized_text),
                "structure_analysis": self._analyze_structure(text_blocks)
            })
        
        return result
    
    # ---------- LAYOUT-AWARE TEXT EXTRACTION ----------
    
    def _extract_with_layout(self, path: str) -> List[TextBlock]:
        """
        Extract text with layout, font, and formatting information
        """
        text_blocks = []
        doc = fitz.open(path)
        
        for page_num, page in enumerate(doc):
            # Get text with formatting details
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks:
                if "lines" not in block:
                    continue
                    
                for line in block["lines"]:
                    line_text = ""
                    font_sizes = []
                    font_names = []
                    is_bold = False
                    
                    for span in line["spans"]:
                        line_text += span["text"]
                        font_sizes.append(span["size"])
                        font_names.append(span["font"])
                        
                        # Detect bold (heuristic: font name contains 'Bold')
                        if "bold" in span["font"].lower():
                            is_bold = True
                    
                    if line_text.strip():
                        avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 12
                        common_font = Counter(font_names).most_common(1)[0][0] if font_names else "Unknown"
                        
                        text_blocks.append(TextBlock(
                            text=line_text.strip(),
                            bbox=tuple(line["bbox"]),
                            font_size=avg_font_size,
                            font_name=common_font,
                            is_bold=is_bold,
                            page_num=page_num
                        ))
        
        return text_blocks
    
    # ---------- OCR ----------
    
    def _ocr_pdf(self, path: str) -> str:
        """
        Enhanced OCR with preprocessing for better accuracy
        """
        doc = fitz.open(path)
        ocr_text = []
        
        for page in doc:
            # Higher DPI for better quality
            pix = page.get_pixmap(dpi=self.dpi)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            
            # OCR with page segmentation mode optimized for documents
            custom_config = r'--oem 3 --psm 6'
            page_text = pytesseract.image_to_string(img, config=custom_config)
            ocr_text.append(page_text)
        
        return "\n".join(ocr_text)
    
    # ---------- SECTION DETECTION ----------
    
    def _detect_sections(self, text: str, text_blocks: List[TextBlock]) -> List[ResumeSection]:
        """
        Detect and extract resume sections with confidence scores
        """
        sections = []
        lines = text.split('\n')
        
        # If we have layout information, use it
        if text_blocks:
            sections = self._detect_sections_with_layout(text_blocks)
        else:
            # Fallback to text-based detection
            current_section = None
            section_content = []
            
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                
                # Check if line is a section header
                section_match = self._match_section_header(line_stripped)
                
                if section_match:
                    # Save previous section
                    if current_section:
                        sections.append(ResumeSection(
                            title=current_section,
                            content="\n".join(section_content),
                            start_page=0,
                            confidence=0.8
                        ))
                    
                    current_section = section_match
                    section_content = []
                elif current_section:
                    section_content.append(line)
            
            # Add last section
            if current_section and section_content:
                sections.append(ResumeSection(
                    title=current_section,
                    content="\n".join(section_content),
                    start_page=0,
                    confidence=0.8
                ))
        
        return sections
    
    def _detect_sections_with_layout(self, text_blocks: List[TextBlock]) -> List[ResumeSection]:
        """
        Use layout information to detect sections more accurately
        """
        sections = []
        
        # Identify headers based on font size and boldness
        avg_font_size = sum(b.font_size for b in text_blocks) / len(text_blocks) if text_blocks else 12
        
        current_section = None
        section_blocks = []
        
        for block in text_blocks:
            is_header = (
                block.font_size > avg_font_size * 1.1 or
                block.is_bold
            )
            
            section_match = self._match_section_header(block.text)
            
            if is_header and section_match:
                # Save previous section
                if current_section and section_blocks:
                    sections.append(ResumeSection(
                        title=current_section,
                        content="\n".join(b.text for b in section_blocks),
                        start_page=section_blocks[0].page_num if section_blocks else 0,
                        confidence=0.9
                    ))
                
                current_section = section_match
                section_blocks = []
            elif current_section:
                section_blocks.append(block)
        
        # Add last section
        if current_section and section_blocks:
            sections.append(ResumeSection(
                title=current_section,
                content="\n".join(b.text for b in section_blocks),
                start_page=section_blocks[0].page_num if section_blocks else 0,
                confidence=0.9
            ))
        
        return sections
    
    def _match_section_header(self, text: str) -> Optional[str]:
        """
        Match text against known section patterns
        """
        text_lower = text.lower().strip()
        
        for section_name, pattern in self.SECTION_PATTERNS.items():
            if re.search(pattern, text_lower):
                return section_name
        
        return None
    
    # ---------- CONTACT INFORMATION EXTRACTION ----------
    
    def _extract_contact_info(self, text: str) -> Dict[str, List[str]]:
        """
        Extract contact information using regex patterns
        """
        contact_info = {}
        
        for contact_type, pattern in self.CONTACT_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                contact_info[contact_type] = list(set(matches))  # Remove duplicates
        
        return contact_info
    
    # ---------- DATE EXTRACTION ----------
    
    def _extract_dates(self, text: str) -> List[str]:
        """
        Extract dates from text (useful for employment history, education)
        """
        date_patterns = [
            r'\b\d{4}\b',  # Year
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b',  # Month Year
            r'\b\d{1,2}/\d{4}\b',  # MM/YYYY
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        
        return list(set(dates))
    
    # ---------- RESUME DETECTION ----------
    
    def _is_resume_advanced(self, text: str) -> Tuple[bool, float]:
        """
        Advanced resume detection with confidence scoring
        """
        text_lower = text.lower()
        score = 0
        max_score = 0
        
        # Check for section keywords (weighted)
        for section_name, pattern in self.SECTION_PATTERNS.items():
            max_score += 10
            if re.search(pattern, text_lower):
                score += 10
        
        # Check for contact information (weighted)
        for contact_type, pattern in self.CONTACT_PATTERNS.items():
            max_score += 5
            if re.search(pattern, text):
                score += 5
        
        # Check for dates (suggests timeline/history)
        if self._extract_dates(text):
            score += 15
            max_score += 15
        
        # Check for common resume phrases
        resume_phrases = [
            'years of experience', 'responsible for', 'managed', 'developed',
            'bachelor', 'master', 'degree', 'university', 'gpa'
        ]
        max_score += 20
        phrase_matches = sum(1 for phrase in resume_phrases if phrase in text_lower)
        score += min(phrase_matches * 2, 20)
        
        confidence = score / max_score if max_score > 0 else 0
        is_resume = confidence > 0.4
        
        return is_resume, confidence
    
    # ---------- STRUCTURE ANALYSIS ----------
    
    def _analyze_structure(self, text_blocks: List[TextBlock]) -> Dict:
        """
        Analyze document structure (useful for understanding layout quality)
        """
        if not text_blocks:
            return {}
        
        font_sizes = [b.font_size for b in text_blocks]
        
        return {
            "avg_font_size": sum(font_sizes) / len(font_sizes),
            "min_font_size": min(font_sizes),
            "max_font_size": max(font_sizes),
            "bold_blocks": sum(1 for b in text_blocks if b.is_bold),
            "total_blocks": len(text_blocks),
            "pages": len(set(b.page_num for b in text_blocks))
        }
    
    # ---------- METADATA ----------
    
    def _get_metadata(self, path: str) -> Dict:
        """
        Extract PDF metadata
        """
        doc = fitz.open(path)
        metadata = doc.metadata or {}
        
        # Add file size
        import os
        if os.path.exists(path):
            metadata['file_size_kb'] = os.path.getsize(path) / 1024
        
        return metadata
    
    def _get_page_count(self, path: str) -> int:
        """
        Get number of pages
        """
        doc = fitz.open(path)
        return len(doc)
    
    # ---------- NORMALIZATION ----------
    
    def _normalize(self, text: str) -> str:
        """
        Enhanced text normalization
        """
        # Remove null bytes
        text = text.replace("\x00", "")
        
        # Remove excessive whitespace while preserving structure
        lines = []
        for line in text.splitlines():
            line = line.strip()
            if line:
                # Normalize multiple spaces to single space
                line = re.sub(r'\s+', ' ', line)
                lines.append(line)
        
        # Join with single newlines
        text = "\n".join(lines)
        
        # Remove excessive blank lines (more than 2 consecutive)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text


# Alias for backwards compatibility
PDFParser = EnhancedPDFParser


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    parser = EnhancedPDFParser(min_text_threshold=100, dpi=300)
    result = parser.process("resume.pdf")
    
    print(f"Is Resume: {result['is_resume']} (confidence: {result.get('resume_confidence', 0):.2f})")
    print(f"Pages: {result['page_count']}")
    print(f"OCR Required: {result['needs_ocr']}")
    
    if result['is_resume']:
        print(f"\nSections found: {len(result.get('sections', []))}")
        for section in result.get('sections', []):
            print(f"  - {section.title.upper()} (confidence: {section.confidence:.2f})")
        
        print(f"\nContact Information:")
        for contact_type, values in result.get('contact_info', {}).items():
            print(f"  - {contact_type}: {values}")