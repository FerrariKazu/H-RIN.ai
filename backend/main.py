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
executive_summary_engine = None
components_initialized = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events
    This replaces the deprecated @app.on_event decorators
    """
    global pdf_processor, nlp_engine, resume_reconstructor, llm_analyzer, executive_summary_engine, components_initialized
    
    # STARTUP
    logger.info("=" * 70)
    logger.info("🚀 HR BUDDY BACKEND - STARTING INITIALIZATION")
    logger.info("=" * 70)
    sys.stdout.flush()
    
    try:
        # Import pipeline components
        logger.info("📦 Step 1/6: Importing pipeline components...")
        sys.stdout.flush()
        
        from backend.pipeline.pdf_processor import PDFProcessor
        from backend.pipeline.nlp_engine_v2 import NLPEngine
        from backend.pipeline.resume_reconstructor import ResumeReconstructor
        from backend.pipeline.llm_analyzer import LLMAnalyzer
        from backend.pipeline.executive_summary import ExecutiveSummaryEngine
        
        logger.info("✓ All pipeline components imported successfully")
        sys.stdout.flush()
        
        # Initialize PDF Processor (fast)
        logger.info("📄 Step 2/6: Initializing PDF Processor...")
        sys.stdout.flush()
        pdf_processor = PDFProcessor()
        logger.info("✓ PDF Processor ready")
        sys.stdout.flush()
        
        # Initialize Resume Reconstructor (fast)
        logger.info("🔧 Step 3/6: Initializing Resume Reconstructor...")
        sys.stdout.flush()
        resume_reconstructor = ResumeReconstructor()
        logger.info("✓ Resume Reconstructor ready")
        sys.stdout.flush()
        
        # Initialize LLM Analyzer (fast if no immediate API calls)
        logger.info("🤖 Step 4/6: Initializing LLM Analyzer...")
        sys.stdout.flush()
        llm_analyzer = LLMAnalyzer(model="qwen2.5:7b-instruct-q4_K_M")
        logger.info("✓ LLM Analyzer ready with Ollama model: qwen2.5:7b-instruct-q4_K_M")
        sys.stdout.flush()
        
        # Initialize Executive Summary Engine (uses llm_analyzer)
        logger.info("📋 Step 5/6: Initializing Executive Summary Engine...")
        sys.stdout.flush()
        executive_summary_engine = ExecutiveSummaryEngine(llm_analyzer=llm_analyzer)
        logger.info("✓ Executive Summary Engine ready")
        sys.stdout.flush()
        
        # Initialize NLP Engine (SLOW - this is likely where it hangs)
        logger.info("🧠 Step 6/6: Initializing NLP Engine (this may take 30-60 seconds)...")
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


class CandidateProfile(BaseModel):
    """Candidate profile with mixed deterministic and analytical data"""
    candidate_id: str
    document_id: str
    filename: Optional[str] = "Unknown"  # Added for frontend compatibility
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    other_links: List[str] = []
    
    # Content Fields
    education: List[Dict] = []
    experience: List[Dict] = []
    skills: List[str] = []
    certifications: List[str] = []
    named_entities: Dict = {}  # Added to support NLP extraction passthrough
    
    analysis_fields_header: str = "" # dummy field to keep comment
    seniority_level: str = "Unknown"
    years_experience: float = 0.0
    preliminary_fit_score: int = 0
    llm_analysis: Dict = {}
    
    # Batch Mode Job Fit Fields (populated when CV count > 1)
    job_fit_score: int = 0
    job_fit_reasoning: str = ""
    
    # Frontend Compatibility
    status: str = "success"
    error: Optional[str] = None


class ExecutiveSummaryResponse(BaseModel):
    """Response with guaranteed three sections: profiles, experience summary, AI assessment"""
    mode: str  # "single" or "batch"
    batch_id: str
    candidates: List[CandidateProfile]
    # Frontend aliases
    candidate: Optional[CandidateProfile] = None
    documents: List[CandidateProfile] = []
    
    experience_summary: str
    ai_executive_assessment: str
    job_requirements: str
    processing_time: float
    success: bool
    
    # Additional analysis fields for frontend batch view
    comparative_analysis: Optional[Dict] = None

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
    Analyze 1-5 PDF resumes with guaranteed sections.
    
    GUARANTEED OUTPUT (all sections always populated):
    - Candidate Profiles: Deterministic personal info (name, email, phone, etc.)
    - Experience Summary: HR-grade summary comparing candidates (Qwen)
    - AI Executive Assessment: Comparative evaluation (Qwen)
    
    Modes:
    - 1 file → single-CV mode (no comparison language)
    - 2-5 files → batch mode (comparative analysis)
    """
    check_components_ready()
    
    start_time = datetime.now()
    batch_id = batch_id or f"batch_{int(start_time.timestamp())}"
    temp_files = []
    
    logger.info("=" * 70)
    logger.info(f"📥 BATCH ANALYZE REQUEST (batch_id={batch_id})")
    logger.info(f"   Files: {len(files)}")
    logger.info(f"   Job requirements: {'Yes' if job_requirements.strip() else 'No'}")
    logger.info("=" * 70)
    
    # Validate file count
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="At least 1 file required")
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 files allowed")
    
    is_single_mode = len(files) == 1
    mode = "single" if is_single_mode else "batch"
    
    try:
        # STEP 1: Extract and analyze each file individually (PASS 1)
        logger.info(f"{'='*70}")
        logger.info(f"🔄 PASS 1: Extracting and analyzing {len(files)} resumes")
        logger.info(f"{'='*70}")
        
        candidates = []
        successful_count = 0
        
        for idx, file in enumerate(files, 1):
            document_id = f"DOC_{idx}"
            logger.info(f"\n[{idx}] Processing: {file.filename}")
            
            temp_path = None
            try:
                # Save temp file
                temp_path = f"temp_{int(start_time.timestamp())}_{file.filename}"
                contents = await file.read()
                with open(temp_path, "wb") as f:
                    f.write(contents)
                temp_files.append(temp_path)
                
                # Step 2: PDF Extraction
                logger.info(f"  [{idx}] Extracting PDF text...")
                extraction_result = pdf_processor.process(temp_path)
                raw_text = extraction_result.raw_text
                
                if not raw_text or len(raw_text) < 50:
                    logger.warning(f"     ⚠ Insufficient text extracted")
                    continue
                
                logger.info(f"     ✓ Extracted {len(raw_text)} chars")
                
                # Parse resume deterministically (NO LLM)
                logger.info(f"     📋 Parsing resume structure...")
                from backend.pipeline.resume_parser import ResumeParser
                parser = ResumeParser()
                parsed_data = parser.parse(raw_text, filename=file.filename)
                
                # Perform LLM analysis for additional insights
                logger.info(f"     🤖 Running LLM analysis...")
                llm_analysis = llm_analyzer.analyze(
                    resume_json=parsed_data,
                    resume_markdown=raw_text, # Use raw text as markdown fallback since reconstruction skipped
                    raw_text=raw_text,
                    job_requirements=job_requirements,
                    is_single_mode=is_single_mode
                )
                
                logger.info(f"     🔍 LLM Analysis Type: {type(llm_analysis)}")
                if isinstance(llm_analysis, str):
                    logger.warning(f"     ⚠ LLM Analysis returned string instead of dict: {llm_analysis[:100]}...")
                    try:
                        import json
                        llm_analysis = json.loads(llm_analysis)
                    except:
                        logger.error("     ❌ Could not parse LLM analysis string as JSON")
                        llm_analysis = {}
                elif not isinstance(llm_analysis, dict):
                    logger.warning(f"     ⚠ LLM Analysis returned unexpected type: {type(llm_analysis)}")
                    llm_analysis = {}
                
                # Build candidate dict with strict division of responsibility
                # 1. Deterministic fields (from ResumeParser)
                # 2. Semantic fields (Skill - from Qwen as requested)
                
                # Extract skills from LLM analysis if available (Preferred per user request)
                final_skills = []
                if llm_analysis and "skills" in llm_analysis:
                    llm_skills = llm_analysis["skills"]
                    # Handle both list of strings or dict with categories
                    if isinstance(llm_skills, list):
                        final_skills = llm_skills
                    elif isinstance(llm_skills, dict):
                        # Flatten dictionary values
                        for cat_skills in llm_skills.values():
                            if isinstance(cat_skills, list):
                                final_skills.extend(cat_skills)
                
                # Fallback to deterministic regex skills if LLM failed
                if not final_skills:
                    final_skills = parsed_data.get("skills", [])
                
                # Safely extract metrics
                years_experience = 0
                seniority = "mid"
                fit_score = 0
                
                if isinstance(llm_analysis, dict):
                    # Extract Seniority
                    seniority = llm_analysis.get("seniority_level", "mid")
                    if not isinstance(seniority, str):
                        seniority = "mid"
                        
                    # Extract Fit Score
                    fit_score = llm_analysis.get("overall_score", 0)
                    if not isinstance(fit_score, (int, float)):
                        fit_score = 0
                        
                    # Extract Years Experience (handling nested dict issues)
                    key_metrics = llm_analysis.get("key_metrics", {})
                    if isinstance(key_metrics, dict):
                        years_experience = key_metrics.get("years_experience", 0)
                    else:
                        logger.warning(f"     ⚠ key_metrics is not a dict: {type(key_metrics)}")
                        years_experience = 0
                        
                candidate = {
                    "candidate_id": parsed_data["candidate_id"],
                    "document_id": document_id,
                    "filename": file.filename,
                    # Deterministic Data (Required)
                    "name": parsed_data.get("name"),
                    "email": parsed_data.get("email"),
                    "phone": parsed_data.get("phone"),
                    "linkedin": parsed_data.get("linkedin"),
                    "github": parsed_data.get("github"),
                    "other_links": parsed_data.get("other_links", []),
                    "education": parsed_data.get("education", []),
                    "experience": parsed_data.get("experience", []),
                    # Qwen Data (Preferred for Skills)
                    "skills": final_skills,
                    "certifications": parsed_data.get("certifications", []),
                    # Analytical Data
                    "seniority_level": seniority,
                    "years_experience": years_experience,
                    "preliminary_fit_score": fit_score,
                    "llm_analysis": llm_analysis,  # Pass full analysis for frontend
                }
                
                candidates.append(candidate)
                successful_count += 1
                logger.info(f"     ✅ Analysis complete - {candidate['name']}")
                
            except Exception as e:
                logger.error(f"     ❌ Failed to build candidate: {str(e)}")
                logger.error(traceback.format_exc())
            
            finally:
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
        
        if successful_count == 0:
            raise HTTPException(status_code=400, detail="Could not extract valid data from any file")
        
        logger.info(f"\n✅ PASS 1 Complete: {successful_count}/{len(files)} successful")
        
        # STEP 2: Generate Executive Summary sections
        logger.info(f"\n{'='*70}")
        logger.info(f"📊 PASS 2: Generating executive summary sections")
        logger.info(f"{'='*70}")
        
        summary_result = executive_summary_engine.process_candidates(
            candidates=candidates,
            job_requirements=job_requirements,
            mode=mode
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Build response
        candidate_profiles = [CandidateProfile(**p) for p in summary_result["candidates"]]
        
        # Prepare comparative analysis payload for frontend
        comparative_analysis = {
            "executive_summary": summary_result["ai_executive_assessment"], # Map to summary
            "comparative_ranking": [], # Needs to be extracted/generated if possible
            "skill_coverage_matrix": {},
            "strengths_comparison": "",
            "weaknesses_comparison": ""
        }
        
        # Build response
        response = ExecutiveSummaryResponse(
            mode=mode,
            batch_id=batch_id,
            candidates=candidate_profiles,
            candidate=candidate_profiles[0] if mode == "single" and candidate_profiles else None,
            documents=candidate_profiles,
            experience_summary=summary_result["experience_summary"],
            ai_executive_assessment=summary_result["ai_executive_assessment"],
            job_requirements=job_requirements,
            processing_time=processing_time,
            success=True,
            comparative_analysis=comparative_analysis
        )
        
        logger.info(f"\n{'='*70}")
        logger.info(f"✅ BATCH ANALYSIS COMPLETE")
        logger.info(f"   Mode: {mode}")
        logger.info(f"   Candidates: {len(response.candidates)}")
        logger.info(f"   Sections: Profiles, Experience Summary, AI Assessment")
        logger.info(f"   Time: {processing_time:.2f}s")
        logger.info(f"{'='*70}\n")
        
        return response
    
    except HTTPException as e:
        logger.error(f"✗ Validation failed: {e.detail}")
        raise
    
    except Exception as e:
        logger.error(f"✗ Batch processing failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Cleanup temp files
        for temp_path in temp_files:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            
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