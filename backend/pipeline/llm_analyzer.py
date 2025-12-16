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
               job_requirements: str = None,
               is_single_mode: bool = False) -> Dict[str, Any]:
        """
        Perform comprehensive LLM analysis - PASS 1
        
        Args:
            resume_json: Structured resume data
            resume_markdown: Markdown version of resume
            raw_text: Original raw text
            job_requirements: Optional job description to assess fit
            is_single_mode: True if single-CV mode, False if batch mode
        
        Returns:
            Analysis results with scoring and recommendations
        """
        self.logs = []
        self.job_requirements = job_requirements
        self.is_single_mode = is_single_mode  # Store for prompt building
        
        # If no LLM available, provide heuristic analysis
        if not self.client:
            self._log("No LLM client available, using heuristic analysis")
            return self._heuristic_analysis(resume_json, job_requirements)
        
        try:
            # Prepare prompt with mode awareness
            prompt = self._build_analysis_prompt(resume_markdown, job_requirements, is_single_mode)
            
            # Get analysis from LLM
            analysis_text = self._call_llm(prompt, force_json=True)
            
            # Parse response
            analysis = self._parse_analysis(analysis_text, resume_json, job_requirements)
            
            self._log("LLM analysis complete")
            return analysis
            
        except Exception as e:
            self._log(f"LLM analysis failed: {e}, falling back to heuristics", "ERROR")
            return self._heuristic_analysis(resume_json)
    
    def _call_llm(self, prompt: str, force_json: bool = True) -> str:
        """
        Call LLM with prompt using streaming for real-time output
        
        ENFORCEMENT:
        - Ollama: temperature ≤ 0.3 (deterministic)
        - Ollama: format=json (structured output, if requested)
        - Streaming mode (no buffering)
        """
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert resume analyst and HR consultant."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,  # ENFORCED: Low temperature for deterministic output
                    max_tokens=2500
                )
                return response.choices[0].message.content
            
            elif self.provider == "ollama":
                # MANDATORY ENFORCEMENT FOR OLLAMA
                log_message = f"[LLM] Calling Ollama with deterministic settings (temp=0.3, format={'json' if force_json else 'text'})"
                self._log(log_message)

                # Base parameters for the call
                params = {
                    'model': self.model,
                    'prompt': prompt,
                    'stream': True,
                    'options': {
                        'temperature': 0.3
                    }
                }

                # Conditionally add the format parameter
                if force_json:
                    params['format'] = 'json'

                response = self.client.generate(**params)
                
                # Accumulate streamed response
                full_response = ""
                for chunk in response:
                    # Ollama returns Pydantic objects, not dicts
                    # Access `response` attribute directly
                    if hasattr(chunk, 'response'):
                        text_chunk = chunk.response or ""
                    elif isinstance(chunk, dict):
                        text_chunk = chunk.get('response', '')
                    else:
                        text_chunk = ""
                    full_response += text_chunk
                
                self._log(f"[LLM] Response received: {len(full_response)} chars")
                return full_response
            
            else:
                # Custom provider
                self._log("Custom LLM provider not implemented, using heuristics")
                return ""
        
        except Exception as e:
            self._log(f"LLM call failed: {e}", "ERROR")
            raise
    
    def _call_ollama(self, prompt: str) -> str:
        """
        Call Ollama directly for role recommendations (non-JSON format)
        """
        try:
            if self.provider != "ollama" or not self.client:
                raise Exception("Ollama client not available")
            
            self._log(f"[LLM] Calling Ollama for role recommendations")
            
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                stream=False,
                temperature=0.7,  # Higher temperature for creative role generation
            )
            
            if isinstance(response, dict):
                return response.get('response', '')
            return str(response)
            
        except Exception as e:
            self._log(f"Ollama call failed: {e}", "ERROR")
            raise
    
    def _build_analysis_prompt(self, resume_markdown: str, job_requirements: str = None, is_single_mode: bool = False) -> str:
        """
        Build analysis prompt for LLM with MANDATORY job requirements enforcement
        
        CRITICAL: Mode-specific prompt guardrails:
        - Single-CV mode: "This is a single candidate. Do not compare against others."
        - Batch mode: "You are evaluating candidates independently in PASS 1."
        
        This prompt MUST be used with:
        - Structured JSON output (format=json in Ollama)
        - Low temperature (≤ 0.3) for consistency
        - All sections must reference job alignment
        """
        
        # ==== MODE-SPECIFIC GUARDRAIL ====
        mode_instruction = ""
        if is_single_mode:
            mode_instruction = """
CRITICAL CONSTRAINT - SINGLE CANDIDATE MODE:
This is a SINGLE candidate being analyzed in isolation.
Do NOT compare against other candidates.
Do NOT reference "other candidates" or "compared to".
Do NOT mention comparative rankings or relative positions.
Provide ONLY standalone analysis for this one person.
"""
        else:
            mode_instruction = """
PASS 1 CONSTRAINT - BATCH MODE:
You are evaluating this candidate independently in PASS 1.
Do NOT perform comparative analysis yet.
Do NOT compare against other candidates.
Comparative analysis will happen in PASS 2 with all candidates together.
Focus on ONLY this candidate's individual profile.
"""
        
        # ==== MANDATORY JOB REQUIREMENTS SECTION ====
        job_requirements_section = ""
        job_used_instruction = ""
        
        if job_requirements and job_requirements.strip():
            job_requirements_section = f"""
=== TARGET JOB REQUIREMENTS (DO NOT IGNORE - MANDATORY) ===
{job_requirements}
=== END OF JOB REQUIREMENTS ===
"""
            job_used_instruction = """
CRITICAL ENFORCEMENT:
- Every single section of your output MUST explicitly reference alignment to the target job
- Do NOT generate a generic resume summary
- PENALIZE missing required skills (reduce scores appropriately)
- EXPLAIN ALL MISMATCHES explicitly
- If a skill is required but missing, highlight it as a CRITICAL GAP
- If a skill is present and required, highlight it as a MATCHED STRENGTH
- Your final verdict MUST explicitly state job fit (YES, MAYBE, or NO)
"""
        else:
            job_requirements_section = """
=== NO JOB REQUIREMENTS PROVIDED ===
Candidate will receive GENERIC analysis without job-specific alignment.
"""
            job_used_instruction = """
NOTE: No job requirements were provided.
This is a GENERIC resume analysis without job-specific fit assessment.
"""
        
        # ==== STRUCTURED OUTPUT REQUIREMENTS ====
        prompt = f"""RESUME ANALYSIS - STRUCTURED OUTPUT (JSON ONLY)

{mode_instruction}

{job_requirements_section}

CANDIDATE RESUME:
{resume_markdown}

{job_used_instruction}

INSTRUCTIONS:
1. Analyze ONLY the provided resume
2. Reference the job requirements in EVERY major section
3. Output MUST be valid JSON with the exact structure below
4. Do not include any markdown, explanations, or text outside JSON
5. All scores must be 0-100 integers
6. All arrays must contain strings

OUTPUT MUST BE VALID JSON IN THIS EXACT STRUCTURE:
{{
    "candidate_name": "Extract candidate's full name from resume",
    "job_requirements_analyzed": {"true" if job_requirements and job_requirements.strip() else "false"},
    "executive_summary": "2-3 sentence assessment of overall fit relative to job (or generic if no job provided)",
    "experience_summary": "Brief summary of candidate's work experience, years, and key roles",
    "job_alignment_summary": "Paragraph explaining how resume aligns or misaligns with job requirements",
    "matched_requirements": [
        {{"requirement": "Required Skill", "evidence": "How/where it appears in resume", "strength": "brief assessment"}}
    ],
    "missing_requirements": [
        {{"requirement": "Required Skill", "impact": "why missing matters", "severity": "CRITICAL|HIGH|MEDIUM"}}
    ],
    "strengths": ["strength 1", "strength 2", "strength 3"],
    "weaknesses": ["weakness 1", "weakness 2"],
    "opportunities": ["improvement 1", "improvement 2"],
    "technical_fit": {{"score": 0-100, "explanation": "Technical skill alignment to job"}},
    "cultural_fit": {{"score": 0-100, "explanation": "Cultural/experience alignment to job"}},
    "seniority_level": "junior|mid|senior|lead|executive",
    "role_fit_verdict": {{"recommendation": "YES|MAYBE|NO", "confidence": 0-100, "rationale": "Why this recommendation"}},
    "recommended_roles": [
        {{"role": "Job Title", "fit_score": 0-100, "reasoning": "Why this candidate fits this role"}}
    ],
    "critical_gaps": ["gap 1", "gap 2"],
    "key_achievements": ["achievement 1", "achievement 2"],
    "overall_score": 0-100,
    "key_metrics": {{"years_experience": 0, "skills_count": 0, "education_count": 0}},
    "skills": {{"technical": ["skill1", "skill2", ...], "soft": ["skill1", "skill2", ...]}},
    "certifications": ["certification 1", "certification 2", ...]
}}

VALIDATION RULES:
- If job requirements were provided, role_fit_verdict MUST address job fit, not generic fit
- If job requirements were NOT provided, state this in job_alignment_summary
- All scores MUST be integers 0-100
- All strings must be under 500 characters
- No nested objects beyond what's shown
- Matched/missing requirements arrays CAN be empty if not applicable
- recommended_roles MUST have at least 5 roles
- Extract candidate_name from the resume text
- experience_summary should briefly describe work history
- skills and certifications must be extracted from resume
"""
        return prompt
    
    def _parse_analysis(self, response_text: str, resume_json: Dict, job_requirements: str = None) -> Dict:
        """
        Parse LLM response with MANDATORY verification of job requirements usage
        
        Returns analysis dict with job_requirements_used and job_requirements_hash flags
        """
        import hashlib
        
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
            
            # ==== MANDATORY: Add job requirements verification flags ====
            job_requirements_raw = job_requirements or ""
            job_requirements_hash = hashlib.sha256(job_requirements_raw.encode()).hexdigest()
            
            # Verify job requirements were actually used
            job_requirements_used = False
            if job_requirements and job_requirements.strip():
                # Check if LLM referenced job requirements in analysis
                job_referenced = (
                    analysis.get("job_requirements_analyzed") == True or
                    "job_alignment_summary" in analysis and analysis["job_alignment_summary"] and 
                    len(analysis["job_alignment_summary"]) > 20
                )
                job_requirements_used = job_referenced
                self._log(f"[VERIFICATION] Job requirements used: {job_requirements_used}")
            
            # Add mandatory fields
            analysis["job_requirements_used"] = job_requirements_used
            analysis["job_requirements_hash"] = job_requirements_hash
            analysis["job_requirements_raw"] = job_requirements_raw
            
            # If job requirements were provided but not used, mark as warning
            if job_requirements and job_requirements.strip() and not job_requirements_used:
                self._log("[WARNING] Job requirements were provided but may not have been properly analyzed", "WARNING")
                analysis["job_requirements_warning"] = True
            
            analysis["logs"] = self.logs
            analysis["success"] = True
            return analysis
        
        except Exception as e:
            self._log(f"Failed to parse LLM response: {e}", "WARNING")
            # Return heuristic analysis with verification flags
            analysis = self._heuristic_analysis(resume_json, job_requirements)
            
            # Add verification flags even for heuristic analysis
            job_requirements_raw = job_requirements or ""
            job_requirements_hash = hashlib.sha256(job_requirements_raw.encode()).hexdigest()
            analysis["job_requirements_used"] = False
            analysis["job_requirements_hash"] = job_requirements_hash
            analysis["job_requirements_raw"] = job_requirements_raw
            
            return analysis
    
    def _heuristic_analysis(self, resume_json: Dict, job_requirements: str = None) -> Dict:
        """
        Provide heuristic analysis when LLM is unavailable
        NO mock data - based on actual resume content
        Optionally compares to job requirements if provided
        """
        if isinstance(resume_json, str):
            try:
                import json
                resume_json = json.loads(resume_json)
            except:
                self._log("resume_json is a string and failed JSON parsing in heuristic", "ERROR")
                resume_json = {}

        # Count actual data
        skills_count = len(resume_json.get("skills", []))
        experience_count = len(resume_json.get("experience", []))
        education_count = len(resume_json.get("education", []))
        
        # Detect skills categories
        skills = resume_json.get("skills", [])
        skill_categories = {}
        for skill in skills:
            if isinstance(skill, str):
                # Handle string skills (from ResumeParser)
                cat = "technical" # Default category
                skill_categories[cat] = skill_categories.get(cat, 0) + 1
            elif isinstance(skill, dict):
                # Handle dict skills (from older parser/LLM)
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
    
    def _recommend_roles(self, skill_categories: Dict, experience_count: int) -> List[Dict]:
        """Use Qwen LLM to recommend 20 detailed roles with icons and explanations"""
        
        # Prepare context for the LLM
        skills_text = ", ".join([f"{k}: {v}" for k, v in skill_categories.items()])
        
        prompt = f"""Based on the following candidate profile, recommend exactly 20 job roles that would be a good fit.

Candidate Profile:
- Skill Categories: {skills_text}
- Years of Experience: {experience_count}

For each role, provide:
1. Role title
2. Brief explanation (1-2 sentences) of why this role fits the candidate
3. Fit score (0-100) indicating how well the candidate matches
4. An emoji icon that represents the role

Format your response as a JSON array with exactly 20 roles:
[
  {{
    "title": "Software Engineer",
    "explanation": "Strong programming skills and technical background make this an excellent fit.",
    "fit_score": 95,
    "icon": "💻"
  }},
  ...
]

Return ONLY the JSON array, no additional text."""

        try:
            # Call Qwen LLM
            response = self._call_ollama(prompt)
            
            # Parse JSON response
            import json
            import re
            
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                roles = json.loads(json_match.group(0))
                
                # Validate we have 20 roles
                if isinstance(roles, list) and len(roles) >= 20:
                    return roles[:20]
                elif isinstance(roles, list) and len(roles) > 0:
                    # If less than 20, return what we have
                    self._log(f"Warning: LLM returned {len(roles)} roles instead of 20")
                    return roles
            
            self._log("Failed to parse LLM response for role recommendations")
            
        except Exception as e:
            self._log(f"Error calling LLM for role recommendations: {str(e)}")
        
        # Fallback: Generate basic recommendations
        return self._generate_fallback_roles(skill_categories, experience_count)
    
    def _generate_fallback_roles(self, skill_categories: Dict, experience_count: int) -> List[Dict]:
        """Generate fallback role recommendations if LLM fails"""
        roles = []
        
        # Define role mappings
        role_mappings = [
            {"title": "Software Engineer", "icon": "💻", "base_score": 80},
            {"title": "Full-Stack Developer", "icon": "🌐", "base_score": 75},
            {"title": "Backend Developer", "icon": "⚙️", "base_score": 75},
            {"title": "Frontend Developer", "icon": "🎨", "base_score": 70},
            {"title": "Data Scientist", "icon": "📊", "base_score": 70},
            {"title": "Machine Learning Engineer", "icon": "🤖", "base_score": 65},
            {"title": "DevOps Engineer", "icon": "🔧", "base_score": 65},
            {"title": "Cloud Architect", "icon": "☁️", "base_score": 60},
            {"title": "Technical Lead", "icon": "👔", "base_score": 70},
            {"title": "Solutions Architect", "icon": "🏗️", "base_score": 65},
            {"title": "Database Administrator", "icon": "🗄️", "base_score": 60},
            {"title": "Site Reliability Engineer", "icon": "🛡️", "base_score": 65},
            {"title": "QA Engineer", "icon": "🔍", "base_score": 60},
            {"title": "Security Engineer", "icon": "🔐", "base_score": 60},
            {"title": "Mobile Developer", "icon": "📱", "base_score": 55},
            {"title": "Product Manager", "icon": "📋", "base_score": 55},
            {"title": "Engineering Manager", "icon": "👨‍💼", "base_score": 65},
            {"title": "Systems Engineer", "icon": "🖥️", "base_score": 60},
            {"title": "AI Engineer", "icon": "🧠", "base_score": 65},
            {"title": "Platform Engineer", "icon": "🚀", "base_score": 60}
        ]
        
        # Adjust scores based on skills and experience
        for role_info in role_mappings:
            score = role_info["base_score"]
            
            # Boost score based on experience
            if experience_count > 5:
                score += 10
            elif experience_count > 2:
                score += 5
            
            # Boost based on skill categories
            if "programming_languages" in skill_categories:
                score += min(10, skill_categories["programming_languages"] * 2)
            
            score = min(100, score)
            
            roles.append({
                "title": role_info["title"],
                "explanation": f"Based on your {experience_count} years of experience and skill profile, this role could be a good fit.",
                "fit_score": score,
                "icon": role_info["icon"]
            })
        
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
    
    def analyze_comparative(self, 
                           candidates: List[Dict],
                           job_requirements: str = "") -> Dict[str, Any]:
        """
        PASS 2: Comparative analysis across all candidates
        
        Receives all candidates with their PASS 1 results and performs
        cross-candidate comparison using a single LLM call.
        
        Args:
            candidates: List of candidate dicts with document_id, name, skills, etc.
            job_requirements: Job requirements for context
            
        Returns:
            Dict with comparative_analysis results
        """
        self._log("Starting PASS 2: Comparative cross-candidate analysis")
        self._log(f"Analyzing {len(candidates)} candidates comparatively")
        
        try:
            # Build comprehensive prompt with ALL candidates
            prompt = self._build_comparative_prompt(candidates, job_requirements)
            
            # Call LLM with ALL candidates in single request
            self._log("Calling LLM for comparative evaluation...")
            response = self._call_llm(prompt, force_json=True)
            
            # Parse comparative response
            comparative_result = self._parse_comparative_response(response, candidates)
            comparative_result["logs"] = self.logs
            
            self._log("✓ Comparative analysis complete")
            return comparative_result
            
        except Exception as e:
            error_msg = f"Comparative analysis failed: {str(e)}"
            self._log(error_msg, "ERROR")
            return {
                "error": error_msg,
                "logs": self.logs,
                "comparative_analysis": None
            }
    
    def _build_comparative_prompt(self, candidates: List[Dict], job_requirements: str) -> str:
        """
        Simplified comparative analysis prompt for Qwen2.5
        Focus on core fields only, minimal formatting requirements
        """
        
        # Build candidate profiles
        candidate_profiles = ""
        for idx, cand in enumerate(candidates, 1):
            doc_id = cand.get("document_id", f"DOC_{idx}")
            name = cand.get("name", f"Candidate_{idx}")
            experience = cand.get("experience_summary", "")[:200]  # Truncate to 200 chars
            skills = cand.get("skills", {}).get("technical", [])[:8]
            score = int(cand.get("preliminary_fit_score", 0))
            seniority = cand.get("seniority_level", "mid")
            
            candidate_profiles += f"Candidate {idx} ({doc_id}): {name}, {seniority}, {score}/100, Skills: {', '.join(skills)}\n"
        
        prompt = f"""Compare these {len(candidates)} candidates and return ONLY valid JSON:

CANDIDATES:
{candidate_profiles}

JOB CONTEXT: {job_requirements if job_requirements else 'General evaluation'}

Return ONLY this exact JSON structure (no markdown, no explanation):
{{
    "executive_summary": "1 paragraph comparing all candidates",
    "comparative_ranking": [
        {{"document_id": "DOC_1", "rank": 1, "normalized_fit_score": 85, "rationale": "Why ranked first"}}
    ],
    "strengths_comparison": "Compare strengths across all candidates",
    "weaknesses_comparison": "Compare weaknesses across all candidates",
    "skill_coverage_matrix": {{"DOC_1": {{"covered": ["skill1"], "missing": ["skill2"]}}}},
    "strongest_candidate": {{"document_id": "DOC_1", "reason": "Why best"}},
    "best_skill_coverage": {{"document_id": "DOC_1", "skills": ["list"], "reason": "Why"}},
    "hiring_recommendations": {{"DOC_1": "HIRE/CONSIDER/MAYBE with brief reason"}}
}}"""
        
        return prompt
    
    def _parse_comparative_response(self, response: str, candidates: List[Dict]) -> Dict:
        """Parse comparative LLM response into structured format"""
        
        try:
            # Extract JSON from response
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            
            comparative_data = json.loads(json_str)
            self._log("✓ Comparative response parsed successfully")
            
            # Verify it's truly comparative (not just repeated single evaluations)
            self._verify_comparative_quality(comparative_data, candidates)
            
            # Ensure all required frontend fields are present with proper structure
            structured_data = self._structure_for_frontend(comparative_data, candidates)
            
            return {
                "comparative_analysis": structured_data,
                "success": True
            }
            
        except json.JSONDecodeError as e:
            self._log(f"Failed to parse comparative JSON: {str(e)}", "ERROR")
            # Fall back to text response
            return {
                "comparative_analysis": {
                    "raw_response": response,
                    "parse_error": str(e)
                },
                "success": False
            }
    
    def _structure_for_frontend(self, data: Dict, candidates: List[Dict]) -> Dict:
        """
        Ensure the comparative data is structured exactly as frontend expects
        Includes smart fallbacks to ensure fields are never completely empty
        """
        structured = {
            "executive_summary": data.get("executive_summary", ""),
            "comparative_ranking": data.get("comparative_ranking", []),
            "strengths_comparison": data.get("strengths_comparison", ""),
            "weaknesses_comparison": data.get("weaknesses_comparison", ""),
            "skill_coverage_matrix": data.get("skill_coverage_matrix", {}),
            "strongest_candidate": data.get("strongest_candidate", {}),
            "best_skill_coverage": data.get("best_skill_coverage", {}),
            "hiring_recommendations": data.get("hiring_recommendations", {})
        }
        
        # CRITICAL: Generate fallback data if core fields are missing
        # This ensures the frontend never displays completely empty sections
        if not structured["comparative_ranking"]:
            self._log("⚠ No comparative_ranking in response, generating fallback", "WARNING")
            # Generate basic ranking from candidates' scores if available
            structured["comparative_ranking"] = self._generate_fallback_ranking(candidates)
        
        if not structured["executive_summary"]:
            self._log("⚠ No executive_summary in response, generating fallback", "WARNING")
            structured["executive_summary"] = self._generate_fallback_summary(candidates)
        
        if not structured["strengths_comparison"]:
            self._log("⚠ No strengths_comparison in response, generating fallback", "WARNING")
            structured["strengths_comparison"] = self._generate_fallback_strengths(candidates)
        
        if not structured["weaknesses_comparison"]:
            self._log("⚠ No weaknesses_comparison in response, generating fallback", "WARNING")
            structured["weaknesses_comparison"] = self._generate_fallback_weaknesses(candidates)
        
        if not structured["skill_coverage_matrix"]:
            self._log("⚠ No skill_coverage_matrix in response, generating fallback", "WARNING")
            structured["skill_coverage_matrix"] = self._generate_fallback_skills(candidates)
        
        if not structured["hiring_recommendations"]:
            self._log("⚠ No hiring_recommendations in response, generating fallback", "WARNING")
            structured["hiring_recommendations"] = self._generate_fallback_recommendations(candidates)
        
        # Optional fields that enhance the frontend display
        if "candidate_profiles" in data:
            structured["candidate_profiles"] = data["candidate_profiles"]
        if "experience_summaries" in data:
            structured["experience_summaries"] = data["experience_summaries"]
        if "skills_and_entities" in data:
            structured["skills_and_entities"] = data["skills_and_entities"]
        if "ai_fit_scores" in data:
            structured["ai_fit_scores"] = data["ai_fit_scores"]
        if "evaluation_factors" in data:
            structured["evaluation_factors"] = data["evaluation_factors"]
        if "recommended_roles" in data:
            structured["recommended_roles"] = data["recommended_roles"]
        
        self._log(f"✓ Structured data for frontend with {len(structured)} fields")
        return structured
    
    def _generate_fallback_ranking(self, candidates: List[Dict]) -> List[Dict]:
        """Generate fallback ranking from preliminary scores"""
        ranking = []
        sorted_candidates = sorted(
            candidates,
            key=lambda x: x.get("preliminary_fit_score", 0),
            reverse=True
        )
        for rank, cand in enumerate(sorted_candidates, 1):
            ranking.append({
                "document_id": cand.get("document_id", f"doc_{rank}"),
                "rank": rank,
                "normalized_fit_score": int(cand.get("preliminary_fit_score", 0)),
                "rationale": f"Ranked #{rank} based on PASS 1 analysis"
            })
        return ranking
    
    def _generate_fallback_summary(self, candidates: List[Dict]) -> str:
        """Generate fallback executive summary"""
        names = [c.get("name", "Candidate") for c in candidates]
        if len(names) == 2:
            return f"Comparative analysis of {names[0]} and {names[1]}. Both candidates have been evaluated based on their resume content, experience, and skill alignment."
        elif len(names) > 2:
            return f"Comparative analysis of {', '.join(names[:-1])}, and {names[-1]}. All candidates have been evaluated based on their resume content, experience, and skill alignment."
        return "Comparative candidate analysis based on PASS 1 results."
    
    def _generate_fallback_strengths(self, candidates: List[Dict]) -> str:
        """Generate fallback strengths comparison"""
        parts = []
        for cand in candidates:
            skills = cand.get("skills", {}).get("technical", [])[:3]
            seniority = cand.get("seniority_level", "Unknown")
            if skills:
                parts.append(f"{cand.get('name', 'Candidate')} ({seniority}): {', '.join(skills)}")
        return " | ".join(parts) if parts else "Candidates assessed on technical and soft skills from PASS 1 analysis."
    
    def _generate_fallback_weaknesses(self, candidates: List[Dict]) -> str:
        """Generate fallback weaknesses comparison"""
        return f"Detailed weakness analysis pending. {len(candidates)} candidate(s) evaluated based on available experience and skills."
    
    def _generate_fallback_skills(self, candidates: List[Dict]) -> Dict:
        """Generate fallback skill coverage matrix"""
        matrix = {}
        for cand in candidates:
            doc_id = cand.get("document_id", "Unknown")
            skills = cand.get("skills", {})
            matrix[doc_id] = {
                "covered": skills.get("technical", [])[:5],
                "missing": []  # Will be filled based on job requirements if available
            }
        return matrix
    
    def _generate_fallback_recommendations(self, candidates: List[Dict]) -> Dict:
        """Generate fallback hiring recommendations"""
        recs = {}
        for cand in candidates:
            doc_id = cand.get("document_id", "Unknown")
            score = cand.get("preliminary_fit_score", 0)
            
            if score >= 75:
                recommendation = "STRONG CANDIDATE - Recommend for interview based on PASS 1 analysis"
            elif score >= 60:
                recommendation = "GOOD CANDIDATE - Consider for interview based on PASS 1 analysis"
            else:
                recommendation = "POSSIBLE CANDIDATE - Review further based on PASS 1 analysis"
            
            recs[doc_id] = recommendation
        return recs
    
    def _verify_comparative_quality(self, comparative_data: Dict, candidates: List[Dict]):
        """
        Verify the comparative analysis is truly comparative and not just
        repeated single-candidate evaluations (FAILURE CRITERIA CHECK)
        """
        
        try:
            # Check 1: Ranking should be different (not all same score)
            ranking = comparative_data.get("comparative_ranking", [])
            if ranking:
                scores = [r.get("normalized_fit_score", 0) for r in ranking]
                if len(set(scores)) == 1:
                    self._log("⚠ WARNING: All candidates have identical scores - may not be truly comparative", "ERROR")
                else:
                    self._log(f"✓ Scores vary across candidates: {scores}")
            
            # Check 2: Rankings reference different candidates
            ranking_ids = [r.get("document_id") for r in ranking]
            if len(ranking_ids) != len(set(ranking_ids)):
                self._log("⚠ WARNING: Duplicate document IDs in ranking", "ERROR")
            
            # Check 3: Summaries mention comparisons (not isolation)
            strengths = comparative_data.get("strengths_comparison", "")
            weaknesses = comparative_data.get("weaknesses_comparison", "")
            executive = comparative_data.get("executive_summary", "")
            
            comparison_keywords = ["compared", "stronger", "weaker", "better", "worse", "outranks", "vs", "both"]
            found_comparison = any(keyword in (strengths + weaknesses + executive).lower() 
                                 for keyword in comparison_keywords)
            
            if found_comparison:
                self._log("✓ Comparative language detected in analysis")
            else:
                self._log("⚠ WARNING: Limited comparative language detected", "ERROR")
            
        except Exception as e:
            self._log(f"Quality check warning: {str(e)}", "ERROR")