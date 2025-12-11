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

# Import our agents
from agent.extractors.nlp_entity_extractor import EntityExtractor
from agent.extractors.llm_structured_extractor import LLMStructuredExtractor
from agent.ml.evaluator import MLEvaluator
from agent.reporting.hr_report_generator import HRReportGenerator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HR_Buddy_Backend")

app = FastAPI(title="HR Buddy API", version="2.0")

# Configure CORS for Production (Ngrok & Vite)
app.add_middleware(
    CORSMiddleware,
    # Allow all for Ngrok/Netlify flexibility during dev
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Agents
nlp_extractor = EntityExtractor()
llm_extractor = LLMStructuredExtractor()
ml_evaluator = MLEvaluator()
report_generator = HRReportGenerator()

# Models
class NLPRequest(BaseModel):
    text: str

class StructureRequest(BaseModel):
    text: str
    nlp_data: Dict[str, Any]
    model: Optional[str] = "qwen2.5:7b-instruct-q4_K_M"

class EvaluationRequest(BaseModel):
    text: str
    structured_data: Dict[str, Any]

class ReportRequest(BaseModel):
    structured_data: Dict[str, Any]
    ml_result: Dict[str, Any]
    model: Optional[str] = "qwen2.5:7b-instruct-q4_K_M"

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "2.0"}

@app.post("/upload_cv")
async def upload_cv(file: UploadFile = File(...)):
    try:
        # Save temp file
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        import fitz
        
        doc = fitz.open(temp_path)
        text = ""
        
        # Check for OCR need
        import pytesseract
        from PIL import Image
        import io

        for page in doc:
            page_text = page.get_text()
            
            # Fallback to OCR if text is sparse (scanned PDF)
            if not page_text.strip() or len(page_text.strip()) < 50:
                logger.info(f"Page {page.number} seems likely scanned. Attempting OCR...")
                try:
                    pix = page.get_pixmap()
                    img_data = pix.tobytes("png")
                    image = Image.open(io.BytesIO(img_data))
                    ocr_text = pytesseract.image_to_string(image)
                    text += ocr_text + "\n"
                except Exception as ocr_err:
                    logger.warning(f"OCR failed for page {page.number}: {ocr_err}")
                    # Fallback to whatever text might be there
                    text += page_text
            else:
                text += page_text

        doc.close()
        os.remove(temp_path)
        
        return {"filename": file.filename, "extracted_text": text}
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/nlp_extract")
async def nlp_extract_endpoint(req: NLPRequest):
    try:
        entities = nlp_extractor.extract_entities(req.text)
        return {"entities": entities}
    except Exception as e:
        logger.error(f"NLP failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract_structured")
async def extract_structured_endpoint(req: StructureRequest):
    try:
        data = llm_extractor.extract(req.text, req.nlp_data)
        return data
    except Exception as e:
        logger.error(f"LLM extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evaluate")
async def evaluate_endpoint(req: EvaluationRequest):
    try:
        # result includes predicted_ai_score, hire_probability, etc.
        result = ml_evaluator.evaluate(req.text, req.structured_data)
        return result
    except Exception as e:
        logger.error(f"ML evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_report")
async def generate_report_endpoint(req: ReportRequest):
    try:
        html_report = report_generator.generate_report(req.structured_data, req.ml_result)
        return {"html": html_report}
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process_full_pipeline")
async def process_full_pipeline(file: UploadFile = File(...)):
    """
    Combined endpoint for robustness if needed.
    """
    # 1. Upload & Text
    upload_res = await upload_cv(file)
    text = upload_res["extracted_text"]
    
    # 2. NLP
    nlp_res = await nlp_extract_endpoint(NLPRequest(text=text))
    nlp_data = nlp_res["entities"]
    
    # 3. LLM
    struct_req = StructureRequest(text=text, nlp_data=nlp_data)
    structured_data = await extract_structured_endpoint(struct_req)
    
    # 4. ML
    eval_req = EvaluationRequest(text=text, structured_data=structured_data)
    ml_result = await evaluate_endpoint(eval_req)
    
    # 5. Report
    report_req = ReportRequest(structured_data=structured_data, ml_result=ml_result)
    report_res = await generate_report_endpoint(report_req)
    
    return {
        "text": text,
        "nlp": nlp_data,
        "structured": structured_data,
        "ml": ml_result,
        "report": report_res["html"]
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
