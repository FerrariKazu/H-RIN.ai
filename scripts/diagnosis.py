"""
Diagnostic script to identify where initialization hangs
Run this BEFORE running main.py to identify the problem
"""

import sys
import os
import time
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("Diagnostic")

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_import(module_name, description):
    """Test importing a module"""
    logger.info(f"Testing: {description}")
    start = time.time()
    try:
        if module_name == "PDFProcessor":
            from backend.pipeline.pdf_processor import PDFProcessor
            obj = PDFProcessor()
        elif module_name == "NLPEngine":
            from backend.pipeline.nlp_engine_v2 import NLPEngine
            obj = NLPEngine()
        elif module_name == "ResumeReconstructor":
            from backend.pipeline.resume_reconstructor import ResumeReconstructor
            obj = ResumeReconstructor()
        elif module_name == "LLMAnalyzer":
            from backend.pipeline.llm_analyzer import LLMAnalyzer
            obj = LLMAnalyzer()
        
        elapsed = time.time() - start
        logger.info(f"✓ {description} - OK ({elapsed:.2f}s)")
        return True, elapsed
    except Exception as e:
        elapsed = time.time() - start
        logger.error(f"✗ {description} - FAILED ({elapsed:.2f}s)")
        logger.error(f"   Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False, elapsed

def main():
    logger.info("=" * 70)
    logger.info("🔍 HR BUDDY BACKEND - DIAGNOSTIC TEST")
    logger.info("=" * 70)
    
    results = []
    
    # Test basic imports
    logger.info("\n1️⃣  Testing basic Python imports...")
    basic_modules = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("pydantic", "Pydantic"),
    ]
    
    for module, name in basic_modules:
        start = time.time()
        try:
            __import__(module)
            elapsed = time.time() - start
            logger.info(f"✓ {name} - OK ({elapsed:.2f}s)")
        except ImportError as e:
            logger.error(f"✗ {name} - MISSING: {e}")
    
    # Test PDF processing dependencies
    logger.info("\n2️⃣  Testing PDF processing dependencies...")
    pdf_modules = [
        ("fitz", "PyMuPDF"),
        ("pdfminer", "PDFMiner"),
        ("pypdf", "PyPDF"),
    ]
    
    for module, name in pdf_modules:
        start = time.time()
        try:
            __import__(module)
            elapsed = time.time() - start
            logger.info(f"✓ {name} - OK ({elapsed:.2f}s)")
        except ImportError as e:
            logger.warning(f"⚠ {name} - MISSING (optional): {e}")
    
    # Test NLP dependencies
    logger.info("\n3️⃣  Testing NLP dependencies...")
    nlp_modules = [
        ("spacy", "spaCy"),
        ("transformers", "Transformers"),
        ("torch", "PyTorch"),
    ]
    
    for module, name in nlp_modules:
        start = time.time()
        try:
            __import__(module)
            elapsed = time.time() - start
            logger.info(f"✓ {name} - OK ({elapsed:.2f}s)")
            
            # Special check for spaCy models
            if module == "spacy":
                try:
                    import spacy
                    logger.info("   Checking spaCy models...")
                    models = ["en_core_web_sm", "en_core_web_md", "en_core_web_lg"]
                    for model in models:
                        try:
                            nlp = spacy.load(model)
                            logger.info(f"   ✓ Model '{model}' available")
                        except OSError:
                            logger.warning(f"   ⚠ Model '{model}' not found")
                except Exception as e:
                    logger.warning(f"   ⚠ Could not check models: {e}")
                    
        except ImportError as e:
            logger.error(f"✗ {name} - MISSING: {e}")
    
    # Test pipeline components
    logger.info("\n4️⃣  Testing pipeline component initialization...")
    logger.info("    (This is where hangs typically occur)")
    
    components = [
        ("PDFProcessor", "PDF Processor"),
        ("ResumeReconstructor", "Resume Reconstructor"),
        ("LLMAnalyzer", "LLM Analyzer"),
        ("NLPEngine", "NLP Engine (SLOW - may take 30-60s)"),
    ]
    
    for component, description in components:
        success, elapsed = test_import(component, description)
        results.append((description, success, elapsed))
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("📊 DIAGNOSTIC SUMMARY")
    logger.info("=" * 70)
    
    total_time = sum(r[2] for r in results)
    failed = [r for r in results if not r[1]]
    
    logger.info(f"Total initialization time: {total_time:.2f}s")
    logger.info(f"Components tested: {len(results)}")
    logger.info(f"Failed: {len(failed)}")
    
    if failed:
        logger.error("\n❌ Failed components:")
        for name, _, elapsed in failed:
            logger.error(f"   - {name} ({elapsed:.2f}s)")
    else:
        logger.info("\n✅ All components initialized successfully!")
    
    logger.info("\n💡 Recommendations:")
    if any("NLP Engine" in r[0] and r[2] > 30 for r in results):
        logger.info("   - NLP Engine is slow. Consider:")
        logger.info("     • Using a smaller spaCy model (en_core_web_sm)")
        logger.info("     • Lazy loading models on first use")
        logger.info("     • Pre-downloading models before deployment")
    
    if failed:
        logger.info("   - Install missing dependencies:")
        logger.info("     • pip install spacy transformers torch")
        logger.info("     • python -m spacy download en_core_web_sm")
    
    logger.info("=" * 70)

if __name__ == "__main__":
    main()