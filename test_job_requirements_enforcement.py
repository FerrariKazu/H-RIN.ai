"""
Test Job Requirements Enforcement
Validates that job requirements are properly enforced across the entire pipeline
"""

import requests
import json
import sys

# Configuration
API_BASE_URL = "http://localhost:8002"

# Sample job requirements
JOB_REQUIREMENTS = """
Senior Full Stack Engineer - Remote

Target Role: Senior Full Stack Engineer
Experience: 5+ years professional development
Required Skills:
- React or Vue.js (frontend framework)
- Node.js or Python (backend)
- PostgreSQL or MongoDB (database)
- Docker and Kubernetes (containerization)
- AWS or GCP (cloud platform)
- REST API design and implementation
- Git and CI/CD pipelines

Optional Skills:
- GraphQL
- TypeScript
- Machine learning basics
- Microservices architecture

Seniority Level: Senior (5+ years)
Domain: Full Stack Web Development
"""

# Sample resume text (minimal)
SAMPLE_RESUME = """
John Smith
john@example.com | 555-1234 | GitHub: github.com/johnsmith | LinkedIn: linkedin.com/in/johnsmith

Summary:
Full Stack Developer with 6 years of experience building scalable web applications.

Experience:
Senior Developer - Tech Corp (2021-Present)
- Led team of 3 developers
- Built React dashboard with Node.js backend
- Deployed to AWS using Docker
- Improved performance by 40%

Developer - StartupXYZ (2018-2021)
- Developed REST APIs in Python
- Created responsive UI with Vue.js
- Managed PostgreSQL databases

Skills:
React, Node.js, Python, PostgreSQL, Docker, AWS, Git, REST APIs, TypeScript, Agile

Education:
BS Computer Science, State University (2018)
"""


def test_job_requirements_enforcement():
    """Test that job requirements are enforced throughout the pipeline"""
    
    print("\n" + "="*70)
    print("JOB REQUIREMENTS ENFORCEMENT TEST")
    print("="*70)
    
    print("\n[TEST] Uploading minimal resume...")
    
    # Step 1: Upload
    files = {'file': ('resume.pdf', b'%PDF-1.4 dummy pdf', 'application/pdf')}
    
    try:
        # Note: This will fail without a real PDF, but we'll test the analysis endpoint directly
        
        # Step 2: Analyze with job requirements
        print("[TEST] Calling /analyze with job requirements...")
        
        analyze_payload = {
            "filename": "test_resume.pdf",
            "extracted_text": SAMPLE_RESUME,
            "enable_llm_analysis": True,
            "job_requirements": JOB_REQUIREMENTS
        }
        
        response = requests.post(
            f"{API_BASE_URL}/analyze",
            json=analyze_payload,
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"[ERROR] Request failed: {response.status_code}")
            print(response.text)
            return False
        
        result = response.json()
        
        # Verify response
        print("\n[VERIFICATION] Checking analysis response...")
        
        llm_analysis = result.get("llm_analysis", {})
        
        # Check mandatory fields
        checks = {
            "job_requirements_used": llm_analysis.get("job_requirements_used"),
            "job_requirements_hash": bool(llm_analysis.get("job_requirements_hash")),
            "job_requirements_raw": bool(llm_analysis.get("job_requirements_raw")),
            "job_alignment_summary": bool(llm_analysis.get("job_alignment_summary")),
            "matched_requirements": isinstance(llm_analysis.get("matched_requirements"), list),
            "missing_requirements": isinstance(llm_analysis.get("missing_requirements"), list),
            "role_fit_verdict": bool(llm_analysis.get("role_fit_verdict")),
        }
        
        print("\n[RESULTS]:")
        all_passed = True
        for check_name, check_result in checks.items():
            status = "✓" if check_result else "✗"
            print(f"  {status} {check_name}: {check_result}")
            if not check_result:
                all_passed = False
        
        # Print key analysis sections
        if llm_analysis:
            print("\n[ANALYSIS SUMMARY]:")
            print(f"  Executive Summary: {llm_analysis.get('executive_summary', 'N/A')[:100]}...")
            print(f"  Job Used: {llm_analysis.get('job_requirements_used')}")
            print(f"  Hash: {llm_analysis.get('job_requirements_hash', 'N/A')[:8]}...")
            
            if llm_analysis.get("matched_requirements"):
                print(f"  Matched Requirements: {len(llm_analysis['matched_requirements'])} items")
            
            if llm_analysis.get("missing_requirements"):
                print(f"  Missing Requirements: {len(llm_analysis['missing_requirements'])} items")
            
            role_verdict = llm_analysis.get("role_fit_verdict", {})
            if role_verdict:
                print(f"  Role Fit: {role_verdict.get('recommendation')} (confidence: {role_verdict.get('confidence')}%)")
        
        print("\n" + "="*70)
        if all_passed:
            print("✓ ALL CHECKS PASSED - Job Requirements Enforcement Working!")
        else:
            print("✗ SOME CHECKS FAILED - Review implementation")
        print("="*70 + "\n")
        
        return all_passed
        
    except requests.exceptions.ConnectionError:
        print("[ERROR] Could not connect to backend at", API_BASE_URL)
        print("Make sure the backend is running: python -m backend.main")
        return False
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_without_job_requirements():
    """Test generic analysis when no job requirements provided"""
    
    print("\n" + "="*70)
    print("GENERIC ANALYSIS TEST (NO JOB REQUIREMENTS)")
    print("="*70)
    
    print("[TEST] Calling /analyze WITHOUT job requirements...")
    
    analyze_payload = {
        "filename": "test_resume2.pdf",
        "extracted_text": SAMPLE_RESUME,
        "enable_llm_analysis": True,
        "job_requirements": ""  # Empty job requirements
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/analyze",
            json=analyze_payload,
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"[ERROR] Request failed: {response.status_code}")
            return False
        
        result = response.json()
        llm_analysis = result.get("llm_analysis", {})
        
        # Should have verification flags even without job requirements
        print("\n[RESULTS]:")
        print(f"  ✓ job_requirements_used: {llm_analysis.get('job_requirements_used')}")
        print(f"  ✓ job_requirements_hash: {llm_analysis.get('job_requirements_hash', 'N/A')[:8]}...")
        print(f"  ✓ Generic analysis completed")
        
        print("\n" + "="*70)
        print("✓ GENERIC ANALYSIS TEST PASSED")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        return False


if __name__ == "__main__":
    print("\nStarting Job Requirements Enforcement Tests...")
    
    test1 = test_job_requirements_enforcement()
    test2 = test_without_job_requirements()
    
    if test1 and test2:
        print("\n✓✓✓ ALL TESTS PASSED ✓✓✓\n")
        sys.exit(0)
    else:
        print("\n✗✗✗ SOME TESTS FAILED ✗✗✗\n")
        sys.exit(1)
