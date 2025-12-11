import requests
import json

url = "http://127.0.0.1:11434/api/generate"
payload = {
    "model": "qwen2.5:7b-instruct-q4_K_M",
    "prompt": "Say hello!",
    "stream": False,
    "format": "json"
}

try:
    print(f"Sending request to {url}...")
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
