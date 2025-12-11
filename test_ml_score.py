import requests
import json

url = "http://localhost:8001/evaluate"

payload = {
    "text": "Experienced software engineer with 5 years of Python and SQL.",
    "structured_data": {
        "experience": [
            {"years": 5, "title": "Software Engineer"}
        ],
        "skills": ["Python", "SQL", "FastAPI"],
        "projects": [{"title": "Project A"}, {"title": "Project B"}]
    }
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
