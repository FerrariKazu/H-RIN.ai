#!/usr/bin/env python3
"""
Test script for batch resume analysis
Tests the /batch-analyze endpoint with multiple PDFs
"""

import requests
import json
import sys
import os
from pathlib import Path

# Configuration
BACKEND_URL = "http://localhost:8002"
BATCH_ENDPOINT = f"{BACKEND_URL}/batch-analyze"

# Job requirements for testing
TEST_JOB_REQUIREMENTS = """
Target Role: Senior Software Engineer

Required Skills:
- Python (expert level)
- JavaScript/Node.js (advanced)
- REST API design
- SQL/NoSQL databases
- System design
- Docker/Kubernetes

Optional Skills:
- Machine Learning
- Cloud platforms (AWS/Azure)
- DevOps
- Microservices architecture

Experience: Minimum 5 years in software development
Seniority: Senior level
Domain: Full-stack web development
"""

def test_batch_analysis():
    """Test batch analysis with sample resumes"""
    
    print("=" * 70)
    print("🧪 BATCH ANALYSIS TEST")
    print("=" * 70)
    
    # Find sample PDF files
    workspace_root = Path(__file__).parent
    pdf_files = list(workspace_root.glob("*.pdf"))
    
    if len(pdf_files) == 0:
        print("❌ No PDF files found in workspace")
        print("   Please add some resume PDFs to test batch analysis")
        print("   Example: resume1.pdf, resume2.pdf, etc.")
        return False
    
    # Use first 5 PDFs (max allowed)
    test_files = pdf_files[:5]
    print(f"📄 Found {len(test_files)} PDF file(s) for testing")
    
    for idx, pdf_path in enumerate(test_files, 1):
        print(f"   [{idx}] {pdf_path.name}")
    
    print("\n" + "=" * 70)
    print("🚀 INITIATING BATCH UPLOAD")
    print("=" * 70)
    
    try:
        # Prepare form data
        files = []
        for pdf_path in test_files:
            with open(pdf_path, 'rb') as f:
                files.append(('files', (pdf_path.name, f.read(), 'application/pdf')))
        
        # Prepare request
        data = {
            'job_requirements': TEST_JOB_REQUIREMENTS,
            'batch_id': f'test_batch_{int(__import__("time").time())}'
        }
        
        print(f"📊 Batch ID: {data['batch_id']}")
        print(f"📝 Job Requirements: {len(TEST_JOB_REQUIREMENTS)} chars")
        print(f"📤 Uploading {len(files)} file(s)...")
        
        # Make request
        response = requests.post(BATCH_ENDPOINT, files=files, data=data)
        
        print(f"\n🔗 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n" + "=" * 70)
            print("✅ BATCH ANALYSIS COMPLETED SUCCESSFULLY")
            print("=" * 70)
            
            # Print summary
            print(f"📊 Summary:")
            print(f"   Total Documents: {result.get('documents_count')}")
            print(f"   Successful: {result.get('success_count')}")
            print(f"   Failed: {result.get('failed_count')}")
            print(f"   Processing Time: {result.get('processing_time'):.2f}s")
            print(f"   Job Requirements Used: {result.get('job_requirements_used')}")
            
            # Print detailed results
            print(f"\n📄 Document Results:")
            for idx, doc in enumerate(result.get('documents', []), 1):
                status_icon = "✓" if doc['status'] == 'success' else "✗"
                print(f"\n   [{idx}] {status_icon} {doc['filename']}")
                print(f"       ID: {doc['document_id']}")
                print(f"       Status: {doc['status']}")
                
                if doc['status'] == 'success':
                    analysis = doc.get('analysis', {})
                    llm = analysis.get('llm_analysis', {})
                    
                    score = llm.get('overall_score', 'N/A')
                    matched = llm.get('matched_skills', [])
                    missing = llm.get('missing_skills', [])
                    
                    print(f"       Score: {score}/100")
                    print(f"       Matched Skills: {len(matched)} ({', '.join(matched[:3])}{'...' if len(matched) > 3 else ''})")
                    print(f"       Missing Skills: {len(missing)} ({', '.join(missing[:3])}{'...' if len(missing) > 3 else ''})")
                else:
                    print(f"       Error: {doc.get('error', 'Unknown error')}")
            
            print("\n" + "=" * 70)
            print("🎉 Batch analysis test completed successfully!")
            print("=" * 70)
            
            # Save results to file
            output_file = workspace_root / "batch_test_results.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"💾 Results saved to: {output_file}")
            
            return True
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Cannot reach backend at " + BACKEND_URL)
        print("   Make sure the backend is running: python backend/main.py")
        return False
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_batch_validation():
    """Test batch validation (file count, file type)"""
    
    print("\n" + "=" * 70)
    print("🧪 BATCH VALIDATION TESTS")
    print("=" * 70)
    
    # Test 1: No files
    print("\n[Test 1] Empty batch (no files)")
    try:
        response = requests.post(BATCH_ENDPOINT, data={'batch_id': 'test_empty'})
        if response.status_code != 200:
            print(f"  ✓ Correctly rejected empty batch: {response.status_code}")
        else:
            print(f"  ✗ Should have rejected empty batch")
    except Exception as e:
        print(f"  ⚠ Error: {str(e)}")
    
    # Test 2: Too many files (6+)
    print("\n[Test 2] Batch with > 5 files")
    workspace_root = Path(__file__).parent
    pdf_files = list(workspace_root.glob("*.pdf"))
    
    if len(pdf_files) >= 6:
        try:
            files = []
            for pdf_path in pdf_files[:6]:
                with open(pdf_path, 'rb') as f:
                    files.append(('files', (pdf_path.name, f.read(), 'application/pdf')))
            
            response = requests.post(
                BATCH_ENDPOINT,
                files=files,
                data={'batch_id': 'test_too_many'}
            )
            if response.status_code != 200:
                print(f"  ✓ Correctly rejected 6 files: {response.status_code}")
            else:
                print(f"  ✗ Should have rejected > 5 files")
        except Exception as e:
            print(f"  ⚠ Error: {str(e)}")
    else:
        print("  ⊘ Skipped (need 6+ PDFs to test)")

if __name__ == "__main__":
    success = test_batch_analysis()
    
    # Optional: Run validation tests
    # test_batch_validation()
    
    sys.exit(0 if success else 1)
