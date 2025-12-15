import requests
import json

url = "http://127.0.0.1:11434/api/generate"
payload = {
    "model": "qwen2.5:7b-instruct-q4_K_M",
    "prompt": "Say hello!",
    "stream": True,
    "format": "json"
}

try:
    print(f"Sending request to {url}...", flush=True)
    response = requests.post(url, json=payload, stream=True)
    print(f"Status Code: {response.status_code}", flush=True)
    
    # Process streaming response
    full_response = ""
    for chunk in response.iter_lines():
        if chunk:
            try:
                line_data = json.loads(chunk)
                text_chunk = line_data.get("response", "")
                full_response += text_chunk
                print(text_chunk, end="", flush=True)
            except json.JSONDecodeError:
                continue
    
    print("\n", flush=True)
    print(f"Full Response: {full_response}", flush=True)
except Exception as e:
    print(f"Error: {e}", flush=True)
