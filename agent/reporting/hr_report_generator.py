import json
import os
import sys
import requests
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent.extractors.llm_structured_extractor import OLLAMA_URL, DEFAULT_MODEL

class HRReportGenerator:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.template_env = Environment(loader=FileSystemLoader(os.path.join(self.base_dir, "templates")))

    def _generate_llm_analysis(self, structured_data: Dict, ml_result: Dict, model: str) -> Dict:
        """
        Asks the LLM to generate the qualitative parts of the report based on data.
        """
        
        prompt = f"""
        You are an expert HR Analyst. Analyze the following candidate data and ML model output to generate a professional assessment.
        
        **Candidate Data:**
        {json.dumps(structured_data, indent=2)}
        
        **ML Model Analysis:**
        - Hire Probability: {ml_result.get('hire_probability', 0):.2f}
        - Predicted AI Score: {ml_result.get('predicted_ai_score', 0):.2f}
        - Top Positive Factors: {json.dumps(ml_result.get('top_positive_features', []))}
        - Top Negative Factors: {json.dumps(ml_result.get('top_negative_features', []))}
        
        **Task:**
        Generate a JSON object with the following fields:
        1. "executive_summary": A 2-3 sentence professional summary of the candidate's suitability.
        2. "strengths": A list of 3-5 key strengths (bullet points).
        3. "weaknesses": A list of 2-3 potential concerns or areas for improvement.
        4. "recommended_roles": A list of 2-3 specific job titles they are best suited for.
        
        **Tone:** Professional, objective, and constructive.
        **Format:** JSON ONLY. No markdown.
        """
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        result = response.json()
        return json.loads(result.get("response", "{}"))

    def generate_report(self, structured_data: Dict, ml_result: Dict, model: str = DEFAULT_MODEL) -> str:
        """
        Generates the full HTML report.
        """
        # 1. Get qualitative analysis from LLM
        analysis = self._generate_llm_analysis(structured_data, ml_result, model)
        
        # 2. Prepare context for template
        context = {
            "candidate_name": structured_data.get("name", "Candidate"),
            "contact_info": structured_data.get("contact_info", {}),
            "hire_probability": ml_result.get("hire_probability", 0),
            "predicted_ai_score": ml_result.get("predicted_ai_score", 0),
            "executive_summary": analysis.get("executive_summary", ""),
            "strengths": analysis.get("strengths", []),
            "weaknesses": analysis.get("weaknesses", []),
            "top_positive_features": ml_result.get("top_positive_features", []),
            "top_negative_features": ml_result.get("top_negative_features", []),
            "recommended_roles": analysis.get("recommended_roles", [])
        }
        
        # 3. Render HTML
        template = self.template_env.get_template("report.html")
        return template.render(**context)

# Singleton
report_generator = HRReportGenerator()
