#!/usr/bin/env python
"""
Quick test to verify backend is responsive
"""

import time
import requests
import sys

def test_backend():
    """Test if backend is running and responding"""
    print("Testing HR Buddy Backend...")
    print("=" * 50)
    
    max_attempts = 30  # 30 seconds max wait
    attempt = 0
    
    while attempt < max_attempts:
        try:
            print(f"Attempt {attempt + 1}/{max_attempts}: Checking health...", end=" ")
            response = requests.get("http://localhost:8001/health", timeout=2)
            
            if response.status_code == 200:
                data = response.json()
                print("✓ SUCCESS")
                print("=" * 50)
                print("Backend Status:")
                print(f"  Status: {data.get('status')}")
                print(f"  Version: {data.get('version')}")
                print(f"  Service: {data.get('service')}")
                print(f"  Backend Port: {data.get('backend_port')}")
                print(f"  Frontend Port: {data.get('frontend_port')}")
                print("=" * 50)
                print("✓ Backend is running and responding!")
                print("\nYou can now:")
                print("  - Upload PDFs to http://localhost:8001/upload")
                print("  - View API docs at http://localhost:8001/docs")
                print("  - Access frontend at http://localhost:3000")
                return True
            else:
                print(f"HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("⏳ Waiting for startup...")
        except requests.exceptions.Timeout:
            print("⏳ Timeout, retrying...")
        except Exception as e:
            print(f"⏳ {type(e).__name__}")
        
        attempt += 1
        if attempt < max_attempts:
            time.sleep(1)
    
    print("\n" + "=" * 50)
    print("✗ Backend did not respond after 30 seconds")
    print("=" * 50)
    print("\nTroubleshooting:")
    print("1. Check if backend window shows errors")
    print("2. Verify Python version: python --version")
    print("3. Check if port 8001 is available: netstat -ano | findstr :8001")
    print("4. Try running: python backend/main.py")
    return False

if __name__ == "__main__":
    success = test_backend()
    sys.exit(0 if success else 1)
