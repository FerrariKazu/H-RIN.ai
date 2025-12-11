import os
import openai

# Load API key from environment
api_key = os.getenv("sk-gRIJbpBtApLNZqn6n7TgNX7aIptDZlMwqDAN6m3eOma56OTY")
if not api_key:
    raise ValueError("API key not found in environment variables!")

openai.api_key = api_key

# Quick test: ask the API to list available models
try:
    models = openai.Model.list()
    print("API Key is working! Available models:")
    for m in models.data[:5]:  # show only first 5 for brevity
        print("-", m.id)
except Exception as e:
    print("Something went wrong:", e)
