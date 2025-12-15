import json
import re
import requests
import os
import sys
from typing import Dict, Any, Optional

# Configuration for Ollama
OLLAMA_URL = "http://127.0.0.1:11500/api/generate"
DEFAULT_MODEL = "qwen2.5:7b-instruct-q4_K_M"


class LLMStructuredExtractor:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.default_model = model

    def load_template(self, template_name: str) -> str:
        """Loads a prompt template from the templates directory."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(current_dir, "templates", f"{template_name}.txt")
        
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Template file not found: {template_path}")

    def clean_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Sanitizes the LLM response to ensure it's valid JSON.
        """
        # Remove markdown code blocks
        text = re.sub(r'```json\s*', '', response_text)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Fallback: Try to find the first '{' and last '}'
            start = text.find('{')
            end = text.rfind('}')
            
            if start != -1 and end != -1:
                try:
                    json_str = text[start:end+1]
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
            raise ValueError(f"Failed to parse JSON from LLM response: {response_text[:100]}...")

    def extract(self, resume_text: str, nlp_data: Dict[str, Any], model: Optional[str] = None) -> Dict[str, Any]:
        """
        Sends the resume text and NLP-extracted data to the LLM and returns structured JSON data.
        Uses streaming mode for real-time output and unbuffered processing.
        """
        target_model = model or self.default_model
        template = self.load_template("resume_to_json_prompt")
        
        # Convert NLP data to string for the prompt
        nlp_data_str = json.dumps(nlp_data, indent=2)
        
        prompt = template.format(resume_text=resume_text, nlp_data=nlp_data_str)
        
        payload = {
            "model": target_model,
            "prompt": prompt,
            "stream": True,  # Enable streaming
            "format": "json"
        }
        
        try:
            print(f"[LLM] Connecting to {OLLAMA_URL} with model {target_model}...", flush=True)
            
            response = requests.post(OLLAMA_URL, json=payload, stream=True)
            response.raise_for_status()
            
            # Accumulate streamed response
            full_response = ""
            
            print(f"[LLM] Streaming response from Ollama...", flush=True)
            for chunk in response.iter_lines():
                if chunk:
                    try:
                        # Each line is a JSON object with a "response" field
                        line_data = json.loads(chunk)
                        text_chunk = line_data.get("response", "")
                        full_response += text_chunk
                        
                        # Flush unbuffered output
                        print(text_chunk, end="", flush=True)
                        sys.stdout.flush()
                        
                    except json.JSONDecodeError:
                        # Skip malformed lines
                        continue
            
            print()  # Newline after streaming
            print(f"[LLM] Stream complete. Processing response...", flush=True)
            
            # Parse the accumulated response
            return self.clean_json_response(full_response)
            
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Connection error to {OLLAMA_URL}: {e}", flush=True)
            raise ConnectionError(f"Failed to connect to LLM at {OLLAMA_URL}: {str(e)}")
        except Exception as e:
            print(f"[ERROR] General error in extract: {e}", flush=True)
            raise ValueError(f"Error during extraction: {str(e)}")
