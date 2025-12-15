"""
Job Requirements Parser and Validator
Enforces strict job requirements handling across the pipeline
"""

import hashlib
import json
import re
from typing import Dict, Any, Optional, List


class JobRequirementsParser:
    """
    Parse and validate job requirements
    Extracts structured information and generates verification hash
    """
    
    @staticmethod
    def parse(raw_text: Optional[str]) -> Dict[str, Any]:
        """
        Parse raw job requirements text into structured format
        
        Args:
            raw_text: Raw job requirements text (optional)
        
        Returns:
            Dict with parsed components and metadata
        """
        if not raw_text or not raw_text.strip():
            return {
                "raw_text": "",
                "is_provided": False,
                "hash": "",
                "target_role": None,
                "required_skills": [],
                "optional_skills": [],
                "seniority": None,
                "domain": None,
                "word_count": 0
            }
        
        raw_text = raw_text.strip()
        
        # Generate SHA256 hash for verification
        text_hash = hashlib.sha256(raw_text.encode()).hexdigest()
        
        # Extract role (often first meaningful words or look for patterns)
        target_role = JobRequirementsParser._extract_role(raw_text)
        
        # Extract required skills
        required_skills = JobRequirementsParser._extract_skills(raw_text, required=True)
        
        # Extract optional skills
        optional_skills = JobRequirementsParser._extract_skills(raw_text, required=False)
        
        # Detect seniority level
        seniority = JobRequirementsParser._extract_seniority(raw_text)
        
        # Detect domain/industry
        domain = JobRequirementsParser._extract_domain(raw_text)
        
        # Count words
        word_count = len(raw_text.split())
        
        return {
            "raw_text": raw_text,
            "is_provided": True,
            "hash": text_hash,
            "target_role": target_role,
            "required_skills": required_skills,
            "optional_skills": optional_skills,
            "seniority": seniority,
            "domain": domain,
            "word_count": word_count
        }
    
    @staticmethod
    def _extract_role(text: str) -> Optional[str]:
        """Extract target role from text"""
        # Look for job title patterns
        title_patterns = [
            r"(?:role|position|title|for|hire|seeking):\s*(.+?)(?:\n|$|,|-)",
            r"^(.+?)\s*(?:role|position|job|title)\s*[-–:]*\s*(.+?)$",
            r"^(.*?\s+(?:Engineer|Developer|Manager|Analyst|Specialist|Designer|Architect|Lead|Senior|Junior|Mid-level)).*$"
        ]
        
        lines = text.split('\n')
        first_line = lines[0] if lines else ""
        
        # If first line looks like a title, return it
        if len(first_line) < 100 and any(keyword in first_line.lower() for keyword in 
                                          ['engineer', 'developer', 'manager', 'analyst', 'specialist', 'designer', 'architect']):
            return first_line.strip()
        
        for pattern in title_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                role = match.group(1) if match.groups() else match.group(0)
                return role.strip()[:100]
        
        return None
    
    @staticmethod
    def _extract_skills(text: str, required: bool = True) -> List[str]:
        """Extract skills from text"""
        skills = []
        
        # Pattern variations for skill lists
        section_keywords = {
            True: ['must|required|must have|requirements|necessary', 'skills|competencies|expertise'],
            False: ['nice to have|optional|preferred|bonus|beneficial', 'skills|competencies|expertise']
        }
        
        # Find section with skills
        if required:
            patterns = [
                r"(?:must\s+(?:have|know)|required|requirements):\s*(.+?)(?:\n\n|$)",
                r"(?:required|must have):\s*(.+?)(?:\n(?:optional|nice|preferred)|$)"
            ]
        else:
            patterns = [
                r"(?:nice to have|optional|preferred|bonus):\s*(.+?)(?:\n|$)"
            ]
        
        skill_section = ""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                skill_section = match.group(1)
                break
        
        if not skill_section:
            # Fall back to looking for common skill indicators
            skill_section = text
        
        # Extract individual skills (split by comma, newline, bullet points)
        skill_lines = re.split(r'[,\n•\-]', skill_section)
        
        for line in skill_lines:
            line = line.strip()
            # Remove numbers, bullets, and clean up
            line = re.sub(r'^[\d+\.\)•\-\*]\s*', '', line).strip()
            
            if len(line) > 2 and len(line) < 100 and line not in skills:
                # Filter out non-skill text
                if not any(phrase in line.lower() for phrase in ['experience', 'knowledge', 'understanding', 'ability']):
                    skills.append(line)
        
        return skills[:15]  # Limit to 15 skills
    
    @staticmethod
    def _extract_seniority(text: str) -> Optional[str]:
        """Detect seniority level from text"""
        text_lower = text.lower()
        
        seniority_map = {
            'executive': ['cxo', 'vp', 'executive', 'director level', 'c-level'],
            'lead': ['lead', 'tech lead', 'team lead', 'principal'],
            'senior': ['senior', '5+', '7+', '10+', 'years of experience'],
            'mid': ['mid-level', 'mid level', '3-5', '3+ year', 'intermediate'],
            'junior': ['junior', 'entry-level', 'entry level', 'graduate', '0-2', '1-2']
        }
        
        for level, keywords in seniority_map.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return level
        
        return None
    
    @staticmethod
    def _extract_domain(text: str) -> Optional[str]:
        """Detect domain/industry from text"""
        text_lower = text.lower()
        
        domain_map = {
            'backend': ['backend', 'rest', 'api', 'server', 'database', 'microservice'],
            'frontend': ['frontend', 'ui', 'ux', 'react', 'vue', 'angular', 'javascript'],
            'fullstack': ['full stack', 'fullstack', 'full-stack'],
            'mobile': ['mobile', 'ios', 'android', 'react native'],
            'devops': ['devops', 'docker', 'kubernetes', 'ci/cd', 'infrastructure'],
            'data': ['data', 'machine learning', 'ml', 'python', 'sql', 'analytics'],
            'cloud': ['aws', 'azure', 'gcp', 'cloud', 'serverless'],
            'security': ['security', 'infosec', 'encryption', 'compliance']
        }
        
        for domain, keywords in domain_map.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return domain
        
        return None
    
    @staticmethod
    def validate_hash(raw_text: str, provided_hash: str) -> bool:
        """
        Validate that raw text matches the provided hash
        
        Args:
            raw_text: The raw text to validate
            provided_hash: The hash to verify against
        
        Returns:
            True if hash matches
        """
        computed_hash = hashlib.sha256(raw_text.encode()).hexdigest()
        return computed_hash == provided_hash
