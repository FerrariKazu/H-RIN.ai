# HR Buddy - Environment & Model Setup Guide

## Quick Start

### Option 1: Automatic Setup (Recommended)
Run the setup script which handles everything:
```
setup.bat
```

This script:
1. Creates a Python virtual environment (.venv)
2. Installs all dependencies from requirements.txt
3. Downloads the SpaCy NLP model (en_core_web_sm)
4. Validates the installation

### Option 2: Manual Setup

#### Step 1: Create Virtual Environment
```powershell
python -m venv venv
```

#### Step 2: Activate Virtual Environment
```powershell
venv\Scripts\activate.bat
```

#### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

#### Step 4: Download SpaCy Model
```powershell
python -m spacy download en_core_web_sm
```

#### Step 5: Verify Installation
```powershell
python diagnose_spacy.py
```

## Running the Application

After setup is complete:

```powershell
run.bat
```

This starts:
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **Frontend**: http://localhost:3000
- **Health Check**: http://localhost:8001/health

## Environment Structure

```
Project Root/
├── venv/                    # Virtual environment (created by setup.bat)
├── backend/                 # FastAPI backend
│   ├── main.py             # API entry point
│   ├── pipeline/
│   │   ├── pdf_processor.py
│   │   ├── nlp_engine_v2.py
│   │   ├── resume_reconstructor.py
│   │   └── llm_analyzer.py
│   └── ...
├── frontend/               # Web interface (if present)
├── requirements.txt        # Python dependencies
├── setup.bat               # Setup script
├── run.bat                 # Runtime script
└── diagnose_spacy.py       # Diagnostic tool
```

## Troubleshooting

### SpaCy Model Not Found
1. Check if model is installed: `python -m spacy info`
2. Reinstall model: `python -m spacy download en_core_web_sm`
3. Run diagnostic: `python diagnose_spacy.py`

### Dependencies Missing
```powershell
pip install -r requirements.txt --upgrade
```

### Backend Won't Start
1. Check the backend window for error messages
2. Verify port 8001 is available
3. Run from the project root directory

### Port Already in Use
- **Backend (8001)**: Find and kill process on port 8001, then restart `run.bat`
- **Frontend (3000)**: Find and kill process on port 3000, then restart `run.bat`

## Technology Stack

- **Framework**: FastAPI with Uvicorn
- **PDF Processing**: PyMuPDF, pdfminer.six, pypdf, camelot-py, pytesseract
- **NLP**: SpaCy (en_core_web_sm)
- **LLM Integration**: OpenAI, Ollama support
- **Data Processing**: pandas, numpy, scikit-learn
- **Frontend**: HTTP server (if frontend exists)

## Python Version
- Required: Python 3.8+
- Tested with: Python 3.13.9

## Notes

- The .venv directory is created locally and not committed to git
- All models are downloaded into the .venv on first run
- The application uses lazy loading for models to optimize startup time
- Ensure you have internet access for initial setup to download models
