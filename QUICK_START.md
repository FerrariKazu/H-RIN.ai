# HR Buddy - Quick Start Guide

## Status: ✓ READY TO USE

The HR Buddy resume processing pipeline is fully functional and tested.

## Quick Start (30 seconds)

### Option 1: Use System Python (Recommended if already using conda)
Simply run the provided batch script:
```batch
run.bat
```

### Option 2: Setup Fresh Virtual Environment
Run the setup script first:
```batch
setup.bat
```

Then start the application:
```batch
run.bat
```

## What Gets Started

**Backend API** (Port 8001)
- Resume PDF upload and processing
- Text extraction and analysis
- NLP entity extraction
- JSON/Markdown generation
- LLM-based analysis

**Frontend** (Port 3000) - if available

## API Endpoints

### Health Check
```
GET http://localhost:8001/health
```
Returns: Service status and component availability

### Upload & Extract PDF
```
POST http://localhost:8001/upload
Content-Type: multipart/form-data
Body: file (PDF)
```
Returns: Raw text extraction, confidence score, processing logs

### Analyze Text
```
POST http://localhost:8001/analyze
Content-Type: application/json
Body: {
    "extracted_text": "string",
    "filename": "optional",
    "enable_llm_analysis": true
}
```
Returns: Markdown version, JSON structured data, LLM analysis

### Full Pipeline
```
POST http://localhost:8001/process
Content-Type: multipart/form-data
Body: file (PDF)
```
Returns: Complete processed result (text + analysis)

### API Documentation
```
GET http://localhost:8001/docs
```
Interactive Swagger UI with all endpoints

## Testing

Run the test suite to verify everything works:
```bash
python test_api.py
```

Expected output:
```
✓ Health Check PASSED
✓ NLP Extraction PASSED
✓ PDF Processing PASSED
Overall: 3/3 tests passed
```

## Technologies Used

- **Framework**: FastAPI with Uvicorn
- **PDF Processing**: PyMuPDF, pdfminer.six, pypdf, camelot-py
- **OCR**: Tesseract via pytesseract
- **NLP**: SpaCy (en_core_web_sm)
- **LLM**: OpenAI or Ollama integration
- **Data**: Pydantic validation, dataclasses

## Environment

- **Python**: 3.8+ (tested with 3.13.9)
- **OS**: Windows (batch scripts provided)
- **Dependencies**: All in requirements.txt
- **Models**: Lazy-loaded on first API call

## File Structure

```
Project/
├── backend/
│   ├── main.py                    # FastAPI application
│   ├── pipeline/
│   │   ├── pdf_processor.py      # Multi-engine PDF extraction
│   │   ├── nlp_engine_v2.py      # NLP entity extraction
│   │   ├── resume_reconstructor.py  # Markdown/JSON formatting
│   │   └── llm_analyzer.py       # LLM analysis with fallback
│   └── ...
├── frontend/                      # Web interface (if present)
├── venv/                         # Virtual environment (created by setup.bat)
├── run.bat                       # Start application
├── setup.bat                     # Setup environment
├── requirements.txt              # Dependencies
├── test_api.py                   # Test suite
└── SETUP_GUIDE.md               # Detailed setup instructions
```

## Troubleshooting

### Port 8001 Already in Use
```powershell
# Find and kill the process
netstat -ano | findstr 8001
taskkill /PID <PID> /F
```

### Backend Not Starting
1. Check you're in the project root directory
2. Verify Python is installed: `python --version`
3. Check error message in the backend window
4. Run `test_api.py` to see detailed error

### NLP Model Not Found
The model loads lazily on first API call. If it's missing:
```bash
python -m spacy download en_core_web_sm
```

## API Usage Examples

### Python
```python
import requests

# Health check
response = requests.get("http://localhost:8001/health")
print(response.json())

# Analyze text
data = {
    "extracted_text": "Your resume text here...",
    "enable_llm_analysis": True
}
response = requests.post("http://localhost:8001/analyze", json=data)
result = response.json()
print(result['markdown'])
print(result['json_data'])
```

### cURL
```bash
# Health check
curl http://localhost:8001/health

# Upload PDF
curl -F "file=@resume.pdf" http://localhost:8001/upload

# Analyze text
curl -X POST http://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -d '{"extracted_text":"John Smith...","enable_llm_analysis":true}'
```

## Performance Notes

- First API call will take longer (model loading)
- Subsequent calls are fast
- PDF processing time depends on file size/complexity
- LLM analysis requires API key if enabled

## Support Files

- **SETUP_GUIDE.md** - Detailed setup instructions
- **API_REFERENCE.md** - Full API documentation (if exists)
- **test_api.py** - Test suite for validation
- **diagnose_spacy.py** - NLP model diagnostic tool

## Success Indicators

✓ `run.bat` opens two windows (Backend + Frontend)
✓ `test_api.py` shows all tests passing
✓ Health endpoint returns `"status": "ok"`
✓ Backend window shows "Uvicorn running on 0.0.0.0:8001"

---

**Last Updated**: System ready for production use  
**Backend Status**: Running and tested  
**All Components**: Ready (pdf_processor, nlp_engine, resume_reconstructor, llm_analyzer)
