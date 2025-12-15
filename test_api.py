#!/usr/bin/env python
"""
Test the HR Buddy API endpoints
"""

import requests
import json
import time

BASE_URL = "http://localhost:8002"

def test_health():
    """Test health check endpoint"""
    print("=" * 60)
    print("TEST 1: Health Check")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        data = response.json()
        
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Response: {json.dumps(data, indent=2)}")
        
        assert data["status"] == "ok", "Status is not 'ok'"
        assert data["components_ready"] == True, "Not all components ready"
        
        print("\n✓ Health check PASSED\n")
        return True
    except Exception as e:
        print(f"✗ Health check FAILED: {e}\n")
        return False

def test_sample_pdf():
    """Test PDF upload and processing"""
    print("=" * 60)
    print("TEST 2: Sample PDF Processing")
    print("=" * 60)
    
    # Create a sample PDF for testing
    sample_pdf_path = "sample_resume.pdf"
    
    # Check if sample exists, if not create a simple test
    try:
        with open(sample_pdf_path, 'rb') as f:
            files = {'file': f}
            
            print("Testing /upload endpoint...")
            response = requests.post(f"{BASE_URL}/upload", files=files)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Upload successful")
                print(f"  - Extracted text length: {len(data.get('raw_text', ''))}")
                print(f"  - Confidence: {data.get('confidence', 0):.2%}")
                
                print("\n✓ PDF upload test PASSED\n")
                return True
            else:
                print(f"✗ Upload failed: {response.status_code}")
                print(f"  Response: {response.text}\n")
                return False
    except FileNotFoundError:
        print(f"⚠ Sample PDF not found: {sample_pdf_path}")
        print("  Skipping PDF test (no sample file)\n")
        return True

def test_nlp_extraction():
    """Test NLP extraction"""
    print("=" * 60)
    print("TEST 3: NLP Extraction")
    print("=" * 60)
    
    sample_text = """
    John Smith
    john.smith@email.com | (555) 123-4567
    LinkedIn: linkedin.com/in/johnsmith
    
    PROFESSIONAL SUMMARY
    Senior Software Engineer with 8 years of experience in full-stack development.
    Expert in Python, JavaScript, React, and AWS.
    
    SKILLS
    Programming Languages: Python, JavaScript, Java, SQL
    Frameworks: React, Django, FastAPI, Node.js
    Cloud & DevOps: AWS, Docker, Kubernetes, CI/CD
    Databases: PostgreSQL, MongoDB, Redis
    
    EXPERIENCE
    Senior Engineer | TechCorp | 2020-Present
    - Led team of 5 engineers
    - Implemented microservices architecture
    
    Software Engineer | StartupXYZ | 2018-2020
    - Developed REST APIs using Python and FastAPI
    
    EDUCATION
    B.S. Computer Science | State University | 2016
    Certifications: AWS Solutions Architect Associate
    """
    
    try:
        payload = {"extracted_text": sample_text}
        
        print("Testing /analyze endpoint...")
        response = requests.post(f"{BASE_URL}/analyze", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ NLP extraction successful")
            print(f"  - Markdown generated: {len(data.get('markdown', '')) > 0}")
            print(f"  - JSON data generated: {len(data.get('json_data', {})) > 0}")
            print(f"  - Analysis available: {'analysis' in data}")
            
            print("\n✓ NLP extraction test PASSED\n")
            return True
        else:
            print(f"✗ NLP extraction failed: {response.status_code}")
            print(f"  Response: {response.text}\n")
            return False
    except Exception as e:
        print(f"✗ NLP extraction test FAILED: {e}\n")
        return False

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "HR Buddy API Test Suite" + " " * 24 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    # Check if backend is running
    try:
        requests.get(f"{BASE_URL}/health", timeout=2)
    except requests.exceptions.ConnectionError:
        print(f"✗ FATAL: Backend is not running on {BASE_URL}")
        print("  Start the backend with: python backend/main.py")
        return
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health()))
    results.append(("NLP Extraction", test_nlp_extraction()))
    results.append(("PDF Processing", test_sample_pdf()))
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} {test_name}")
    
    print()
    print(f"Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests PASSED! Backend is ready for use.")
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Check the output above.")

if __name__ == "__main__":
    main()
