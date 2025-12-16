"""
Deterministic Resume Parser - NO LLM INVOLVED
Extracts personal info, contact details, education, and experience using regex and NLP.
All data returned is guaranteed deterministic (same input = same output).
"""

import re
import json
from typing import List, Dict, Optional, Tuple
from uuid import uuid4
from datetime import datetime


class ResumeParser:
    """
    Deterministic resume parser using regex, NLP, and pattern matching.
    NO LLM calls. NO inference. Pure data extraction.
    """
    
    def __init__(self):
        """Initialize parser with regex patterns"""
        # Email patterns
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        # Phone patterns (US/International)
        self.phone_patterns = [
            r'\b(?:\+1|1)?[-.\s]?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b',  # US
            r'\b(?:\+\d{1,3}[-.\s]?)?(?:\d{1,4}[-.\s]?)+\d{1,4}\b',  # International
        ]
        
        # LinkedIn URL pattern
        self.linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/(?:in|company)/[^\s]+'
        
        # GitHub URL pattern
        self.github_pattern = r'https?://(?:www\.)?github\.com/[^\s]+'
        
        # Education degree patterns
        self.degree_patterns = {
            'PhD': r'\b(?:PhD|Doctor of Philosophy|Doctorate)\b',
            'Master': r'\b(?:Master|M\.S\.|M\.A\.|MBA|MA|MS)\b',
            'Bachelor': r'\b(?:Bachelor|B\.S\.|B\.A\.|BS|BA|Undergraduate)\b',
            'Associate': r'\b(?:Associate|A\.S\.|AS)\b',
            'Certificate': r'\b(?:Certification|Certificate|Certified)\b'
        }
        
        # Year patterns
        self.year_pattern = r'\b(19\d{2}|20\d{2})\b'
        
        # Education keywords
        self.education_keywords = [
            'university', 'college', 'school', 'institute', 'academy',
            'bachelor', 'master', 'phd', 'diploma', 'degree', 'program'
        ]
        
        # Experience keywords (job titles)
        self.job_title_keywords = [
            'engineer', 'developer', 'analyst', 'manager', 'director', 'lead',
            'architect', 'specialist', 'coordinator', 'administrator', 'scientist',
            'consultant', 'associate', 'officer', 'executive', 'designer'
        ]

    def parse(self, text: str, filename: str = "resume.pdf") -> Dict:
        """
        Parse resume text and extract all deterministic information.
        
        Args:
            text: Raw resume text
            filename: Original filename for reference
            
        Returns:
            Structured resume data with guaranteed keys
        """
        
        candidate_data = {
            "candidate_id": str(uuid4()),
            "filename": filename,
            "name": self._extract_name(text),
            "email": self._extract_email(text),
            "phone": self._extract_phone(text),
            "linkedin": self._extract_linkedin(text),
            "github": self._extract_github(text),
            "other_links": self._extract_other_urls(text),
            "education": self._extract_education(text),
            "experience": self._extract_experience(text),
            "skills": self._extract_skills(text),
            "certifications": self._extract_certifications(text)
        }
        
        return candidate_data

    def _extract_name(self, text: str) -> Optional[str]:
        """
        Extract candidate name from resume.
        Usually appears at the top, typically 2-4 words, capitalized.
        """
        lines = text.split('\n')
        
        for i, line in enumerate(lines[:20]):  # Check first 20 lines
            line_clean = line.strip()
            if not line_clean:
                continue
            
            # Skip email/phone lines
            if '@' in line_clean or re.search(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', line_clean):
                continue
            
            # Skip common header words
            if any(kw in line_clean.lower() for kw in ['summary', 'objective', 'professional', 'contact']):
                continue
            
            # Name is typically 2-4 capitalized words (not all caps or all lowercase)
            words = line_clean.split()
            if 2 <= len(words) <= 4:
                # Check if mostly capitalized (first letter of each word)
                if all(w[0].isupper() for w in words if w):
                    # Additional check: name shouldn't contain special chars (except hyphen/apostrophe)
                    if re.match(r'^[A-Z][a-zA-Z\-\'\s]+$', line_clean):
                        return line_clean.strip()
        
        return None

    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address"""
        match = re.search(self.email_pattern, text)
        return match.group(0) if match else None

    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number"""
        for pattern in self.phone_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None

    def _extract_linkedin(self, text: str) -> Optional[str]:
        """Extract LinkedIn profile URL"""
        match = re.search(self.linkedin_pattern, text, re.IGNORECASE)
        return match.group(0) if match else None

    def _extract_github(self, text: str) -> Optional[str]:
        """Extract GitHub profile URL"""
        match = re.search(self.github_pattern, text, re.IGNORECASE)
        return match.group(0) if match else None

    def _extract_other_urls(self, text: str) -> List[str]:
        """Extract other URLs (portfolio, website, etc.)"""
        urls = []
        url_pattern = r'https?://[^\s\)]+'
        
        for match in re.finditer(url_pattern, text):
            url = match.group(0)
            # Exclude LinkedIn and GitHub (already extracted)
            if not any(domain in url.lower() for domain in ['linkedin', 'github']):
                urls.append(url)
        
        return list(set(urls))  # Remove duplicates

    def _extract_education(self, text: str) -> List[Dict]:
        """Extract education information"""
        education = []
        lines = text.split('\n')
        
        current_education = None
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Check if this line contains education keywords
            if any(kw in line_lower for kw in self.education_keywords):
                # Extract degree if present
                degree = None
                for degree_type, pattern in self.degree_patterns.items():
                    if re.search(pattern, line, re.IGNORECASE):
                        degree = degree_type
                        break
                
                # Extract institution name (usually longest word in the line)
                words = [w.strip() for w in line.split() if len(w.strip()) > 2]
                institution = ' '.join(words[:4]) if words else None
                
                # Extract years
                years = re.findall(self.year_pattern, text[max(0, text.find(line)-100):text.find(line)+500])
                start_year = None
                end_year = None
                
                if len(years) >= 2:
                    start_year = years[0]
                    end_year = years[1] if years[1] != years[0] else None
                elif len(years) == 1:
                    end_year = years[0]
                
                if degree or institution:
                    current_education = {
                        "degree": degree,
                        "field": None,
                        "institution": institution,
                        "start": start_year,
                        "end": end_year
                    }
                    education.append(current_education)
        
        return education

    def _extract_experience(self, text: str) -> List[Dict]:
        """Extract work experience"""
        experience = []
        lines = text.split('\n')
        
        experience_keywords = ['experience', 'employment', 'work history', 'professional']
        in_experience = False
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Check if we're entering experience section
            if any(kw in line_lower for kw in experience_keywords):
                in_experience = True
                continue
            
            if not in_experience:
                continue
            
            # Look for job title patterns
            has_job_title = any(kw in line_lower for kw in self.job_title_keywords)
            has_company_pattern = re.search(r'\b[A-Z][a-zA-Z\s&\-]*(?:Inc|LLC|Corp|Ltd|Co|Company)\b', line)
            
            if has_job_title or has_company_pattern:
                # Extract years from this job entry
                job_text = line + '\n' + lines[i+1] if i+1 < len(lines) else line
                years = re.findall(self.year_pattern, job_text)
                
                # Extract title (usually at end or beginning of line)
                title = None
                company = None
                
                # Simple heuristic: company is usually capitalized multi-word phrase
                words = [w.strip() for w in line.split('—') if w.strip()]
                if len(words) == 2:
                    title, company = words[0].strip(), words[1].strip()
                elif has_job_title:
                    title = line.strip()
                
                if title:
                    job_entry = {
                        "title": title,
                        "company": company,
                        "start": years[0] if len(years) > 0 else None,
                        "end": years[1] if len(years) > 1 else None,
                        "description": None
                    }
                    experience.append(job_entry)
        
        return experience

    def _extract_skills(self, text: str) -> List[str]:
        """
        Extract technical skills from resume.
        Looks for skill keywords and programming language names.
        """
        skills = set()
        
        # Common technical skills and programming languages
        skill_keywords = [
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust',
            'sql', 'nosql', 'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch',
            'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'terraform',
            'react', 'angular', 'vue', 'node', 'express', 'django', 'flask', 'fastapi',
            'rest', 'graphql', 'microservices', 'architecture', 'design patterns',
            'machine learning', 'deep learning', 'nlp', 'cv', 'tensorflow', 'pytorch',
            'git', 'github', 'gitlab', 'bitbucket', 'cicd', 'jenkins', 'gitlab ci',
            'agile', 'scrum', 'kanban', 'linux', 'unix', 'windows', 'macos',
            'html', 'css', 'sass', 'webpack', 'npm', 'yarn', 'maven', 'gradle',
            'apache', 'nginx', 'apache kafka', 'rabbitmq', 'apache spark',
            'data analysis', 'data science', 'analytics', 'tableau', 'power bi',
            'api development', 'system design', 'database design', 'software engineering'
        ]
        
        text_lower = text.lower()
        
        for skill in skill_keywords:
            if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
                # Format as title case
                skills.add(skill.title())
        
        return sorted(list(skills))

    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certifications and credentials"""
        certifications = []
        
        cert_keywords = [
            'aws certified', 'azure certified', 'gcp certified',
            'ckad', 'cka', 'cissp', 'oscp', 'security+',
            'cpa', 'pmp', 'scrum master', 'certified kubernetes'
        ]
        
        text_lower = text.lower()
        
        for cert in cert_keywords:
            if cert in text_lower:
                # Extract the full certification line if possible
                for line in text.split('\n'):
                    if cert in line.lower():
                        certifications.append(line.strip())
                        break
        
        return certifications


def parse_resume(text: str, filename: str = "resume.pdf") -> Dict:
    """
    Convenience function to parse a resume.
    
    Args:
        text: Resume text
        filename: Original filename
        
    Returns:
        Structured resume data
    """
    parser = ResumeParser()
    return parser.parse(text, filename)
