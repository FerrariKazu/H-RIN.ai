#!/usr/bin/env python3
"""
Test script to verify batch upload and comparative analysis
Tests both PASS 1 (individual analysis) and PASS 2 (comparative analysis)
"""

import os
import sys
import json
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

def test_batch_upload():
    """Test batch upload with multiple PDFs"""
    
    from pipeline.llm_analyzer import LLMAnalyzer
    from pipeline.pdf_processor import PDFProcessor
    
    print("\n" + "="*80)
    print("BATCH UPLOAD TEST - COMPARATIVE ANALYSIS")
    print("="*80)
    
    # Find test PDFs
    test_dir = Path(__file__).parent
    pdf_files = list(test_dir.glob("temp_*.pdf"))[:2]  # Take first 2 PDFs
    
    if len(pdf_files) < 2:
        print(f"❌ ERROR: Need at least 2 PDFs for batch test. Found: {len(pdf_files)}")
        return False
    
    print(f"\n📄 Found {len(pdf_files)} test PDFs:")
    for pdf in pdf_files:
        print(f"   - {pdf.name}")
    
    # Initialize components
    print("\n🔧 Initializing components...")
    processor = PDFProcessor()
    analyzer = LLMAnalyzer()
    
    # PASS 1: Extract and analyze each PDF individually
    print("\n" + "-"*80)
    print("PASS 1: Individual CV Analysis")
    print("-"*80)
    
    candidates = []
    
    for idx, pdf_path in enumerate(pdf_files, 1):
        try:
            print(f"\n📋 Processing PDF {idx}/{len(pdf_files)}: {pdf_path.name}")
            
            # Extract text from PDF
            text = processor.extract_text(str(pdf_path))
            if not text:
                print(f"   ⚠️  No text extracted from {pdf_path.name}")
                continue
            
            print(f"   ✓ Extracted {len(text)} characters")
            
            # Analyze with PASS 1
            print(f"   🤖 Running PASS 1 analysis...")
            result = analyzer.analyze(text, filename=pdf_path.name)
            
            if result and "success" in result and result["success"]:
                candidate = result.get("result", {})
                candidate["document_id"] = f"DOC_{idx}"
                candidate["filename"] = pdf_path.name
                candidates.append(candidate)
                
                print(f"   ✓ PASS 1 complete")
                print(f"     - Name: {candidate.get('name', 'Unknown')}")
                print(f"     - Score: {candidate.get('preliminary_fit_score', 0)}/100")
                print(f"     - Seniority: {candidate.get('seniority_level', 'N/A')}")
            else:
                print(f"   ❌ PASS 1 failed: {result}")
        
        except Exception as e:
            print(f"   ❌ Error processing {pdf_path.name}: {e}")
            import traceback
            traceback.print_exc()
    
    if len(candidates) < 2:
        print(f"\n❌ ERROR: Need at least 2 successful PASS 1 analyses. Got: {len(candidates)}")
        return False
    
    print(f"\n✅ PASS 1 complete: {len(candidates)} candidates analyzed")
    
    # PASS 2: Comparative analysis
    print("\n" + "-"*80)
    print("PASS 2: Comparative Analysis")
    print("-"*80)
    
    print(f"\n🤖 Running PASS 2 comparative analysis on {len(candidates)} candidates...")
    print("   (This may take a minute...)")
    
    job_requirements = """
    Senior Software Engineer role requiring:
    - Python and system design expertise
    - Cloud architecture experience
    - Team leadership and mentoring
    - Problem-solving and communication skills
    """
    
    try:
        start_time = time.time()
        comparative_result = analyzer.analyze_comparative(candidates, job_requirements)
        elapsed = time.time() - start_time
        
        print(f"\n   ✓ PASS 2 complete in {elapsed:.1f} seconds")
        
        if comparative_result:
            comparative_data = comparative_result.get("comparative_analysis", {})
            print(f"\n✅ Comparative analysis received with {len(comparative_data)} fields:")
            
            # Display what we got
            for field, value in comparative_data.items():
                if isinstance(value, str):
                    preview = value[:80].replace('\n', ' ') + "..." if len(value) > 80 else value
                    print(f"   ✓ {field}: {preview}")
                elif isinstance(value, (list, dict)):
                    print(f"   ✓ {field}: {type(value).__name__} with {len(value)} items")
                else:
                    print(f"   ✓ {field}: {type(value).__name__}")
            
            # Check if sections would be empty
            print(f"\n📊 Frontend Section Status:")
            empty_sections = []
            required_fields = [
                "executive_summary",
                "comparative_ranking",
                "strengths_comparison",
                "weaknesses_comparison"
            ]
            
            for field in required_fields:
                value = comparative_data.get(field, "")
                if not value or (isinstance(value, list) and len(value) == 0):
                    empty_sections.append(field)
                    print(f"   ❌ {field}: EMPTY")
                else:
                    print(f"   ✅ {field}: Has data")
            
            if empty_sections:
                print(f"\n⚠️  WARNING: These sections would still be empty in frontend:")
                for section in empty_sections:
                    print(f"   - {section}")
                return False
            else:
                print(f"\n✅ All critical sections have data!")
                print("\n" + "="*80)
                print("RESULT: BATCH UPLOAD TEST PASSED ✅")
                print("="*80)
                return True
        else:
            print(f"\n❌ ERROR: No comparative_analysis in result")
            print(f"Result keys: {list(comparative_result.keys()) if comparative_result else 'None'}")
            return False
    
    except Exception as e:
        print(f"\n❌ ERROR during PASS 2: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_batch_upload()
    sys.exit(0 if success else 1)
