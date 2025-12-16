
import requests
import json
import os
import time

BASE_URL = "http://localhost:8002"

def wait_for_backend():
    print("Waiting for backend to start...")
    for _ in range(30):
        try:
            requests.get(f"{BASE_URL}/health")
            print("Backend is ready!")
            return True
        except:
            time.sleep(1)
    return False

def test_single_cv(pdf_path):
    print("\n[TEST] Single CV Mode")
    with open(pdf_path, "rb") as f:
        files = [("files", (os.path.basename(pdf_path), f, "application/pdf"))]
        response = requests.post(f"{BASE_URL}/batch-analyze", files=files)
    
    if response.status_code != 200:
        print(f"FAILED: Status {response.status_code}")
        print(response.text)
        return False
        
    data = response.json()
    print("Response keys:", data.keys())
    
    # Validation
    try:
        assert data["mode"] == "single", f"Expected mode 'single', got {data.get('mode')}"
        assert len(data["candidates"]) == 1
        assert "experience_summary" in data
        assert "ai_executive_assessment" in data
        assert data["experience_summary"] is not None
        assert data["ai_executive_assessment"] is not None
        
        cand = data["candidates"][0]
        # Check deterministic fields
        assert "name" in cand
        assert "email" in cand
        # Check Qwen skills
        assert "skills" in cand
        assert isinstance(cand["skills"], list)
        
        print("✅ Single CV Test Passed")
        return True
    except AssertionError as e:
        print(f"❌ Single CV Test Failed: {e}")
        return False

def test_batch_cv(pdf_path):
    print("\n[TEST] Batch CV Mode (2 files)")
    # Re-use the same file twice to simulate batch
    files = []
    f1 = open(pdf_path, "rb")
    files.append(("files", ("resume1.pdf", f1, "application/pdf")))
    f2 = open(pdf_path, "rb")
    files.append(("files", ("resume2.pdf", f2, "application/pdf")))
    
    try:
        response = requests.post(f"{BASE_URL}/batch-analyze", files=files)
        
        if response.status_code != 200:
            print(f"FAILED: Status {response.status_code}")
            return False
            
        data = response.json()
        
        # Validation
        try:
            assert data["mode"] == "batch", f"Expected mode 'batch', got {data.get('mode')}"
            assert len(data["candidates"]) == 2
            assert data["experience_summary"] is not None
            assert data["ai_executive_assessment"] is not None
            
            print("✅ Batch CV Test Passed")
            return True
        except AssertionError as e:
            print(f"❌ Batch CV Test Failed: {e}")
            return False
            
    finally:
        f1.close()
        f2.close()

if __name__ == "__main__":
    if not wait_for_backend():
        print("Backend failed to start")
        exit(1)
    
    # Find a PDF file to use
    pdf_files = [f for f in os.listdir(".") if f.lower().endswith(".pdf")]
    if not pdf_files:
        print("No PDF files found in current directory to test with.")
        # Try to find one in temp dir or similar? 
        # Actually I saw one in the file list earlier: "temp_1765824615.104227_Sandy_Antonius_ATS_CV-1.pdf"
        # I will assume there is one or I will fail.
        exit(1)
        
    test_pdf = pdf_files[0]
    print(f"Using test PDF: {test_pdf}")
    
    test_single_cv(test_pdf)
    test_batch_cv(test_pdf)
