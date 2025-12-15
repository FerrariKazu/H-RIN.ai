# Quick Reference - Job Requirements Enforcement

## 🚀 Quick Start

### For Users
1. **Optional**: Enter job requirements in textarea (or leave empty)
2. **Submit**: Upload resume
3. **View**: Check "Analysis Context" section to see:
   - ✅ Job requirements used (Yes/No)
   - 📋 SHA256 hash for verification
   - 📄 Full job requirements text

### For Developers

#### Check if Job Requirements Are Working
```bash
# Run test
python test_job_requirements_enforcement.py

# Look for: ✓ ALL CHECKS PASSED
```

#### Debug Job Requirements in Logs
```python
# Backend logs show:
[JOB_REQS] Provided: 150 words
[VERIFICATION] Job requirements used: true
[LLM] Calling Ollama with deterministic settings (temp=0.3, format=json)
```

#### Verify Response Has All Fields
```python
llm_analysis = response["llm_analysis"]

required_fields = [
    "job_requirements_used",      # ✅ bool
    "job_requirements_hash",      # ✅ SHA256
    "job_requirements_raw",       # ✅ full text
    "job_alignment_summary",      # ✅ paragraph
    "matched_requirements",       # ✅ array
    "missing_requirements",       # ✅ array
    "role_fit_verdict"           # ✅ YES|MAYBE|NO
]

for field in required_fields:
    assert field in llm_analysis, f"Missing: {field}"
```

---

## 🎯 What Got Changed

### 1. Frontend (`frontend/js/main.js`)
```javascript
// BEFORE: job_requirements: state.jobRequirements || null
// AFTER: job_requirements: jobReqsText (always sent, even if empty)
```

### 2. Backend Validation (`backend/main.py`)
```python
# NEW: Validation of job_requirements receipt
if job_reqs_text.strip():
    logger.info(f"✓ Job requirements provided: {job_word_count} words")
```

### 3. LLM Prompt (`backend/pipeline/llm_analyzer.py`)
```
=== TARGET JOB REQUIREMENTS (DO NOT IGNORE - MANDATORY) ===
[text]
=== END OF JOB REQUIREMENTS ===
```

### 4. LLM Parameters (`backend/pipeline/llm_analyzer.py`)
```python
# ENFORCED: temperature=0.3, format="json", stream=True
```

### 5. Response Flags (`backend/pipeline/llm_analyzer.py`)
```python
analysis["job_requirements_used"] = bool
analysis["job_requirements_hash"] = sha256
analysis["job_requirements_raw"] = text
```

### 6. UI Display (`frontend/js/main.js`)
```javascript
// NEW: Display job requirements in "Analysis Context"
```

---

## ✅ Verification Checklist

- [ ] Frontend always sends `job_requirements` in request
- [ ] Backend validates receipt
- [ ] LLM receives "DO NOT IGNORE" section
- [ ] LLM temperature set to 0.3
- [ ] LLM format set to "json"
- [ ] Response includes `job_requirements_used` flag
- [ ] Response includes SHA256 `job_requirements_hash`
- [ ] Response includes `job_requirements_raw` text
- [ ] UI displays job requirements context
- [ ] Test passes: `python test_job_requirements_enforcement.py`

---

## 🔍 Common Issues & Fixes

### Issue: `job_requirements_used` is False but requirements were provided
**Fix**: Check LLM logs - ensure temperature=0.3 and format="json" are set

### Issue: Hash doesn't match
**Fix**: Verify no whitespace changes - SHA256 is character-exact

### Issue: Missing `matched_requirements` in response
**Fix**: Check if job requirements were actually provided (not empty string)

### Issue: UI doesn't show "Analysis Context"
**Fix**: Ensure `id="analysis-context"` div exists in HTML

---

## 📊 Example Response

```json
{
    "llm_analysis": {
        "job_requirements_used": true,
        "job_requirements_hash": "a3f5c8e2d1b4c7f0a9e2c5f8b1d4a7e0c3f6a9b2c5d8e1f4a7b0c3d6e9f2a5",
        "job_requirements_raw": "Senior Full Stack Engineer...",
        "job_alignment_summary": "Candidate is well-aligned with role...",
        "matched_requirements": [
            {
                "requirement": "React",
                "evidence": "5+ years React development",
                "strength": "Strong - exceeds requirement"
            }
        ],
        "missing_requirements": [
            {
                "requirement": "Kubernetes",
                "impact": "Cannot manage K8s deployments",
                "severity": "CRITICAL"
            }
        ],
        "role_fit_verdict": {
            "recommendation": "MAYBE",
            "confidence": 72,
            "rationale": "Strong technical match but missing DevOps skills"
        }
    }
}
```

---

## 🔐 Security Notes

- **Hash**: Use SHA256 to verify exact job requirements text used
- **Raw Text**: Included in response for full traceability
- **Logs**: All steps logged for audit trail
- **Flags**: Explicit boolean to show if requirements were used

---

## 📝 Files Modified

| File | Lines | Purpose |
|------|-------|---------|
| `frontend/js/main.js` | 155-165, 287-330 | Always send, display context |
| `frontend/index.html` | Added div | Analysis context container |
| `backend/main.py` | 350-385 | Validation & logging |
| `backend/pipeline/llm_analyzer.py` | 104-155, 162-252, 257-320 | Prompt enforcement, verification |
| `backend/pipeline/job_requirements_parser.py` | NEW | Parsing utility |
| `test_job_requirements_enforcement.py` | NEW | Test suite |

---

## 🎓 Architecture

```
User Input
    ↓
Frontend (always send job_requirements)
    ↓
Backend /analyze endpoint
    ├→ Validate job_requirements
    ├→ Log presence/absence
    └→ Pass to LLM
    ↓
LLM Analyzer
    ├→ Insert mandatory section
    ├→ Add explicit instructions
    ├→ Set temperature=0.3, format=json
    └→ Generate structured output
    ↓
Response with Verification Flags
    ├→ job_requirements_used: bool
    ├→ job_requirements_hash: SHA256
    ├→ job_requirements_raw: text
    └→ job_alignment_summary: paragraph
    ↓
Frontend Display
    └→ Show in "Analysis Context"
```

---

## 📞 Support

**Issue**: Not working?
**Check**:
1. `backend/pipeline/llm_analyzer.py` has `temperature=0.3`
2. `backend/pipeline/llm_analyzer.py` has `format="json"`
3. `backend/main.py` validate section is present
4. `frontend/js/main.js` always sends `job_requirements`
5. Ollama is running with qwen2.5 model loaded

**Test**: `python test_job_requirements_enforcement.py`

---

**Last Updated**: December 15, 2025
**Status**: ✅ COMPLETE
