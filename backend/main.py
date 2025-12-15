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

# Allow importing from root directory (agent, etc.)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HR_Buddy_Backend")

# Import Pipeline Engines (with fallback)
PDFParser = OCREngine = NLPEngine = LayoutEngine = None
try:
    from backend.pipeline.pdf_parser import PDFParser
    from backend.pipeline.ocr_engine import OCREngine
    from backend.pipeline.nlp_engine import NLPEngine
    from backend.pipeline.layout_engine import LayoutEngine
except ImportError as e:
    logger.warning(f"Pipeline imports failed: {e}. Server will run without full pipeline support.")

# Import existing agents (keeping for ML/LLM logic)
LLMStructuredExtractor = MLEvaluator = HRReportGenerator = None
try:
    from agent.extractors.llm_structured_extractor import LLMStructuredExtractor
    from agent.ml.evaluator import MLEvaluator
    from agent.reporting.hr_report_generator import HRReportGenerator
except ImportError as e:
    logger.warning(f"Agent imports failed: {e}. Server will run with limited functionality.")

app = FastAPI(title="HR Buddy API", version="3.0 - Production")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Pipeline (skip if imports failed)
pdf_parser = None
ocr_engine = None
nlp_engine = None
layout_engine = None
llm_extractor = None
ml_evaluator = None
report_generator = None

if PDFParser:
    try:
        pdf_parser = PDFParser()
        ocr_engine = OCREngine()
        nlp_engine = NLPEngine()
        layout_engine = LayoutEngine()
    except Exception as e:
        logger.warning(f"Pipeline initialization failed: {e}")

if LLMStructuredExtractor:
    try:
        llm_extractor = LLMStructuredExtractor()
        ml_evaluator = MLEvaluator()
        report_generator = HRReportGenerator()
    except Exception as e:
        logger.warning(f"Agent initialization failed: {e}")

# Models
class NLPRequest(BaseModel):
    text: str

class StructureRequest(BaseModel):
    text: str
    nlp_data: Dict
    model: Optional[str] = "qwen3:14b-q4_K_M"

class EvaluationRequest(BaseModel):
    text: str
    structured_data: Dict

class ReportRequest(BaseModel):
    structured_data: Dict
    ml_result: Dict
    model: Optional[str] = "qwen3:14b-q4_K_M"

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "3.0", "pipeline": "active"}

@app.post("/upload_cv")
async def upload_cv(file: UploadFile = File(...)):
    if not pdf_parser:
        raise HTTPException(status_code=503, detail="PDF parser not initialized")
    try:
        # Save temp file
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 1. Pipeline: PDF Parse
        extract_result = pdf_parser.process(temp_path)
        
        final_text = extract_result["text"]
        layout_info = []
        
        # 2. Pipeline: OCR / Layout / Hybrid
        if extract_result.get("needs_ocr", False):
            logger.info("Triggering OCR Pipeline")
            ocr_text = ""
            for img_bytes in extract_result.get("images", []):
                # Preprocess & OCR
                ocr_res = ocr_engine.process_image(img_bytes)
                ocr_text += ocr_res["text"] + "\n"
                
                # Layout Analysis (on the first page or all)
                # Just analyzing first page for layout signature to save time
                if not layout_info:
                    layout_info = layout_engine.analyze(img_bytes)
            
            final_text = ocr_text if len(ocr_text) > len(final_text) else final_text
        
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return {
            "filename": file.filename,
            "extracted_text": final_text,
            "document_type": "Scanned/Hybrid" if extract_result.get("needs_ocr") else "Digital Native",
            "meta": extract_result.get("meta", {}),
            "layout_summary": str(layout_info)[:200] # Truncate for sanity
        }
    except Exception as e:
        logger.error(f"Upload pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/nlp_extract")
async def nlp_extract_endpoint(req: NLPRequest):
    if not nlp_engine:
        raise HTTPException(status_code=503, detail="NLP engine not initialized")
    try:
        # Use new generic NLP Engine
        data = nlp_engine.extract(req.text)
        return data # returns {"entities": ...}
    except Exception as e:
        logger.error(f"NLP failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract_structured")
async def extract_structured_endpoint(req: StructureRequest):
    if not llm_extractor:
        raise HTTPException(status_code=503, detail="LLM extractor not initialized")
    try:
        data = llm_extractor.extract(req.text, req.nlp_data)
        return data
    except Exception as e:
        logger.error(f"LLM extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evaluate")
async def evaluate_endpoint(req: EvaluationRequest):
    if not ml_evaluator:
        raise HTTPException(status_code=503, detail="ML evaluator not initialized")
    try:
        result = ml_evaluator.evaluate(req.text, req.structured_data)
        return result
    except Exception as e:
        logger.error(f"ML evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_report")
async def generate_report_endpoint(req: ReportRequest):
    if not report_generator:
        raise HTTPException(status_code=503, detail="Report generator not initialized")
    try:
        html_report = report_generator.generate_report(req.structured_data, req.ml_result)
        return {"html": html_report}
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
