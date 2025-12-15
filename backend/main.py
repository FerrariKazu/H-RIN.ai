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

class DocumentResult(BaseModel):
    """Result for a single document in batch processing (PASS 1)"""
    document_id: str
    filename: str
    status: str  # 'success' or 'failed'
    extraction: Optional[Dict] = None
    analysis: Optional[Dict] = None
    error: Optional[str] = None

class ComparativeAnalysisResult(BaseModel):
    """PASS 2: Comparative analysis across all candidates"""
    comparative_ranking: List[Dict] = []
    strengths_comparison: str = ""
    weaknesses_comparison: str = ""
    skill_coverage_matrix: Dict = {}
    strongest_candidate: Dict = {}
    best_skill_coverage: Dict = {}
    hiring_recommendations: Dict = {}
    executive_summary: str = ""

class SingleCVResponse(BaseModel):
    """Response for single CV analysis (PASS 1 ONLY)"""
    mode: str = "single"
    batch_id: str
    job_requirements: str
    job_requirements_used: bool
    candidate: Dict  # Single candidate's PASS 1 analysis
    processing_time: float
    success: bool

class BatchAnalyzeResponse(BaseModel):
    """Response for batch analysis (PASS 1 + optional PASS 2)"""
    mode: str = "batch"
    batch_id: str
    job_requirements: str
    documents: List[DocumentResult]
    comparative_analysis: Optional[ComparativeAnalysisResult] = None
    job_requirements_used: bool
    job_requirements_provided: bool
    documents_count: int
    success_count: int
    failed_count: int
    processing_time: float
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
                # ==== MANDATORY JOB REQUIREMENTS VALIDATION ====
                job_reqs_text = request.job_requirements or ""
                
                if job_reqs_text.strip():
                    job_word_count = len(job_reqs_text.split())
                    logger.info(f"✓ Job requirements provided: {job_word_count} words, {len(job_reqs_text)} chars")
                    all_logs.append(f"[JOB_REQS] Provided: {job_word_count} words")
                else:
                    logger.info("⚠ No job requirements provided - will perform generic analysis")
                    all_logs.append("[JOB_REQS] None provided - generic analysis mode")
                
                llm_analysis = llm_analyzer.analyze(
                    resume_json=resume_json,
                    resume_markdown=resume_markdown,
                    raw_text=request.extracted_text,
                    job_requirements=job_reqs_text
                )
                all_logs.extend(llm_analysis.get("logs", []))
                
                # ==== VERIFY JOB REQUIREMENTS WERE USED ====
                if llm_analysis:
                    job_used = llm_analysis.get("job_requirements_used", False)
                    job_hash = llm_analysis.get("job_requirements_hash", "")
                    
                    if job_reqs_text.strip():
                        if job_used:
                            logger.info(f"✓ Job requirements ENFORCED in analysis (hash: {job_hash[:8]}...)")
                            all_logs.append(f"[VERIFICATION] Job requirements successfully integrated")
                        else:
                            logger.warning(f"⚠ Job requirements may not have been fully used (hash: {job_hash[:8]}...)")
                            all_logs.append(f"[WARNING] Job requirements analysis may be incomplete")
                    else:
                        logger.info("ℹ Generic analysis mode (no job requirements)")
                        all_logs.append("[INFO] Generic analysis completed")
                
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

@app.post("/batch-analyze")
async def batch_analyze(
    files: List[UploadFile] = File(...),
    job_requirements: str = "",
    batch_id: str = ""
):
    """
    Analyze one or more PDF resumes - AUTOMATIC MODE DETECTION
    
    - 1 file → PASS 1 only (single-CV mode, no comparison)
    - 2-5 files → PASS 1 + PASS 2 (batch mode with comparison)
    
    Response structure depends on file count:
    - mode: "single" → {mode, batch_id, candidate, ...}
    - mode: "batch" → {mode, batch_id, documents, comparative_analysis, ...}
    """
    check_components_ready()
    
    start_time = datetime.now()
    temp_files = []
    documents_results = []
    
    try:
        # STEP 0: INPUT NORMALIZATION - Always convert to array
        if not files or len(files) == 0:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Normalize to list (should already be list, but ensure it)
        file_list = list(files) if isinstance(files, (list, tuple)) else [files]
        
        # Validate file count
        if len(file_list) > 5:
            raise HTTPException(status_code=400, detail="Maximum 5 files allowed per batch")
        
        # Validate all are PDFs
        for file in file_list:
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(
                    status_code=400,
                    detail=f"File '{file.filename}' is not a PDF. Only PDF files are accepted."
                )
        
        # STEP 1: DETERMINE MODE based on file count
        is_single_mode = len(file_list) == 1
        mode = "single" if is_single_mode else "batch"
        
        logger.info(f"{'='*70}")
        logger.info(f"🚀 Starting analysis: {len(file_list)} file(s), mode={mode}")
        if is_single_mode:
            logger.info(f"   ℹ SINGLE-CV MODE: PASS 1 only (no comparative analysis)")
        else:
            logger.info(f"   ℹ BATCH MODE: PASS 1 + PASS 2 (comparative analysis enabled)")
        logger.info(f"   Job requirements: {len(job_requirements.split()) if job_requirements.strip() else 0} words")
        logger.info(f"{'='*70}")
        
        # Process each file independently
        for idx, file in enumerate(file_list, 1):
            document_id = f"doc_{batch_id}_{idx}_{datetime.now().timestamp()}"
            logger.info(f"Processing document {idx}/{len(files)}: {file.filename} (ID: {document_id})")
            
            temp_path = None
            try:
                # Step 1: Save temporary file
                temp_path = f"temp_{datetime.now().timestamp()}_{file.filename}"
                with open(temp_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                temp_files.append(temp_path)
                
                logger.info(f"  [{idx}] Saved to temp: {temp_path}")
                
                # Step 2: PDF Extraction
                logger.info(f"  [{idx}] Extracting PDF text...")
                extraction_result = pdf_processor.process(temp_path)
                raw_text = extraction_result.raw_text
                
                if not raw_text or len(raw_text.strip()) < 50:
                    raise ValueError("Extracted text too short or empty")
                
                logger.info(f"  [{idx}] Extracted {len(raw_text)} characters")
                
                # Step 3: NLP Analysis
                logger.info(f"  [{idx}] Running NLP analysis...")
                nlp_result = nlp_engine.extract(raw_text)
                
                # Step 4: Resume Reconstruction
                logger.info(f"  [{idx}] Reconstructing resume...")
                reconstruction_result = resume_reconstructor.reconstruct(
                    raw_text=raw_text,
                    nlp_data=nlp_result,
                    sections=nlp_result.get("sections", {})
                )
                
                resume_markdown = reconstruction_result.get("markdown", "")
                resume_json = reconstruction_result.get("json", {})
                
                # Step 5: LLM PASS 1 Analysis
                logger.info(f"  [{idx}] Running LLM PASS 1 (single-candidate analysis)...")
                llm_analysis = llm_analyzer.analyze(
                    resume_json=resume_json,
                    resume_markdown=resume_markdown,
                    raw_text=raw_text,
                    job_requirements=job_requirements,
                    is_single_mode=is_single_mode  # Tell analyzer if single or batch
                )
                
                logger.info(f"  [{idx}] Analysis complete - Score: {llm_analysis.get('llm_analysis', {}).get('overall_score', 'N/A')}")
                
                # Build document result
                doc_result = DocumentResult(
                    document_id=document_id,
                    filename=file.filename,
                    status="success",
                    extraction={
                        "raw_text_preview": raw_text[:300] + "..." if len(raw_text) > 300 else raw_text,
                        "char_count": len(raw_text),
                        "confidence": extraction_result.confidence,
                        "document_type": "Scanned" if extraction_result.needs_ocr else "Digital"
                    },
                    analysis={
                        "resume_json": resume_json,
                        "resume_markdown": resume_markdown,
                        "llm_analysis": llm_analysis
                    }
                )
                
                documents_results.append(doc_result)
                logger.info(f"✓ Document {idx} completed successfully")
                
            except Exception as e:
                error_msg = f"Document processing failed: {str(e)}"
                logger.error(f"✗ Document {idx} failed: {error_msg}")
                logger.error(traceback.format_exc())
                
                # Record failure
                doc_result = DocumentResult(
                    document_id=document_id,
                    filename=file.filename,
                    status="failed",
                    error=error_msg
                )
                
                documents_results.append(doc_result)
            
            finally:
                # Cleanup this file's temp
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
        
        processing_time_pass1 = (datetime.now() - start_time).total_seconds()
        
        # Count results
        success_count = sum(1 for d in documents_results if d.status == "success")
        failed_count = len(documents_results) - success_count
        
        logger.info(f"{'='*70}")
        logger.info(f"✅ PASS 1 COMPLETE: {success_count} succeeded, {failed_count} failed")
        logger.info(f"   Time: {processing_time_pass1:.2f}s")
        logger.info(f"{'='*70}")
        
        # STEP 2: Branch by CV count
        # If single CV: Return immediately with PASS 1 only (NO comparative analysis)
        if is_single_mode and success_count == 1:
            logger.info(f"{'='*70}")
            logger.info(f"✅ SINGLE-CV ANALYSIS COMPLETE")
            logger.info(f"   Mode: single (no comparative analysis)")
            logger.info(f"   Result: Full PASS 1 analysis")
            logger.info(f"{'='*70}")
            
            processing_time_total = (datetime.now() - start_time).total_seconds()
            
            single_result = documents_results[0]
            return SingleCVResponse(
                mode="single",
                batch_id=batch_id,
                job_requirements=job_requirements,
                job_requirements_used=bool(job_requirements.strip()),
                candidate={
                    "document_id": single_result.document_id,
                    "filename": single_result.filename,
                    "llm_analysis": single_result.analysis.get("llm_analysis", {}) if single_result.analysis else {},
                    "resume_json": single_result.analysis.get("resume_json", {}) if single_result.analysis else {},
                    "extraction": single_result.extraction
                },
                processing_time=processing_time_total,
                success=True
            )
        
        # PASS 2: Comparative Analysis (only if batch mode AND 2+ successful candidates)
        comparative_analysis = None
        if not is_single_mode and success_count > 1:  # Only comparative if batch AND 2+ candidates
            logger.info("=" * 70)
            logger.info("🚀 STARTING PASS 2: CROSS-CANDIDATE COMPARATIVE ANALYSIS")
            logger.info(f"   Comparing {success_count} candidates...")
            logger.info("=" * 70)
            
            try:
                # Extract successful candidates for comparison
                successful_docs = []
                for doc_result in documents_results:
                    if doc_result.status == "success" and doc_result.analysis:
                        llm_analysis = doc_result.analysis.get("llm_analysis", {})
                        resume_json = doc_result.analysis.get("resume_json", {})
                        
                        candidate_data = {
                            "document_id": doc_result.document_id,
                            "filename": doc_result.filename,
                            "name": llm_analysis.get("candidate_name", "Unknown"),
                            "experience_summary": llm_analysis.get("experience_summary", ""),
                            "skills": llm_analysis.get("skills", {}),
                            "certifications": llm_analysis.get("certifications", []),
                            "preliminary_fit_score": llm_analysis.get("overall_score", 0),
                            "seniority_level": llm_analysis.get("seniority_level", "mid"),
                            "years_experience": llm_analysis.get("key_metrics", {}).get("years_experience", 0),
                            "resume_json": resume_json
                        }
                        successful_docs.append(candidate_data)
                
                # Call LLM for comparative analysis (single call with ALL candidates)
                comparative_result = llm_analyzer.analyze_comparative(
                    candidates=successful_docs,
                    job_requirements=job_requirements
                )
                
                if comparative_result and "comparative_analysis" in comparative_result:
                    comparative_analysis = comparative_result["comparative_analysis"]
                    logger.info("✓ PASS 2 Comparative analysis complete")
                else:
                    logger.warning("⚠ Comparative analysis returned empty result")
                
            except Exception as e:
                logger.error(f"✗ Comparative analysis failed: {str(e)}")
                logger.error(traceback.format_exc())
                # Continue without comparative analysis - not critical
        
        elif not is_single_mode and success_count == 1:
            logger.info("ℹ Only 1 successful candidate from batch - skipping PASS 2 comparative analysis")
        
        processing_time_total = (datetime.now() - start_time).total_seconds()
        
        # Create batch response with both PASS 1 and optional PASS 2 results
        batch_response = BatchAnalyzeResponse(
            mode="batch",
            batch_id=batch_id,
            job_requirements=job_requirements,
            documents=documents_results,
            comparative_analysis=comparative_analysis,
            job_requirements_used=bool(job_requirements.strip()),
            job_requirements_provided=bool(job_requirements.strip()),
            documents_count=len(documents_results),
            success_count=success_count,
            failed_count=failed_count,
            processing_time=processing_time_total,
            success=success_count > 0
        )
        
        logger.info(f"{'='*70}")
        logger.info(f"✅ BATCH ANALYSIS COMPLETE (PASS 1 + PASS 2)")
        logger.info(f"   Mode: batch (comparative analysis {'enabled' if comparative_analysis else 'not available'})")
        logger.info(f"   Documents: {success_count} succeeded, {failed_count} failed")
        logger.info(f"   Comparative analysis: {'Yes' if comparative_analysis else 'No'}")
        logger.info(f"   Total time: {processing_time_total:.2f}s")
        logger.info(f"{'='*70}")
        
        return batch_response
    
    except HTTPException as e:
        logger.error(f"✗ Batch validation failed: {e.detail}")
        raise
    
    except Exception as e:
        logger.error(f"✗ Batch processing failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Cleanup all temp files
        for temp_path in temp_files:
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
            "/process": "Complete end-to-end processing",
            "/batch-analyze": "Batch analyze up to 5 PDFs with shared job requirements"
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