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
        print("\nTesting generation with qwen2.5:7b-instruct-q4_K_M...", flush=True)
        payload = {
            "model": "qwen2.5:7b-instruct-q4_K_M",
            "prompt": "Hi",
            "stream": True
        }
        resp = requests.post(f"{OLLAMA_HOST}/api/generate", json=payload, stream=True)
        if resp.status_code == 200:
            print("[OK] Generation successful!", flush=True)
            # Process streaming response
            full_response = ""
            for chunk in resp.iter_lines():
                if chunk:
                    try:
                        line_data = json.loads(chunk)
                        text_chunk = line_data.get("response", "")
                        full_response += text_chunk
                        print(text_chunk, end="", flush=True)
                    except json.JSONDecodeError:
                        continue
            print("\n", flush=True)
            print(f"Response preview: {full_response[:50]}", flush=True)
        else:
            print(f"[ERR] Generation failed (Status {resp.status_code})", flush=True)
            print(resp.text, flush=True)

    except Exception as e:
        print(f"[ERR] Connection error: {e}", flush=True)

if __name__ == "__main__":
    check_server()
