import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extracts text from a PDF file provided as bytes.
    
    Args:
        pdf_bytes (bytes): The content of the PDF file.
        
    Returns:
        str: The extracted text from the PDF.
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        raise ValueError(f"Error extracting text from PDF: {str(e)}")
