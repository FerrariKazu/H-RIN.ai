# Batch Multi-PDF Analysis Feature

## Overview

The batch processing feature allows you to upload and analyze **up to 5 resume PDFs in a single request**, with shared job requirements applied to all documents. This is a **true batch processing system** (not sequential single uploads), enabling efficient parallel analysis of multiple candidates.

## Architecture

### Frontend → Backend Flow

```
┌─────────────────────────────────────────────────────────────┐
│ FRONTEND (vanilla JS + Lucide icons)                        │
│                                                              │
│ User drops/selects up to 5 PDFs                             │
│         ↓                                                    │
│ handleFiles() validates: ✓ PDF only ✓ Max 5 files          │
│         ↓                                                    │
│ showFileQueue() displays per-file status                    │
│         ↓                                                    │
│ uploadBatch() sends FormData to backend                     │
│         ↓                                                    │
│ renderBatchResults() displays comparison table              │
└─────────────────────────────────────────────────────────────┘
                         ↓
                    FormData with:
                    - files: [PDF1, PDF2, ..., PDF5]
                    - job_requirements: string
                    - batch_id: unique identifier
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ BACKEND (/batch-analyze endpoint)                           │
│                                                              │
│ For each document:                                          │
│   1. Validate PDF format                                    │
│   2. Extract text (PDF Processor)                          │
│   3. NLP analysis (spaCy + transformers)                   │
│   4. Resume reconstruction (JSON + Markdown)               │
│   5. LLM analysis with job requirements                    │
│   6. Return: document_id, status, extraction, analysis     │
│                                                              │
│ Return: BatchAnalyzeResponse with all documents            │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ FRONTEND (Results Display)                                  │
│                                                              │
│ Render Comparison Table:                                   │
│ - Candidate name with document_id                          │
│ - Status (Success/Failed)                                  │
│ - Overall Score (color coded)                              │
│ - Matched Skills (green tags)                              │
│ - Missing Skills (red tags)                                │
│ - Experience Assessment                                    │
│ - Fit Assessment                                           │
│                                                              │
│ Enable Sorting:                                            │
│ - Sort by Score (descending, best fit first)              │
│ - Sort by Name (alphabetical)                              │
└─────────────────────────────────────────────────────────────┘
```

## User Interface

### 1. Upload Area (Updated)
- **Drag & Drop**: "Drag & Drop up to 5 Resume PDFs"
- **File Input**: Accepts multiple PDF files only
- **Max Files**: 5 PDFs per batch
- **Validation**: Real-time feedback on file count and type

### 2. File Queue (New)
- **Per-File Display**: Shows each file with status badge
- **Status Badges**: 
  - `queued` (gray) - Waiting to upload
  - `uploading` (blue) - Being sent to server
  - `extracting` (purple) - PDF text extraction
  - `analyzing` (indigo) - LLM analysis in progress
  - `completed` (green) - ✓ Analysis complete
  - `failed` (red) - ✗ Processing failed

### 3. Batch Comparison View (New)
- **Status**: Show after batch completes
- **Comparison Table**:
  - **Candidate**: Filename + Document ID (for audit)
  - **Status**: Success/Failed badge
  - **Overall Score**: Color-coded (green ≥75, orange 50-75, red <50)
  - **Matched Skills**: Green tags (matches job requirements)
  - **Missing Skills**: Red tags (gaps to address)
  - **Experience**: Auto-assessed from resume
  - **Fit Assessment**: LLM evaluation

### 4. Sort Controls
- **Sort by Score**: Descending (best fit first) ⭐⭐⭐
- **Sort by Name**: Alphabetical (A-Z)

## Data Models

### Backend Request

```python
POST /batch-analyze

Content-Type: multipart/form-data
├── files: List[UploadFile]  # 1-5 PDF files
├── job_requirements: str     # Shared for all documents
└── batch_id: str             # Unique batch identifier
```

### Backend Response

```python
{
  "batch_id": "batch_1234567890",
  "documents": [
    {
      "document_id": "doc_batch_1234567890_1_...",
      "filename": "candidate1.pdf",
      "status": "success",
      "extraction": {
        "raw_text_preview": "...",
        "char_count": 2500,
        "confidence": 0.95,
        "document_type": "Digital"
      },
      "analysis": {
        "resume_json": { /* structured resume */ },
        "resume_markdown": "# Candidate Name\n...",
        "llm_analysis": {
          "overall_score": 82,
          "matched_skills": ["Python", "REST API", "SQL"],
          "missing_skills": ["Kubernetes", "ML"],
          "experience_assessment": "5 years full-stack development",
          "fit_assessment": "Strong technical fit for Senior role"
        }
      }
    },
    // ... more documents
  ],
  "job_requirements_used": true,
  "job_requirements_provided": true,
  "documents_count": 3,
  "success_count": 3,
  "failed_count": 0,
  "processing_time": 45.23,
  "success": true
}
```

## Key Features

### ✅ True Batch Processing
- **Not** sequential client-side loops
- **Actual** backend batch endpoint
- **Parallel** document processing (where possible)
- **Efficient** resource utilization

### ✅ Shared Job Requirements
- **One** job requirements input
- **Applied** to **all** documents in batch
- **Context** consistent across candidates
- **Comparison** is fair and accurate

### ✅ Per-Document Isolation
- **Independent** processing per resume
- **Unique** document_id assignment
- **Failure** in one doesn't stop others
- **Granular** error reporting

### ✅ Real-Time Status Tracking
- **Per-file** status badges
- **Live** updates as processing advances
- **Color-coded** for quick scanning
- **Accessible** in logs and UI

### ✅ Structured Comparison
- **Side-by-side** candidate comparison
- **Sortable** by multiple fields
- **Color-coded** scores for quick assessment
- **Detailed** skill matching analysis

### ✅ Audit Trail
- **Unique** document_id per file
- **Batch_id** groups related documents
- **Timestamp** tracking
- **Hash verification** for job requirements
- **Processing logs** for each document

## Processing Pipeline

For each document in the batch:

```
1. VALIDATION
   ├── Check file is PDF
   ├── Check file size is reasonable
   └── Generate unique document_id

2. PDF EXTRACTION
   ├── Extract text using PyMuPDF + fallback engines
   ├── Handle OCR if scanned document
   ├── Measure confidence score
   └── Extract metadata (page count, etc.)

3. NLP ANALYSIS
   ├── Run spaCy NLP pipeline
   ├── Extract: experience, education, skills, etc.
   ├── Named Entity Recognition (persons, orgs, locations)
   └── Semantic understanding

4. RESUME RECONSTRUCTION
   ├── Combine raw text + NLP results
   ├── Generate structured JSON resume
   ├── Generate readable Markdown version
   └── Extract key sections

5. LLM ANALYSIS
   ├── Provide job requirements context (MANDATORY)
   ├── Run LLM scoring with temperature=0.3 (deterministic)
   ├── Analyze: skills match, experience fit, seniority
   ├── Generate: overall_score, matched_skills, missing_skills
   ├── Produce: fit_assessment and recommendations
   └── Verify job requirements were used

6. RESPONSE COMPILATION
   ├── Collect all extraction data
   ├── Collect all analysis results
   ├── Track processing time per document
   ├── Handle any errors gracefully
   └── Return document result
```

## Job Requirements Handling

### Frontend
1. User enters job requirements in textarea
2. Text is captured in `state.jobRequirements`
3. On batch upload, passed to backend via FormData
4. Displayed as log: "✓ Shared Job Requirements: X words"

### Backend
1. Receives job_requirements as string from FormData
2. Passes to LLM analyzer for each document
3. LLM generates mandatory section: "DO NOT IGNORE - MANDATORY"
4. Enforced with `temperature=0.3` and `format=json`
5. Verification flag: `job_requirements_used=True`
6. SHA256 hash for audit trail

### LLM (Ollama qwen2.5:7b)
1. Receives job requirements in prompt
2. Mandatory section: "MANDATORY: DO NOT IGNORE..."
3. Instructions: "Consider these requirements in all analysis"
4. Must cite which requirements are matched/missing
5. Score reflects both job fit AND general quality

## Error Handling

### Validation Errors
- **Empty batch**: "No files provided" → 400
- **Too many files**: "Maximum 5 files allowed per batch" → 400
- **Non-PDF file**: "File 'X' is not a PDF" → 400

### Processing Errors
- **PDF extraction fails**: Document marked `status=failed`, error message included
- **NLP analysis fails**: Continues with next document, records error
- **LLM call fails**: Falls back to generic analysis or marks failed
- **One document fails**: Others continue processing, batch still returns

### Recovery
- **Partial success**: `success_count=X, failed_count=Y` in response
- **Retry capability**: Each document_id is unique, can retry individually
- **Detailed logs**: `processing_logs` field tracks what happened

## Usage Examples

### JavaScript Frontend
```javascript
// User selects 3 PDFs and enters job requirements
const files = [resume1.pdf, resume2.pdf, resume3.pdf];
state.jobRequirements = "Senior Engineer - Python, AWS, ...";

// Click upload button → triggers handleFiles() → uploadBatch()
// Frontend calls: POST /batch-analyze with FormData

// Response contains per-document results:
batchResult.documents[0] = {
  document_id: "doc_batch_1234567890_1_...",
  filename: "resume1.pdf",
  status: "success",
  analysis: {
    llm_analysis: {
      overall_score: 85,
      matched_skills: ["Python", "AWS", "REST API"],
      missing_skills: ["Kubernetes"]
    }
  }
}

// Render comparison table with sort buttons
renderBatchResults(batchResult);
```

### Python Backend
```python
# Endpoint receives multipart/form-data
@app.post("/batch-analyze")
async def batch_analyze(
    files: List[UploadFile] = File(...),
    job_requirements: str = "",
    batch_id: str = ""
):
    # Validate input
    # For each file:
    #   - Extract PDF
    #   - Run NLP
    #   - Reconstruct resume
    #   - Run LLM with job_requirements
    # Return BatchAnalyzeResponse
```

## Testing

### Run Batch Test
```bash
python test_batch_analysis.py
```

This will:
1. Find PDF files in workspace
2. Create batch request with up to 5 PDFs
3. Send to `/batch-analyze` endpoint
4. Display summary of results
5. Save results to `batch_test_results.json`

## Performance Considerations

### Processing Time
- **Per document**: ~15-30 seconds (depending on resume length)
- **Batch of 5**: ~75-150 seconds total
- **Bottleneck**: NLP model initialization, LLM API calls

### Optimization Tips
- **Reuse models**: Backend loads spaCy/transformers once at startup
- **Async processing**: Backend processes documents sequentially (can be parallelized)
- **Streaming**: LLM responses are streamed for real-time feedback
- **Frontend**: Show per-file progress to keep user engaged

### Memory Usage
- **Per document**: ~50-100MB (spaCy models, LLM context)
- **Batch of 5**: ~250-500MB peak
- **Cleanup**: Temporary PDF files deleted after processing

## Limitations & Future Enhancements

### Current Limitations
- Max 5 files per batch (by design)
- Sequential processing (not parallel)
- Single job requirements per batch
- Results stored in response only (not persisted)

### Future Enhancements
1. **Parallel Processing**: Use asyncio.gather() for true parallelization
2. **Result Persistence**: Save batch results to database
3. **Resume Storage**: Store successful extractions for future reference
4. **Bulk Download**: Export comparison view as PDF/Excel
5. **Candidate Ranking**: AI-powered ranking with explanation
6. **Interview Recommendations**: Generate interview focus areas per candidate
7. **Historical Tracking**: Compare batches over time
8. **Webhook Notifications**: Notify when batch completes
9. **Streaming Results**: Stream document results as they complete
10. **Advanced Filtering**: Filter comparison by score, skills, experience, etc.

## Files Modified/Created

### Backend
- **main.py**: Added `/batch-analyze` endpoint, BatchAnalyzeResponse model, DocumentResult model

### Frontend  
- **index.html**: Added file-queue display, batch-comparison section, sort buttons
- **js/main.js**: Updated handleFiles(), added uploadBatch(), renderBatchResults(), sortBatchResults()
- **styles.css**: Added CSS for comparison-table, skill-tags, badges

### Tests
- **test_batch_analysis.py**: New comprehensive batch testing script

### Documentation
- **BATCH_PROCESSING.md**: This file (detailed feature documentation)

## Support & Troubleshooting

### Backend won't start?
- Check Ollama is running: `ollama serve`
- Verify port 8002 is available
- Check Python dependencies: `pip install -r requirements.txt`

### Batch upload fails?
- Check browser console for error messages
- Verify PDFs are valid: `pdfinfo resume.pdf`
- Check backend logs for detailed error
- Try single file upload first to isolate issue

### Results look incomplete?
- Check processing time - may still be running
- Verify job requirements were entered
- Check individual document errors in response
- Review backend logs for specific failures

### Performance is slow?
- NLP model loading is slow on first run (30-60s startup)
- LLM calls are network-bound (depends on Ollama)
- Try smaller batch (2-3 files) to test speed
- Consider offline LLM models for faster inference

