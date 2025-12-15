# HR Buddy API - Quick Reference

## 🚀 Getting Started

```bash
# Start services
.\run.bat

# Services will run on:
# - Backend: http://localhost:8001
# - Frontend: http://localhost:3000
```

---

## 📡 API Endpoints Quick Reference

### Health Check
```bash
GET http://localhost:8001/health
```

### Upload & Extract
```bash
POST http://localhost:8001/upload
Body: multipart/form-data (PDF file)

Response: {
  "raw_text": "...",
  "extraction_logs": [...],
  "confidence": 0.95,
  "processing_time": 2.34
}
```

### Analyze Extracted Text
```bash
POST http://localhost:8001/analyze
Body: {
  "filename": "resume.pdf",
  "extracted_text": "...",
  "enable_llm_analysis": true
}

Response: {
  "resume_markdown": "...",
  "resume_json": {...},
  "llm_analysis": {...}
}
```

### End-to-End Processing
```bash
POST http://localhost:8001/process
Body: multipart/form-data (PDF file)
Query: ?enable_llm_analysis=true

Response: {
  "raw_text": "...",
  "resume_markdown": "...",
  "resume_json": {...},
  "llm_analysis": {...},
  "processing_logs": [...]
}
```

### Interactive Docs
```
http://localhost:8001/docs
```

---

## 📊 JSON Schema Reference

### Resume JSON Structure
```json
{
  "summary": "Professional summary text",
  "contact": {
    "phone": "+1-555-0000",
    "email": "user@email.com",
    "address": "City, State",
    "linkedin": "linkedin.com/in/username",
    "github": "github.com/username"
  },
  "skills": [
    {
      "skill": "Python",
      "category": "programming_languages",
      "proficiency": "advanced"
    }
  ],
  "experience": [
    {
      "company": "Company Name",
      "role": "Senior Engineer",
      "start_date": "2020-01",
      "end_date": "2023-12",
      "description": "Responsibilities and achievements",
      "current": false
    }
  ],
  "education": [
    {
      "school": "University Name",
      "degree": "Bachelor of Science",
      "field_of_study": "Computer Science",
      "start_date": "2016-09",
      "end_date": "2020-05",
      "gpa": "3.8"
    }
  ],
  "projects": [
    {
      "name": "Project Name",
      "description": "Project description"
    }
  ],
  "certifications": [
    {
      "name": "Certification Name",
      "issuer": "Issuing Organization"
    }
  ],
  "languages": [
    {
      "language": "English",
      "proficiency": "Native"
    }
  ],
  "achievements": [
    "Key achievement or award"
  ]
}
```

### LLM Analysis Schema
```json
{
  "executive_summary": "One-liner assessment",
  "strengths": [
    "Strong technical background",
    "Leadership experience"
  ],
  "weaknesses": [
    "Limited cloud experience"
  ],
  "opportunities": [
    "AWS certification would boost profile"
  ],
  "technical_fit": {
    "score": 82,
    "explanation": "Strong in core tech stack"
  },
  "cultural_fit": {
    "score": 78,
    "explanation": "Leadership and teamwork evident"
  },
  "seniority_level": "senior",
  "recommended_roles": [
    "Senior Software Engineer",
    "Tech Lead",
    "Engineering Manager"
  ],
  "missing_skills": [
    "AWS/Azure",
    "Kubernetes"
  ],
  "overall_score": 80,
  "key_metrics": {
    "skills_count": 15,
    "experience_count": 4,
    "education_count": 1
  }
}
```

---

## 🔍 Processing Logs Reference

Logs contain information in format: `[HH:MM:SS] LEVEL: message`

**Log Levels:**
- `[INFO]` - Normal operation
- `[WARNING]` - Degradation or fallback
- `[ERROR]` - Failed operation

**Example Log Output:**
```
[14:30:15] INFO: Document type: text_native (confidence: 0.95)
[14:30:15] INFO: PyMuPDF: 5234 chars, confidence 0.95
[14:30:16] INFO: pdfminer: 5240 chars, confidence 0.92
[14:30:16] INFO: Processing complete in 1.23s
[14:30:17] INFO: Extracted 15 skills using NLP
[14:30:18] INFO: Detected 4 experience entries
[14:30:20] INFO: LLM analysis: score 82/100, seniority senior
```

---

## 🛠️ Troubleshooting

### "Tesseract not found"
- Install from: https://github.com/UB-Mannheim/tesseract/wiki
- Default path: `C:\Program Files\Tesseract-OCR`
- Or update path in: `backend/pipeline/pdf_processor.py`

### "Spacy model not found"
```bash
python -m spacy download en_core_web_sm
```

### Port already in use
- Backend: Change port in `backend/main.py` (line ~220)
- Frontend: Change port in `run.bat` line 32

### LLM Analysis Fails
- Falls back to heuristic analysis
- No mock data - based on actual extraction
- Check logs for details

---

## 📈 Performance Notes

- **Single page PDF**: ~1-2 seconds
- **Multi-page PDF**: ~3-5 seconds
- **Scanned PDF**: +1-2 seconds (OCR)
- **End-to-end with LLM**: +1-2 seconds
- **Total for typical resume**: ~5-10 seconds

---

## 🔐 Data Handling

- **No data storage** - processing only
- **Temporary files deleted** - after processing
- **No external uploads** - all local
- **CORS enabled** - for frontend integration
- **Logs returned** - for audit trail

---

## 📚 More Information

- Full implementation details: [BACKEND_IMPLEMENTATION.md](BACKEND_IMPLEMENTATION.md)
- API Swagger Docs: `http://localhost:8001/docs`
- OpenAPI JSON: `http://localhost:8001/openapi.json`

---

## 💡 Example Usage (Python)

```python
import requests

# Upload and process
files = {'file': open('resume.pdf', 'rb')}
response = requests.post(
    'http://localhost:8001/process',
    files=files,
    params={'enable_llm_analysis': True}
)

result = response.json()

# Access results
print(f"Confidence: {result['extraction_confidence']}")
print(f"Skills found: {len(result['resume_json']['skills'])}")
print(f"Overall score: {result['llm_analysis']['overall_score']}")

for log in result['processing_logs']:
    print(log)
```

---

## 💬 Example Usage (JavaScript/Fetch)

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch(
  'http://localhost:8001/process?enable_llm_analysis=true',
  {
    method: 'POST',
    body: formData
  }
);

const result = await response.json();

console.log('Resume:', result.resume_json);
console.log('Analysis:', result.llm_analysis);
console.log('Logs:', result.processing_logs);
```

---

Last Updated: December 15, 2025
Version: 3.0 Production
