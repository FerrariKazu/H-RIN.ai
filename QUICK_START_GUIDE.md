# 🚀 Quick Start - Complete Setup Guide

## ✅ What's Been Configured

### Frontend (COMPLETE ✅)
- **File**: `frontend/js/main.js` (922 lines)
- **Status**: ✅ Ready to display comparative analysis
- **Features**: Executive summary, rankings, candidate profiles, experience analysis, skill matrix, hiring recommendations

### Backend (COMPLETE ✅)
- **File**: `backend/pipeline/llm_analyzer.py` 
- **Status**: ✅ Optimized for Qwen2.5 comparative analysis
- **Features**: Comparative ranking, strengths/weaknesses comparison, skill coverage matrix, hiring recommendations

---

## 🎯 Quick Start (5 Steps)

### Step 1: Ensure Ollama is Running
```bash
# Terminal 1: Start Ollama service
ollama serve

# Terminal 2: Verify Qwen model is available
ollama list
# Should show: qwen2.5:7b-instruct-q4_K_M
```

### Step 2: Activate Python Environment
```bash
cd "c:\Users\FerrariKazu\Documents\AI Folder\P3\AM-DS-01"
.venv\Scripts\Activate.ps1
```

### Step 3: Test Comparative Analysis (Optional but Recommended)
```bash
python test_comparative_analysis.py
# Should complete in 30-60 seconds and show sample comparative analysis
```

### Step 4: Start Backend Server
```bash
# Terminal 3: Start the backend API
python backend/main.py
# Or: uvicorn backend.main:app --reload --port 8002

# Should show:
# ✓ PDF Processor ready
# ✓ Resume Reconstructor ready  
# ✓ LLM Analyzer ready with Ollama model: qwen2.5:7b-instruct-q4_K_M
# ✓ NLP Engine ready (takes 30-60 seconds)
# ✓ API running on http://localhost:8002
```

### Step 5: Start Frontend Server
```bash
# Terminal 4: Start the frontend dev server
cd frontend
npm run dev
# Should open http://localhost:5173 in browser
```

---

## 💻 System Architecture

```
┌─────────────────────────────────────────────────────────┐
│ USER INTERFACE (Browser)                                │
│ http://localhost:5173                                   │
│ frontend/js/main.js (922 lines)                        │
│ ✅ Displays PASS 1 & PASS 2 results                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ POST /batch-analyze
                     │ 2+ PDF files
                     ↓
┌─────────────────────────────────────────────────────────┐
│ BACKEND API (FastAPI)                                   │
│ http://localhost:8002                                   │
│ backend/main.py                                         │
│ ✅ Handles file upload & validation                    │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ↓ PASS 1                  ↓ PASS 2
┌──────────────────────┐  ┌────────────────────────┐
│ Individual Analysis  │  │ Comparative Analysis   │
│ • Parse PDF          │  │ • Call analyze_compar. │
│ • Extract text       │  │ • Build Qwen prompt    │
│ • LLM analysis       │  │ • Parse JSON response  │
│ • Per-candidate      │  │ • Structure for FE     │
│   scores, skills     │  │ • Rankings, comparison │
└──────────────────────┘  └────────────────────────┘
        │                         │
        └────────────┬────────────┘
                     │
              ┌──────↓──────┐
              │   Ollama    │
              │   Qwen2.5   │
              │   Model     │
              └─────────────┘

Response: {documents[], comparative_analysis{}}
```

---

## 📊 Data Flow Example

**Scenario**: User uploads Alice.pdf, Bob.pdf, Carol.pdf

```
Frontend:
  ↓ Upload 3 PDFs to /batch-analyze

Backend PASS 1:
  Alice.pdf → LLM → {name: "Alice", score: 85, skills: [...]}
  Bob.pdf   → LLM → {name: "Bob", score: 62, skills: [...]}
  Carol.pdf → LLM → {name: "Carol", score: 78, skills: [...]}

Backend PASS 2 (NEW!):
  Qwen: "Compare these 3 candidates..."
  Qwen Response:
  {
    "comparative_ranking": [
      {"document_id": "doc_1", "rank": 1, "score": 85, "reason": "Alice best overall..."},
      {"document_id": "doc_3", "rank": 2, "score": 78, "reason": "Carol strong DevOps..."},
      {"document_id": "doc_2", "rank": 3, "score": 62, "reason": "Bob frontend specialist..."}
    ],
    "strengths_comparison": "Alice dominates backend... Bob excels frontend... Carol expert infrastructure...",
    "weaknesses_comparison": "Alice lacks frontend skills... Bob no cloud experience... Carol learning app dev...",
    "skill_coverage_matrix": {...},
    "hiring_recommendations": {...},
    ...
  }

Frontend Display:
  PASS 1: Individual Analysis Table
    ├─ Alice: 85/100, Skills: [...], Fit: STRONG
    ├─ Bob: 62/100, Skills: [...], Fit: MODERATE  
    └─ Carol: 78/100, Skills: [...], Fit: STRONG

  PASS 2: Comparative Analysis
    ├─ Executive Summary: "Alice is strongest overall..."
    ├─ Rankings: #1 Alice, #2 Carol, #3 Bob
    ├─ Candidate Profiles: [Alice card][Bob card][Carol card]
    ├─ Experience Analysis: [Experience per candidate]
    ├─ Skill Coverage: [Matrix showing covered/missing skills]
    └─ Hiring Recommendations: [Action items per candidate]
```

---

## 🔄 Complete System Verification

### Checklist Before Testing

- [ ] Python 3.9+ installed
- [ ] Node.js 16+ installed
- [ ] Ollama installed and running
- [ ] Qwen2.5 model downloaded: `ollama pull qwen2.5:7b-instruct-q4_K_M`
- [ ] Backend dependencies installed: `pip install -r requirements.txt`
- [ ] Frontend dependencies installed: `cd frontend && npm install`
- [ ] All files checked for syntax errors

### Verification Commands

```bash
# Check Ollama
ollama list

# Check Python environment
python --version

# Check Node.js
node --version

# Check backend syntax
python -m py_compile backend/main.py
python -m py_compile backend/pipeline/llm_analyzer.py

# Check frontend syntax
cd frontend
npx eslint js/main.js

# Test comparative analysis
cd ..
python test_comparative_analysis.py
```

---

## 🎮 Testing the System

### Test 1: Single PDF Upload (PASS 1 Only)
1. Open http://localhost:5173
2. Upload 1 PDF resume
3. Wait for analysis
4. Verify "Candidate Analysis" displays with score, skills, fit

**Expected**: PASS 1 results only (no comparative section)

### Test 2: Batch Upload (PASS 1 + PASS 2)
1. Open http://localhost:5173
2. Upload 2+ PDF resumes
3. Wait for analysis (takes longer for PASS 2)
4. Verify both sections display

**Expected PASS 1**:
- Table with all candidates
- Individual scores and skills
- Status indicators

**Expected PASS 2**:
- Executive Summary (gradient box)
- Rankings table with all candidates
- Candidate Profiles for each person
- Experience Analysis section
- Skill Coverage Matrix
- Hiring Recommendations
- Strengths/Weaknesses Comparison

---

## 📋 Expected Output Sizes

| Component | PASS 1 Time | PASS 2 Time | Total |
|-----------|------------|-----------|-------|
| Single PDF | 10-15s | N/A | 10-15s |
| 2 PDFs | 20-30s | 30-60s | 50-90s |
| 3 PDFs | 30-45s | 30-60s | 60-105s |
| 5 PDFs | 50-75s | 30-60s | 80-135s |

**Note**: PASS 1 is per-file (linear), PASS 2 is single LLM call (fixed time)

---

## 🐛 Troubleshooting

### Issue: "Ollama not available"
```bash
# Solution: Start Ollama service
ollama serve
# Then verify model
ollama list
```

### Issue: "Model qwen2.5 not found"
```bash
# Solution: Pull the model
ollama pull qwen2.5:7b-instruct-q4_K_M
# Takes ~7GB disk space, ~5-10 minutes
```

### Issue: Backend hangs on startup
```bash
# The NLP Engine initialization can take 30-60 seconds
# This is normal - be patient
# Once you see "✓ NLP Engine ready", it's done

# If it hangs longer, check logs for errors
# Backend logs are detailed and show progress
```

### Issue: Frontend doesn't show comparative section
```bash
# Ensure you're uploading 2+ files in BATCH mode
# Check backend logs for PASS 2 completion
# Verify comparative_analysis is in response (browser DevTools → Network)
```

### Issue: Qwen response is invalid JSON
```bash
# Prompt might be too aggressive
# Try:
# 1. Check backend logs for "Failed to parse comparative JSON"
# 2. Manually test: python test_comparative_analysis.py
# 3. Review prompt in backend/pipeline/llm_analyzer.py line ~763
```

---

## 📚 Key Files Reference

| File | Purpose | Status |
|------|---------|--------|
| frontend/js/main.js | Frontend UI & rendering | ✅ 922 lines |
| backend/main.py | FastAPI server | ✅ Ready |
| backend/pipeline/llm_analyzer.py | LLM analysis (PASS 1 & 2) | ✅ Enhanced |
| test_comparative_analysis.py | Validation script | ✅ Created |
| requirements.txt | Python dependencies | ✅ Check installed |
| frontend/package.json | Node dependencies | ✅ Check installed |

---

## 🎓 Understanding the Two-Pass System

**PASS 1: Individual Analysis**
- Each resume analyzed independently
- Extracts: skills, experience, fit score
- Uses: spaCy NLP + Qwen LLM
- Runs: In parallel (one per file)
- Output: Per-candidate analysis

**PASS 2: Comparative Analysis** 
- All resumes analyzed together
- Extracts: comparative rankings, relative strengths/weaknesses, skill gaps
- Uses: Qwen LLM with all candidates in context
- Runs: Single LLM call with all candidates
- Output: Cross-candidate comparison

**Frontend Display**:
- PASS 1 → Individual candidate table (always shown)
- PASS 2 → Comparative analysis section (only if 2+ candidates)

---

## ✨ Key Features Summary

### Frontend Features (frontend/js/main.js)
- ✅ Batch PDF upload with validation
- ✅ Individual analysis table (PASS 1)
- ✅ Executive summary (PASS 2)
- ✅ Candidate rankings (PASS 2)
- ✅ Candidate profiles (PASS 2)
- ✅ Experience analysis (PASS 2)
- ✅ Skill coverage matrix (PASS 2)
- ✅ Hiring recommendations (PASS 2)
- ✅ Strengths/weaknesses comparison (PASS 2)

### Backend Features (backend/llm_analyzer.py)
- ✅ Qwen2.5 integration via Ollama
- ✅ PASS 1: Per-candidate LLM analysis
- ✅ PASS 2: Comparative Qwen analysis
- ✅ Proper JSON structuring
- ✅ Frontend response formatting
- ✅ Error handling and fallbacks

---

## 🚀 Next Steps

1. **Start all services**:
   ```bash
   # Terminal 1
   ollama serve
   
   # Terminal 2
   cd "c:\Users\FerrariKazu\Documents\AI Folder\P3\AM-DS-01"
   .venv\Scripts\Activate.ps1
   python backend/main.py
   
   # Terminal 3
   cd frontend
   npm run dev
   ```

2. **Test the system**:
   - Open browser to http://localhost:5173
   - Upload 2+ PDF resumes
   - Wait for analysis
   - Verify both PASS 1 and PASS 2 display

3. **Monitor logs**:
   - Backend logs show PASS 1 and PASS 2 progress
   - Browser DevTools show network requests/responses

---

## ✅ System Ready

**Frontend**: ✅ Ready to display comparative analysis  
**Backend**: ✅ Configured to generate comparative analysis with Qwen  
**Integration**: ✅ Complete end-to-end workflow  
**Testing**: ✅ Test script provided for validation  

**Status**: READY FOR PRODUCTION TESTING
