"""
Executive Summary Engine
Handles the three guaranteed sections:
1. Candidate Profile (deterministic from parsing)
2. Experience Summary (Qwen-powered HR summary)
3. AI Executive Assessment (Qwen-powered comparative evaluation)
"""

import json
import logging
from typing import List, Dict, Optional
from backend.pipeline.resume_parser import ResumeParser
from backend.pipeline.llm_analyzer import LLMAnalyzer

logger = logging.getLogger("ExecutiveSummary")


class ExecutiveSummaryEngine:
    """
    Generates the three guaranteed sections using the proper division of labor:
    - Candidate Profile: Deterministic parsing (NO LLM)
    - Experience Summary: Qwen-powered summarization
    - AI Executive Assessment: Qwen-powered evaluation
    """
    
    def __init__(self, llm_analyzer: Optional[LLMAnalyzer] = None):
        """
        Initialize the engine
        
        Args:
            llm_analyzer: LLMAnalyzer instance (will create if None)
        """
        self.parser = ResumeParser()
        self.llm_analyzer = llm_analyzer or LLMAnalyzer(model="qwen2.5:7b-instruct-q4_K_M")
    
    def process_candidates(
        self,
        candidates: List[Dict],
        job_requirements: str = "",
        mode: str = "batch"
    ) -> Dict:
        """
        Process candidates and generate all three sections.
        
        Args:
            candidates: List of parsed candidate data from llm_analyzer
            job_requirements: Job description (optional)
            mode: "single" or "batch"
            
        Returns:
            {
                "candidates": [...],  # Candidate profiles
                "experience_summary": "...",
                "ai_executive_assessment": "...",
                "success": True
            }
        """
        
        logger.info(f"🧠 Executive Summary Engine: Processing {len(candidates)} candidates (mode={mode})")
        
        # STEP 1: Extract Candidate Profiles (deterministic - NO LLM)
        logger.info("📋 STEP 1: Building candidate profiles...")
        candidate_profiles = self._build_candidate_profiles(candidates)
        
        logger.info(f"   ✓ {len(candidate_profiles)} profiles created")
        
        # STEP 2: Generate Experience Summary (Qwen)
        logger.info("📊 STEP 2: Generating experience summary (Qwen)...")
        experience_summary = self._generate_experience_summary(
            candidate_profiles,
            job_requirements,
            mode
        )
        
        if not experience_summary:
            experience_summary = "Unable to generate experience summary at this time."
            logger.warning("   ⚠ Experience summary generation failed, using fallback")
        else:
            logger.info("   ✓ Experience summary generated")
        
        # STEP 3: Generate AI Executive Assessment (Qwen)
        logger.info("📈 STEP 3: Generating AI executive assessment (Qwen)...")
        ai_assessment = self._generate_ai_assessment(
            candidate_profiles,
            job_requirements,
            mode
        )
        
        if not ai_assessment:
            ai_assessment = "Unable to generate AI assessment at this time."
            logger.warning("   ⚠ AI assessment generation failed, using fallback")
        else:
            logger.info("   ✓ AI assessment generated")
        
        result = {
            "candidates": candidate_profiles,
            "experience_summary": experience_summary,
            "ai_executive_assessment": ai_assessment,
            "success": True
        }
        
        logger.info("✅ Executive summary engine complete")
        
        return result
    
    def _build_candidate_profiles(self, candidates: List[Dict]) -> List[Dict]:
        """
        Build deterministic candidate profiles from parsed data.
        NO LLM - purely deterministic extraction.
        """
        profiles = []
        
        for candidate in candidates:
            profile = {
                "candidate_id": candidate.get("candidate_id"),
                "document_id": candidate.get("document_id"),
                "filename": candidate.get("filename"),  # Added
                "name": candidate.get("name"),
                "email": candidate.get("email"),
                "phone": candidate.get("phone"),
                "linkedin": candidate.get("linkedin"),
                "github": candidate.get("github"),
                "other_links": candidate.get("other_links", []),
                
                # Content Fields
                "education": candidate.get("education", []),
                "experience": candidate.get("experience", []),
                "skills": candidate.get("skills", []),
                "certifications": candidate.get("certifications", []),
                "named_entities": candidate.get("entities", {}),  # Map from NLP result 'entities'
                
                # Analysis Fields
                "seniority_level": candidate.get("seniority_level", "Unknown"),
                "years_experience": candidate.get("years_experience", 0),
                "preliminary_fit_score": candidate.get("preliminary_fit_score", 0),
                "llm_analysis": candidate.get("llm_analysis", {})
            }
            profiles.append(profile)
        
        return profiles
    
    def _generate_experience_summary(
        self,
        profiles: List[Dict],
        job_requirements: str,
        mode: str
    ) -> Optional[str]:
        """
        Generate experience summary using Qwen.

        Prompt: Analyze education + experience across all candidates (batch) or single candidate (single).
        Format: Single professional paragraph for HR dashboard.
        """

        if mode == "single":
            # Single candidate mode - individual analysis
            profile = profiles[0]
            prompt = f"""You are an HR analyst.

You are given structured resume data for a single candidate.
Analyze and summarize their EDUCATION and PROFESSIONAL EXPERIENCE.

CANDIDATE:
{profile['name']} ({profile['seniority_level']}, {profile['years_experience']} years)

JOB CONTEXT:
{job_requirements if job_requirements else 'General evaluation'}

Instructions:
- Mention the candidate by name
- Analyze seniority, relevance, and career progression
- Highlight academic background
- Highlight work experience
- Be factual, concise, and professional
- Do NOT invent data
- Do NOT mention missing data unless relevant

Return a single professional paragraph suitable for an HR dashboard."""
        else:
            # Batch mode - comparative analysis (USER-PROVIDED PROMPT)
            candidate_summaries = []
            for profile in profiles:
                summary = f"- {profile['name']} ({profile['seniority_level']}, {profile['years_experience']} years)"
                candidate_summaries.append(summary)

            candidates_text = "\n".join(candidate_summaries)

            prompt = f"""You are an HR analyst.

You are given structured education and work experience data for multiple candidates.

CANDIDATES:
{candidates_text}

JOB CONTEXT:
{job_requirements if job_requirements else 'General evaluation'}

Tasks:
- Summarize each candidate's education and experience briefly
- Compare seniority, relevance, and progression
- Highlight who is strongest academically
- Highlight who is strongest professionally
- Do NOT rank numerically
- Be professional and factual

Return a single cohesive summary suitable for an executive dashboard."""

        try:
            response = self.llm_analyzer._call_llm(prompt, force_json=False)

            if response and response.strip():
                return response.strip()
            else:
                logger.warning("Empty response from LLM for experience summary")
                return None

        except Exception as e:
            logger.error(f"Error generating experience summary: {e}")
            return None
    
    def _generate_ai_assessment(
        self,
        profiles: List[Dict],
        job_requirements: str,
        mode: str
    ) -> Optional[str]:
        """
        Generate AI executive assessment using Qwen.

        Prompt: Deep comparative evaluation (batch) or individual assessment (single).
        Format: Executive HR judgment suitable for decision-making.
        """

        if mode == "single":
            # Single candidate mode - individual assessment
            profile = profiles[0]
            prompt = f"""You are a senior HR executive AI.

You are evaluating a single candidate for a role.

CANDIDATE:
Candidate: {profile['name']}
Seniority: {profile['seniority_level']}
Experience: {profile['years_experience']} years
Fit Score: {profile['preliminary_fit_score']}/100

JOB REQUIREMENTS:
{job_requirements if job_requirements else 'No specific requirements provided'}

Evaluate the candidate across:
- Experience depth
- Skill relevance
- Career trajectory
- Certifications
- Overall job fit

Rules:
- Mention strengths and weaknesses
- Be decisive and professional
- This is an assessment, not a summary
- Assume resume is accurate
- Maximum verbosity: medium

Output must be suitable for executive decision-making."""
        else:
            # Batch mode - comparative evaluation (USER-PROVIDED PROMPT)
            candidates_details = []
            for profile in profiles:
                detail = f"""
Candidate: {profile['name']}
Seniority: {profile['seniority_level']}
Experience: {profile['years_experience']} years
Fit Score: {profile['preliminary_fit_score']}/100"""
                candidates_details.append(detail)

            candidates_text = "\n".join(candidates_details)

            prompt = f"""You are a senior HR executive AI.

You are evaluating multiple candidates for the SAME role.

CANDIDATES:
{candidates_text}

JOB REQUIREMENTS:
{job_requirements if job_requirements else 'No specific requirements provided'}

For EACH candidate:
- Assess fit against the job requirements
- Identify strengths and gaps

THEN:
- Compare candidates against each other
- Identify strongest overall fit
- Identify potential risks
- Recommend hiring priorities

Rules:
- Mention each candidate by name
- No hallucinations
- Executive tone

Output must be suitable for executive decision-making."""

        try:
            response = self.llm_analyzer._call_llm(prompt, force_json=False)

            if response and response.strip():
                return response.strip()
            else:
                logger.warning("Empty response from LLM for AI assessment")
                return None

        except Exception as e:
            logger.error(f"Error generating AI assessment: {e}")
            return None
