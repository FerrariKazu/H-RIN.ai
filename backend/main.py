"""
HR Buddy Backend API - Production v3.0
Complete resume processing and analysis pipeline
"""

import shutil
import os
import sys
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import logging
from datetime import datetime
import traceback
from contextlib import asynccontextmanager

# Allow importing from root directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging with more verbose output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("HR_Buddy_Backend")

# Force flush stdout/stderr
sys.stdout.flush()
sys.stderr.flush()

# Global component instances
pdf_processor = None
nlp_engine = None
resume_reconstructor = None
llm_analyzer = None
components_initialized = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events
    This replaces the deprecated @app.on_event decorators
    """
    global pdf_processor, nlp_engine, resume_reconstructor, llm_analyzer, components_initialized
    
    # STARTUP
    logger.info("=" * 70)
    logger.info("🚀 HR BUDDY BACKEND - STARTING INITIALIZATION")
    logger.info("=" * 70)
    sys.stdout.flush()
    
    try:
        # Import pipeline components
        logger.info("📦 Step 1/5: Importing pipeline components...")
        sys.stdout.flush()
        
        from backend.pipeline.pdf_processor import PDFProcessor
        from backend.pipeline.nlp_engine_v2 import NLPEngine
        from backend.pipeline.resume_reconstructor import ResumeReconstructor
        from backend.pipeline.llm_analyzer import LLMAnalyzer
        
        logger.info("✓ All pipeline components imported successfully")
        sys.stdout.flush()
        
        # Initialize PDF Processor (fast)
        logger.info("📄 Step 2/5: Initializing PDF Processor...")
        sys.stdout.flush()
        pdf_processor = PDFProcessor()
        logger.info("✓ PDF Processor ready")
        sys.stdout.flush()
        
        # Initialize Resume Reconstructor (fast)
        logger.info("🔧 Step 3/5: Initializing Resume Reconstructor...")
        sys.stdout.flush()
        resume_reconstructor = ResumeReconstructor()
        logger.info("✓ Resume Reconstructor ready")
        sys.stdout.flush()
        
        # Initialize LLM Analyzer (fast if no immediate API calls)
        logger.info("🤖 Step 4/5: Initializing LLM Analyzer...")
        sys.stdout.flush()
        llm_analyzer = LLMAnalyzer(model="qwen2.5:7b-instruct-q4_K_M")
        logger.info("✓ LLM Analyzer ready with Ollama model: qwen2.5:7b-instruct-q4_K_M")
        sys.stdout.flush()
        
        # Initialize NLP Engine (SLOW - this is likely where it hangs)
        logger.info("🧠 Step 5/5: Initializing NLP Engine (this may take 30-60 seconds)...")
        logger.info("    Loading spaCy models and transformers...")
        logger.info("    Please wait - downloading models if first run...")
        sys.stdout.flush()
        
        nlp_engine = NLPEngine()
        
        logger.info("✓ NLP Engine ready")
        sys.stdout.flush()
        
        components_initialized = True
        
        logger.info("=" * 70)
        logger.info("✅ ALL COMPONENTS INITIALIZED SUCCESSFULLY")
        logger.info("=" * 70)
        logger.info("🌐 Backend: http://localhost:8002")
        logger.info("📚 API Docs: http://localhost:8002/docs")
        logger.info("💚 Health: http://localhost:8002/health")
        logger.info("=" * 70)
        sys.stdout.flush()
        
    except ImportError as e:
        logger.error(f"❌ Import failed: {e}")
        logger.error("Traceback:")
        logger.error(traceback.format_exc())
        sys.stdout.flush()
        raise
    
    except Exception as e:
        logger.error(f"❌ Component initialization failed: {e}")
        logger.error(traceback.format_exc())
        sys.stdout.flush()
        raise
    
    # Application is now running
    yield
    
    # SHUTDOWN
    logger.info("=" * 70)
    logger.info("🛑 HR BUDDY BACKEND - SHUTTING DOWN")
    logger.info("=" * 70)
    sys.stdout.flush()

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="HR Buddy API",
    version="3.0 - Production",
    description="Complete resume processing and analysis pipeline",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class UploadResponse(BaseModel):
    """Upload response model"""
    filename: str
    extraction_logs: List[str]
    raw_text_preview: str
    processing_time: float
    document_type: str
    success: bool

class AnalyzeRequest(BaseModel):
    """Analyze request model"""
    filename: str = "resume"
    extracted_text: str
    enable_llm_analysis: bool = True
    job_requirements: Optional[str] = None

class AnalyzeResponse(BaseModel):
    """Analyze response model"""
    filename: str
    resume_markdown: str
    resume_json: Dict
    llm_analysis: Optional[Dict]
    processing_logs: List[str]
    success: bool

# =====================================================
# HELPER FUNCTIONS
# =====================================================

def check_components_ready():
    """Check if all components are initialized"""
    if not components_initialized:
        raise HTTPException(
            status_code=503,
            detail="Backend is still initializing. Please wait a moment and try again."
        )

# =====================================================
# ENDPOINTS
# =====================================================

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "ok" if components_initialized else "initializing",
        "version": "3.0",
        "service": "HR Buddy Resume Processing API",
        "backend_port": 8002,
        "frontend_port": 3000,
        "components_ready": components_initialized,
        "components": {
            "pdf_processor": pdf_processor is not None,
            "nlp_engine": nlp_engine is not None,
            "resume_reconstructor": resume_reconstructor is not None,
            "llm_analyzer": llm_analyzer is not None
        }
    }

@app.get("/")
def root():
    """Root endpoint with API information"""
    return {
        "service": "HR Buddy Resume Processing API",
        "version": "3.0",
        "status": "running" if components_initialized else "initializing",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "upload": "/upload",
            "analyze": "/analyze",
            "process": "/process"
        },
        "documentation": "/docs"
    }

@app.post("/upload")
async def upload_cv(file: UploadFile = File(...)):
    """
    Upload and process PDF resume
    
    Returns:
    - Extracted text
    - Processing logs
    - Document analysis
    """
    check_components_ready()
    
    start_time = datetime.now()
    temp_path = None
    
    try:
        # Validate file
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are accepted"
            )
        
        # Save temporary file
        temp_path = f"temp_{datetime.now().timestamp()}_{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Processing: {file.filename}")
        
        # Process PDF
        extraction_result = pdf_processor.process(temp_path)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Determine document type
        doc_type = "Unknown"
        if extraction_result.needs_ocr:
            doc_type = "Scanned/OCR Required"
        else:
            doc_type = "Digital Text"
        
        # Create response
        response = {
            "filename": file.filename,
            "raw_text": extraction_result.raw_text,
            "raw_text_preview": extraction_result.raw_text[:500] + "..." if len(extraction_result.raw_text) > 500 else extraction_result.raw_text,
            "extraction_logs": extraction_result.logs or [],
            "document_type": doc_type,
            "needs_ocr": extraction_result.needs_ocr,
            "confidence": extraction_result.confidence,
            "engine_used": extraction_result.engine_used,
            "processing_time": processing_time,
            "page_count": extraction_result.metadata.get("page_count", 0) if extraction_result.metadata else 0,
            "metadata": extraction_result.metadata or {},
            "tables_found": len(extraction_result.tables or []),
            "success": True
        }
        
        logger.info(f"✓ Upload processed: {len(extraction_result.raw_text)} chars, confidence {extraction_result.confidence:.2f}")
        
        return response
    
    except Exception as e:
        logger.error(f"✗ Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Cleanup
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass

@app.post("/analyze")
async def analyze_resume(request: AnalyzeRequest):
    """
    Analyze extracted resume text
    
    Returns:
    - Markdown version
    - Structured JSON
    - LLM analysis (optional)
    - Processing logs
    """
    check_components_ready()
    
    start_time = datetime.now()
    all_logs = []
    
    try:
        if not request.extracted_text:
            raise HTTPException(
                status_code=400,
                detail="extracted_text is required"
            )
        
        logger.info(f"Analyzing: {request.filename}")
        
        # Step 1: NLP Extraction
        logger.info("Step 1: NLP extraction...")
        nlp_result = nlp_engine.extract(request.extracted_text)
        all_logs.extend(nlp_result.get("logs", []))
        
        # Step 2: Resume Reconstruction
        logger.info("Step 2: Reconstructing resume...")
        reconstruction_result = resume_reconstructor.reconstruct(
            raw_text=request.extracted_text,
            nlp_data=nlp_result,
            sections=nlp_result.get("sections", {})
        )
        all_logs.extend(reconstruction_result.get("logs", []))
        
        resume_markdown = reconstruction_result.get("markdown", "")
        resume_json = reconstruction_result.get("json", {})
        
        # Step 3: LLM Analysis (optional)
        llm_analysis = None
        if request.enable_llm_analysis:
            logger.info("Step 3: LLM analysis...")
            try:
                # Log if job requirements provided
                if request.job_requirements:
                    logger.info(f"Job requirements provided ({len(request.job_requirements)} chars)")
                
                llm_analysis = llm_analyzer.analyze(
                    resume_json=resume_json,
                    resume_markdown=resume_markdown,
                    raw_text=request.extracted_text,
                    job_requirements=request.job_requirements
                )
                all_logs.extend(llm_analysis.get("logs", []))
            except Exception as e:
                logger.warning(f"LLM analysis failed: {e}, continuing...")
                all_logs.append(f"[WARNING] LLM analysis failed: {e}")
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Create response
        response = {
            "filename": request.filename,
            "resume_markdown": resume_markdown,
            "resume_json": resume_json,
            "llm_analysis": llm_analysis,
            "processing_logs": all_logs,
            "processing_time": processing_time,
            "success": True
        }
        
        logger.info(f"✓ Analysis complete: {len(resume_markdown)} chars markdown, {len(resume_json.get('skills', []))} skills")
        
        return response
    
    except Exception as e:
        logger.error(f"✗ Analysis failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process")
async def process_complete(file: UploadFile = File(...), enable_llm_analysis: bool = True):
    """
    Complete end-to-end processing in one call
    
    1. Upload → Extract text
    2. Analyze → Extract structured data
    3. Reconstruct → Generate Markdown + JSON
    4. Analyze → LLM scoring (optional)
    """
    check_components_ready()
    
    start_time = datetime.now()
    temp_path = None
    
    try:
        # Validate
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files accepted")
        
        # Save temp file
        temp_path = f"temp_{datetime.now().timestamp()}_{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Complete processing: {file.filename}")
        
        # Step 1: PDF Processing
        extraction_result = pdf_processor.process(temp_path)
        raw_text = extraction_result.raw_text
        
        # Step 2: NLP Analysis
        nlp_result = nlp_engine.extract(raw_text)
        
        # Step 3: Reconstruction
        reconstruction_result = resume_reconstructor.reconstruct(
            raw_text=raw_text,
            nlp_data=nlp_result,
            sections=nlp_result.get("sections", {})
        )
        
        # Step 4: LLM Analysis
        llm_analysis = None
        if enable_llm_analysis:
            llm_analysis = llm_analyzer.analyze(
                resume_json=reconstruction_result.get("json", {}),
                resume_markdown=reconstruction_result.get("markdown", ""),
                raw_text=raw_text
            )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Compile all logs
        all_logs = []
        all_logs.extend(extraction_result.logs or [])
        all_logs.extend(nlp_result.get("logs", []))
        all_logs.extend(reconstruction_result.get("logs", []))
        if llm_analysis:
            all_logs.extend(llm_analysis.get("logs", []))
        
        response = {
            "filename": file.filename,
            "raw_text": raw_text,
            "raw_text_preview": raw_text[:300] + "..." if len(raw_text) > 300 else raw_text,
            "resume_markdown": reconstruction_result.get("markdown", ""),
            "resume_json": reconstruction_result.get("json", {}),
            "llm_analysis": llm_analysis,
            "extraction_confidence": extraction_result.confidence,
            "document_type": "Scanned" if extraction_result.needs_ocr else "Digital",
            "processing_logs": all_logs,
            "processing_time": processing_time,
            "success": True
        }
        
        logger.info(f"✓ Complete processing done in {processing_time:.2f}s")
        
        return response
    
    except Exception as e:
        logger.error(f"✗ Complete processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass

@app.get("/docs-info")
def get_docs():
    """API Documentation"""
    return {
        "endpoints": {
            "/health": "Health check",
            "/upload": "Upload PDF and extract text",
            "/analyze": "Analyze extracted text",
            "/process": "Complete end-to-end processing"
        },
        "ports": {
            "backend": 8002,
            "frontend": 3000
        },
        "requirements": {
            "pdf_processing": "PyMuPDF, pdfminer.six, pypdf, camelot",
            "nlp": "spacy, transformers",
            "ocr": "opencv-python, pytesseract (requires Tesseract installed)",
            "llm": "openai (optional)"
        }
    }

# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 HR BUDDY BACKEND - STARTING SERVER")
    print("=" * 70)
    print("⏳ Initializing components... (this may take 30-60 seconds)")
    print("=" * 70)
    sys.stdout.flush()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=False,  # Set to False for production, True only for development
        log_level="info",
        access_log=True
    )