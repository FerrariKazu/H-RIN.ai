import requests
import json

OLLAMA_HOST = "http://127.0.0.1:11500"

def check_server():
    print(f"Checking Ollama at {OLLAMA_HOST}...")
    try:
        # Check version/root
        resp = requests.get(f"{OLLAMA_HOST}/")
        if resp.status_code == 200:
            print("[OK] Server is reachable.")
        else:
            print(f"[WARN] Server returned status {resp.status_code}")
            
        # List tags
        print("\nListing models...")
        resp = requests.get(f"{OLLAMA_HOST}/api/tags")
        if resp.status_code == 200:
            models = resp.json().get('models', [])
            print(f"Found {len(models)} models:")
            for m in models:
                print(f" - {m['name']}")
        else:
            print(f"[ERR] Failed to list tags (Status {resp.status_code})")
            print(resp.text)
            
        # Try a simple generation
        print("\nTesting generation with qwen2.5:7b-instruct-q4_K_M...")
        payload = {
            "model": "qwen2.5:7b-instruct-q4_K_M",
            "prompt": "Hi",
            "stream": False
        }
        resp = requests.post(f"{OLLAMA_HOST}/api/generate", json=payload)
        if resp.status_code == 200:
            print("[OK] Generation successful!")
            print(resp.json().get('response', '')[:50])
        else:
            print(f"[ERR] Generation failed (Status {resp.status_code})")
            print(resp.text)

    except Exception as e:
        print(f"[ERR] Connection error: {e}")

if __name__ == "__main__":
    check_server()
