"""
LLM Second-Pass Analysis for Resume Evaluation
Provides intelligent insights and scoring
"""

import json
import logging
from typing import Dict, List, Optional, Any
import os

logger = logging.getLogger(__name__)


class LLMAnalyzer:
    """
    LLM-based analysis of resumes
    Can use OpenAI, Ollama, or other LLM providers
    """
    
    def __init__(self, model: str = "gpt-3.5-turbo", api_key: Optional[str] = None):
        """
        Initialize LLM Analyzer
        
        Args:
            model: Model name (gpt-3.5-turbo, gpt-4, ollama models, etc.)
            api_key: API key for external services (optional)
        """
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.logs = []
        
        # Determine provider
        if "gpt" in model.lower():
            self.provider = "openai"
            self._init_openai()
        elif "ollama" in model.lower() or ":" in model:
            # Check for ollama keyword OR colon pattern (e.g., qwen2.5:7b-instruct-q4_K_M)
            self.provider = "ollama"
            self._init_ollama()
        else:
            self.provider = "custom"
            self._log("Using custom/local LLM provider")
    
    def _init_openai(self):
        """Initialize OpenAI client"""
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key) if self.api_key else OpenAI()
            self._log(f"OpenAI client initialized with model {self.model}")
        except ImportError:
            self._log("OpenAI package not installed. Install with: pip install openai", "WARNING")
            self.client = None
        except Exception as e:
            self._log(f"OpenAI initialization failed: {e}", "WARNING")
            self.client = None
    
    def _init_ollama(self):
        """Initialize Ollama client"""
        try:
            import ollama
            self.client = ollama
            self._log(f"Ollama client initialized with model {self.model}")
        except ImportError:
            self._log("Ollama package not installed. Install with: pip install ollama", "WARNING")
            self.client = None
    
    def analyze(self, 
               resume_json: Dict,
               resume_markdown: str,
               raw_text: str = "",
               job_requirements: str = None) -> Dict[str, Any]:
        """
        Perform comprehensive LLM analysis
        
        Args:
            resume_json: Structured resume data
            resume_markdown: Markdown version of resume
            raw_text: Original raw text
            job_requirements: Optional job description to assess fit
        
        Returns:
            Analysis results with scoring and recommendations
        """
        self.logs = []
        self.job_requirements = job_requirements
        
        # If no LLM available, provide heuristic analysis
        if not self.client:
            self._log("No LLM client available, using heuristic analysis")
            return self._heuristic_analysis(resume_json, job_requirements)
        
        try:
            # Prepare prompt
            prompt = self._build_analysis_prompt(resume_markdown, job_requirements)
            
            # Get analysis from LLM
            analysis_text = self._call_llm(prompt)
            
            # Parse response
            analysis = self._parse_analysis(analysis_text, resume_json, job_requirements)
            
            self._log("LLM analysis complete")
            return analysis
            
        except Exception as e:
            self._log(f"LLM analysis failed: {e}, falling back to heuristics", "ERROR")
            return self._heuristic_analysis(resume_json)
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM with prompt using streaming for real-time output"""
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert resume analyst and HR consultant."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
                return response.choices[0].message.content
            
            elif self.provider == "ollama":
                # Use streaming mode for unbuffered real-time output
                response = self.client.generate(
                    model=self.model,
                    prompt=prompt,
                    stream=True  # Enable streaming
                )
                
                # Accumulate streamed response
                full_response = ""
                for chunk in response:
                    if isinstance(chunk, dict):
                        text_chunk = chunk.get('response', '')
                        full_response += text_chunk
                    else:
                        full_response += str(chunk)
                
                return full_response
            
            else:
                # Custom provider
                self._log("Custom LLM provider not implemented, using heuristics")
                return ""
        
        except Exception as e:
            self._log(f"LLM call failed: {e}", "ERROR")
            raise
    
    def _build_analysis_prompt(self, resume_markdown: str, job_requirements: str = None) -> str:
        """Build analysis prompt for LLM"""
        
        job_section = ""
        if job_requirements:
            job_section = f"""
TARGET JOB REQUIREMENTS:
{job_requirements}

TASK: Evaluate the candidate's fit for THIS SPECIFIC JOB. Highlight gaps and alignment.
"""
        
        prompt = f"""
Analyze the following resume{' relative to the job requirements' if job_requirements else ''}:

{resume_markdown}
{job_section}

Please provide your analysis in the following JSON structure:
{{
    "executive_summary": "1-2 sentence overall assessment",
    "strengths": ["strength 1", "strength 2", ...],
    "weaknesses": ["weakness 1", "weakness 2", ...],
    "opportunities": ["opportunity 1", ...],
    {"gap_analysis": {"required_skills": ["...", ], "missing_skills": ["...", ]}, " if job_requirements else ""}
    "technical_fit": {{"score": 0-100, "explanation": "..."}},
    "cultural_fit": {{"score": 0-100, "explanation": "..."}},
    "seniority_level": "junior|mid|senior|lead|executive",
    "recommended_roles": ["role 1", "role 2", ...],
    "missing_skills": ["skill 1", "skill 2", ...],
    "key_achievements": ["achievement 1", ...],
    {"hire_recommendation": "YES|MAYBE|NO (relative to job)" if job_requirements else ""}
    "overall_score": 0-100,
    "key_metrics": {{"experience_years": X, "skills_count": Y, ...}}
}}

Be specific, data-driven, and constructive. {
    'Focus on job-specific fit and explicitly explain why this candidate is suitable or not for the role.' if job_requirements else ''
}
"""
        return prompt
    
    def _parse_analysis(self, response_text: str, resume_json: Dict, job_requirements: str = None) -> Dict:
        """Parse LLM response"""
        try:
            # Try to extract JSON from response
            import json
            
            # Find JSON in response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                analysis = json.loads(json_str)
            else:
                analysis = self._heuristic_analysis(resume_json, job_requirements)
            
            analysis["logs"] = self.logs
            analysis["success"] = True
            return analysis
        
        except Exception as e:
            self._log(f"Failed to parse LLM response: {e}", "WARNING")
            return self._heuristic_analysis(resume_json, job_requirements)
    
    def _heuristic_analysis(self, resume_json: Dict, job_requirements: str = None) -> Dict:
        """
        Provide heuristic analysis when LLM is unavailable
        NO mock data - based on actual resume content
        Optionally compares to job requirements if provided
        """
        # Count actual data
        skills_count = len(resume_json.get("skills", []))
        experience_count = len(resume_json.get("experience", []))
        education_count = len(resume_json.get("education", []))
        
        # Detect skills categories
        skills = resume_json.get("skills", [])
        skill_categories = {}
        for skill in skills:
            cat = skill.get("category", "other")
            skill_categories[cat] = skill_categories.get(cat, 0) + 1
        
        # Determine seniority based on experience
        seniority = "junior"
        if experience_count >= 3:
            seniority = "mid"
        if experience_count >= 7:
            seniority = "senior"
        if experience_count >= 12:
            seniority = "lead"
        
        # Identify strengths
        strengths = []
        if skills_count > 10:
            strengths.append("Strong technical skill set")
        if education_count > 0:
            strengths.append("Formal education")
        if experience_count > 0:
            strengths.append("Professional experience")
        if skill_categories.get("programming_languages", 0) > 3:
            strengths.append("Multiple programming languages")
        if skill_categories.get("cloud_devops", 0) > 0:
            strengths.append("Cloud/DevOps capabilities")
        
        # Identify weaknesses
        weaknesses = []
        if skills_count < 5:
            weaknesses.append("Limited skill diversity")
        if experience_count == 0:
            weaknesses.append("No professional experience documented")
        if education_count == 0:
            weaknesses.append("No formal education listed")
        if not resume_json.get("summary"):
            weaknesses.append("No professional summary")
        
        # Recommended roles
        recommended_roles = self._recommend_roles(skill_categories, experience_count)
        
        # Score calculation (0-100)
        base_score = 50
        if skills_count > 5:
            base_score += 15
        if experience_count > 0:
            base_score += min(20, experience_count * 2)
        if education_count > 0:
            base_score += 10
        if resume_json.get("summary"):
            base_score += 5
        
        overall_score = min(100, base_score)
        
        analysis = {
            "executive_summary": f"Resume shows {seniority}-level candidate with {skills_count} skills and {experience_count} positions",
            "strengths": strengths or ["Resume contains structured information"],
            "weaknesses": weaknesses or ["All core sections present"],
            "opportunities": self._identify_opportunities(skill_categories),
            "technical_fit": {
                "score": overall_score - 10 if experience_count < 3 else overall_score,
                "explanation": f"Based on {skills_count} technical skills detected"
            },
            "cultural_fit": {
                "score": overall_score,
                "explanation": "Based on professional background and skills"
            },
            "seniority_level": seniority,
            "recommended_roles": recommended_roles,
            "missing_skills": self._suggest_missing_skills(skill_categories),
            "key_achievements": [exp.get("role", "") for exp in resume_json.get("experience", [])[:3]],
            "overall_score": overall_score,
            "key_metrics": {
                "skills_count": skills_count,
                "experience_count": experience_count,
                "education_count": education_count,
                "skill_categories": skill_categories,
                "seniority_years": experience_count
            },
            "logs": self.logs,
            "success": True,
            "analysis_type": "heuristic"
        }
        
        # Add job requirements analysis if provided
        if job_requirements:
            analysis["gap_analysis"] = self._analyze_job_fit(
                resume_json, 
                job_requirements, 
                skill_categories
            )
            analysis["hire_recommendation"] = self._make_hire_recommendation(
                analysis["gap_analysis"],
                overall_score
            )
            self._log(f"Job-specific analysis: {analysis['hire_recommendation']}")
        
        self._log(f"Heuristic analysis: score {overall_score}/100, seniority {seniority}")
        
        return analysis
    
    def _recommend_roles(self, skill_categories: Dict, experience_count: int) -> List[str]:
        """Recommend roles based on skills"""
        roles = []
        
        if skill_categories.get("programming_languages", 0) > 3:
            roles.append("Software Engineer")
        if skill_categories.get("data_ml", 0) > 0:
            roles.append("Data Scientist")
        if skill_categories.get("cloud_devops", 0) > 0:
            roles.append("DevOps Engineer")
        if skill_categories.get("cloud_devops", 0) > 2 and experience_count > 5:
            roles.append("Cloud Architect")
        if skill_categories.get("frameworks", 0) > 2:
            roles.append("Full-Stack Developer")
        
        # Default if no specific match
        if not roles:
            if experience_count > 5:
                roles = ["Senior Developer", "Technical Lead"]
            else:
                roles = ["Software Developer", "Junior Developer"]
        
        return roles
    
    def _identify_opportunities(self, skill_categories: Dict) -> List[str]:
        """Identify growth opportunities"""
        opportunities = []
        
        if skill_categories.get("programming_languages", 0) < 3:
            opportunities.append("Learn additional programming languages")
        if skill_categories.get("cloud_devops", 0) == 0:
            opportunities.append("Develop cloud/DevOps skills")
        if skill_categories.get("data_ml", 0) == 0:
            opportunities.append("Explore machine learning opportunities")
        
        return opportunities
    
    def _suggest_missing_skills(self, skill_categories: Dict) -> List[str]:
        """Suggest missing skills based on profile"""
        missing = []
        
        if skill_categories.get("programming_languages", 0) > 0:
            # Already has programming
            if "python" not in str(skill_categories) and skill_categories.get("data_ml", 0) == 0:
                missing.append("Python (if pursuing data science)")
            if skill_categories.get("cloud_devops", 0) == 0:
                missing.append("AWS/Azure/GCP")
        
        return missing
    
    def _analyze_job_fit(self, resume_json: Dict, job_requirements: str, skill_categories: Dict) -> Dict:
        """
        Analyze how well the resume matches job requirements
        Returns gap analysis with required vs missing skills
        """
        resume_skills = set(s.lower() if isinstance(s, str) else s.get("name", "").lower() 
                           for s in resume_json.get("skills", []))
        
        # Parse job requirements to extract common keywords (simple heuristic)
        job_lower = job_requirements.lower()
        
        # Common tech skills and roles
        common_skills = {
            "python", "javascript", "java", "csharp", "c#", "c++", "golang", "rust", "typescript",
            "react", "angular", "vue", "nodejs", "node.js", "express", "django", "flask",
            "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "cicd",
            "sql", "mysql", "postgresql", "mongodb", "dynamodb",
            "git", "linux", "unix", "windows", "macos",
            "agile", "scrum", "devops", "microservices",
            "api", "rest", "graphql", "websocket",
            "machine learning", "ml", "ai", "tensorflow", "pytorch",
            "html", "css", "sass", "webpack", "npm", "yarn"
        }
        
        required_skills = set()
        for skill in common_skills:
            if skill in job_lower:
                required_skills.add(skill.replace("c#", "csharp"))
        
        # Find missing skills
        missing_skills = required_skills - resume_skills
        matched_skills = required_skills & resume_skills
        
        # Extract requirements analysis
        years_req = "3" if "3+" in job_requirements or "3 years" in job_lower else "not specified"
        seniority_keywords = ["junior", "mid", "senior", "lead", "principal", "staff"]
        role_seniority = next((kw for kw in seniority_keywords if kw in job_lower), "not specified")
        
        return {
            "required_skills": list(required_skills),
            "matched_skills": list(matched_skills),
            "missing_skills": list(missing_skills),
            "skills_match_ratio": round(len(matched_skills) / len(required_skills) * 100, 1) if required_skills else 0,
            "required_experience": f"{years_req} years",
            "role_seniority": role_seniority,
            "analysis": f"Matched {len(matched_skills)}/{len(required_skills)} required skills"
        }
    
    def _make_hire_recommendation(self, gap_analysis: Dict, base_score: int) -> str:
        """
        Make a hire/no-hire recommendation based on gap analysis and score
        """
        match_ratio = gap_analysis.get("skills_match_ratio", 0)
        missing_count = len(gap_analysis.get("missing_skills", []))
        
        # Decision logic
        if match_ratio >= 80 and base_score >= 75:
            return "YES"
        elif match_ratio >= 60 and base_score >= 60:
            return "MAYBE"
        else:
            return "NO"
    
    def _log(self, message: str, level: str = "INFO"):
        """Add to logs"""
        log_entry = f"[{level}] {message}"
        self.logs.append(log_entry)
        
        if level == "ERROR":
            logger.error(message)
        else:
            logger.info(message)