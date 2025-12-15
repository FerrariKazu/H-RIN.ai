# 🚀 Quick Startup Guide

## Fixed Issues

✅ **Lazy model loading** - Spacy model now loads on first API call, not at startup
✅ **Removed heavy models** - Removed facebook/bart-large-mnli (1.6GB) that was blocking
✅ **Better logging** - Shows exact initialization progress
✅ **Startup test** - Run `test_backend.py` to verify responsiveness

---

## Starting the Backend

### Method 1: Using run.bat (Recommended)
```bash
.\run.bat
```
This will:
- Start Backend on http://localhost:8001
- Start Frontend on http://localhost:3000
- Show initialization progress

### Method 2: Direct
```bash
python backend/main.py
```

---

## Monitoring Startup

The backend should now start **instantly** and show:
```
2024-12-15 14:30:00 - HR_Buddy_Backend - INFO - Initializing pipeline components...
2024-12-15 14:30:00 - HR_Buddy_Backend - INFO -   1. Initializing PDF Processor...
2024-12-15 14:30:00 - HR_Buddy_Backend - INFO -   ✓ PDF Processor ready
2024-12-15 14:30:00 - HR_Buddy_Backend - INFO -   2. Initializing NLP Engine (lazy load)...
2024-12-15 14:30:00 - HR_Buddy_Backend - INFO -   ✓ NLP Engine ready
2024-12-15 14:30:00 - HR_Buddy_Backend - INFO -   3. Initializing Resume Reconstructor...
2024-12-15 14:30:00 - HR_Buddy_Backend - INFO -   ✓ Resume Reconstructor ready
2024-12-15 14:30:00 - HR_Buddy_Backend - INFO -   4. Initializing LLM Analyzer...
2024-12-15 14:30:00 - HR_Buddy_Backend - INFO -   ✓ LLM Analyzer ready
2024-12-15 14:30:00 - HR_Buddy_Backend - INFO - ✓ All components initialized successfully
============================================================
HR Buddy Backend - Starting
============================================================
Backend: http://localhost:8001
API Docs: http://localhost:8001/docs
Health: http://localhost:8001/health
============================================================
INFO:     Uvicorn running on http://0.0.0.0:8001
```

**If you see this, the backend is ready!**

---

## Verifying Backend is Running

### Option 1: Use test script
```bash
python test_backend.py
```
This will:
- Check if backend responds
- Show health status
- Print API endpoints

### Option 2: Check health endpoint
```bash
# In another terminal or browser
curl http://localhost:8001/health
```

Should return:
```json
{
  "status": "ok",
  "version": "3.0",
  "service": "HR Buddy Resume Processing API",
  "backend_port": 8001,
  "frontend_port": 3000
}
```

### Option 3: Open in browser
```
http://localhost:8001/health
http://localhost:8001/docs
```

---

## What's Different Now?

### Before (Hanging)
- Spacy model loaded at startup (~20-30 seconds)
- Zero-shot classifier loaded at startup (~2-3 minutes!)
- Long wait before server was ready

### After (Fast)
- Models load **on first use** (lazy loading)
- Backend starts **instantly**
- First API call takes slightly longer
- Much better user experience

---

## Model Loading Timeline

- **Backend startup**: Instant (< 1 second)
- **First `/upload` call**: +10-15 seconds (Spacy loads)
- **Subsequent calls**: Normal speed (models already loaded)

---

## Troubleshooting

### Backend window closes immediately
- Check if there's an error
- Run directly: `python backend/main.py`
- Look for import errors or missing packages

### Port 8001 already in use
```bash
# Check what's using port 8001
netstat -ano | findstr :8001

# Kill the process (Windows)
taskkill /PID <PID> /F
```

### Spacy model missing
- Backend will warn but continue
- On first API call, it will try to load
- If missing, install with: `python -m spacy download en_core_web_sm`

### Slow first API call
- This is normal - Spacy model loading
- Subsequent calls will be fast
- You can pre-load by calling `/health` after backend starts

---

## Next Steps

1. **Start backend**: `.\run.bat` or `python backend/main.py`
2. **Verify running**: `python test_backend.py` or check http://localhost:8001/health
3. **Test API**: Visit http://localhost:8001/docs
4. **Upload PDF**: Use the Swagger UI or integrate with frontend

---

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Health check |
| POST | `/upload` | Extract text from PDF |
| POST | `/analyze` | Analyze extracted text |
| POST | `/process` | End-to-end processing |
| GET | `/docs` | API documentation |

---

**Last Updated:** December 15, 2025
**Version:** 3.0 - Production
**Status:** ✅ Ready to use
