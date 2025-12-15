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
        """
        Call LLM with prompt using streaming for real-time output
        
        ENFORCEMENT:
        - Ollama: temperature ≤ 0.3 (deterministic)
        - Ollama: format=json (structured output)
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
                self._log(f"[LLM] Calling Ollama with deterministic settings (temp=0.3, format=json)")
                
                # Use streaming mode for unbuffered real-time output
                response = self.client.generate(
                    model=self.model,
                    prompt=prompt,
                    stream=True,                  # ENFORCED: Streaming enabled
                    temperature=0.3,              # ENFORCED: Low temperature for consistency
                    format="json"                 # ENFORCED: Structured JSON output
                )
                
                # Accumulate streamed response
                full_response = ""
                for chunk in response:
                    if isinstance(chunk, dict):
                        text_chunk = chunk.get('response', '')
                        full_response += text_chunk
                    else:
                        full_response += str(chunk)
                
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
    
    def _build_analysis_prompt(self, resume_markdown: str, job_requirements: str = None) -> str:
        """
        Build analysis prompt for LLM with MANDATORY job requirements enforcement
        
        This prompt MUST be used with:
        - Structured JSON output (format=json in Ollama)
        - Low temperature (≤ 0.3) for consistency
        - All sections must reference job alignment
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
    "job_requirements_analyzed": {"true" if job_requirements and job_requirements.strip() else "false"},
    "executive_summary": "2-3 sentence assessment of overall fit relative to job (or generic if no job provided)",
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
    "recommended_roles": ["role 1", "role 2"],
    "critical_gaps": ["gap 1", "gap 2"],
    "key_achievements": ["achievement 1", "achievement 2"],
    "overall_score": 0-100,
    "key_metrics": {{"years_experience": 0, "skills_count": 0, "education_count": 0}}
}}

VALIDATION RULES:
- If job requirements were provided, role_fit_verdict MUST address job fit, not generic fit
- If job requirements were NOT provided, state this in job_alignment_summary
- All scores MUST be integers 0-100
- All strings must be under 500 characters
- No nested objects beyond what's shown
- Matched/missing requirements arrays CAN be empty if not applicable
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
            response = self._call_llm(prompt)
            
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
        Build prompt for PASS 2 comparative analysis
        
        CRITICAL: This prompt must force Qwen2.5 to compare candidates
        against each other, not evaluate them independently.
        """
        
        # Build candidate profiles string
        candidate_profiles = ""
        for idx, cand in enumerate(candidates, 1):
            doc_id = cand.get("document_id", f"DOC_{idx}")
            name = cand.get("name", "Unknown")
            experience = cand.get("experience_summary", "Not specified")
            skills = cand.get("skills", {})
            
            tech_skills = skills.get("technical", [])[:5]
            soft_skills = skills.get("soft", [])[:3]
            preliminary_score = cand.get("preliminary_fit_score", 0)
            
            candidate_profiles += f"""
CANDIDATE {idx} (ID: {doc_id})
- Name: {name}
- Experience: {experience}
- Technical Skills: {', '.join(tech_skills) if tech_skills else 'N/A'}
- Soft Skills: {', '.join(soft_skills) if soft_skills else 'N/A'}
- Preliminary Score: {preliminary_score}/100
"""
        
        prompt = f"""YOU ARE A COMPARATIVE RECRUITMENT ANALYST

DO NOT evaluate candidates independently. You must compare them AGAINST EACH OTHER.

JOB REQUIREMENTS:
{job_requirements if job_requirements else "Generic evaluation - no specific requirements"}

CANDIDATES TO COMPARE:
{candidate_profiles}

CRITICAL INSTRUCTIONS:
1. Compare candidates RELATIVE to each other, not in absolute terms
2. Reference candidates by their document ID (DOC_X) throughout
3. Explain why Candidate A outranks Candidate B with specific details
4. Identify which candidate is strongest, which is weakest
5. Explain specific skill gaps for EACH candidate
6. Normalize scores so they reflect relative fit within this group
7. Provide different hiring recommendations for different candidates

OUTPUT FORMAT (JSON):
{{
    "comparative_ranking": [
        {{"document_id": "DOC_X", "rank": 1, "normalized_fit_score": XX, "rationale": "Why this candidate ranks first"}},
        ...
    ],
    "strengths_comparison": "Compare strengths across candidates. Which candidate excels where? Reference by DOC_ID.",
    "weaknesses_comparison": "Identify gaps. Which candidate lacks what? Why is DOC_X weak in Y?",
    "skill_coverage_matrix": {{"DOC_1": {{"covered": [...], "missing": [...]}}, ...}},
    "strongest_candidate": {{"document_id": "DOC_X", "reason": "Why this candidate is best"}},
    "best_skill_coverage": {{"document_id": "DOC_X", "skills": [...], "reason": "..."}},
    "hiring_recommendations": {{
        "DOC_1": "Specific recommendation for this candidate",
        "DOC_2": "Different recommendation for this candidate",
        ...
    }},
    "executive_summary": "2-3 sentence summary comparing all candidates"
}}

Remember: COMPARE not ISOLATE. Reference specific document IDs. Explain rankings with details."""
        
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
            
            return {
                "comparative_analysis": comparative_data,
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