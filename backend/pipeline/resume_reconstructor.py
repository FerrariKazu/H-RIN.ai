"""
Resume Reconstructor - Converts extracted data to Markdown and JSON formats
NO mock data - all output from actual extraction
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ResumeJSON:
    """Structured resume JSON format"""
    name: str = ""
    summary: str = ""
    contact: Dict = None
    skills: List[Dict] = None
    experience: List[Dict] = None
    education: List[Dict] = None
    projects: List[Dict] = None
    certifications: List[Dict] = None
    languages: List[Dict] = None
    achievements: List[Dict] = None
    
    def __post_init__(self):
        if self.contact is None:
            self.contact = {"phone": "", "email": "", "address": "", "linkedin": "", "github": ""}
        if self.skills is None:
            self.skills = []
        if self.experience is None:
            self.experience = []
        if self.education is None:
            self.education = []
        if self.projects is None:
            self.projects = []
        if self.certifications is None:
            self.certifications = []
        if self.languages is None:
            self.languages = []
        if self.achievements is None:
            self.achievements = []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "summary": self.summary,
            "contact": self.contact,
            "skills": self.skills,
            "experience": self.experience,
            "education": self.education,
            "projects": self.projects,
            "certifications": self.certifications,
            "languages": self.languages,
            "achievements": self.achievements
        }


class ResumeReconstructor:
    """Reconstruct resume in multiple formats"""
    
    def __init__(self):
        self.logs = []
    
    def reconstruct(self, 
                   raw_text: str,
                   nlp_data: Dict,
                   sections: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Reconstruct resume from extracted data
        
        Args:
            raw_text: Original raw text from PDF
            nlp_data: Extracted NLP data
            sections: Detected sections (optional)
        
        Returns:
            Dict with markdown and json versions
        """
        self.logs = []
        
        # Build structured data
        resume_json = self._build_json(raw_text, nlp_data, sections)
        
        # Generate markdown
        markdown = self._generate_markdown(resume_json, raw_text)
        
        result = {
            "markdown": markdown,
            "json": resume_json.to_dict(),
            "logs": self.logs,
            "success": True
        }
        
        self._log(f"Reconstruction complete: {len(markdown)} chars markdown, {len(resume_json.skills)} skills detected")
        
        return result
    
    def _build_json(self, 
                   raw_text: str,
                   nlp_data: Dict,
                   sections: Optional[Dict]) -> ResumeJSON:
        """Build structured JSON from extracted data"""
        resume = ResumeJSON()
        
        # Extract name from persons entities or first line
        persons = nlp_data.get("entities", {}).get("persons", [])
        if persons and len(persons) > 0:
            # Use first person entity as name
            first_person = persons[0]
            resume.name = first_person.get("text", "") if isinstance(first_person, dict) else first_person
        else:
            # Fallback: use first line of text if it looks like a name (short and no special chars)
            first_line = raw_text.split('\n')[0].strip()
            if first_line and len(first_line) < 50 and not any(char in first_line for char in ['@', 'http', ':', '=']):
                resume.name = first_line
        
        # Contact information
        contact_data = nlp_data.get("entities", {}).get("contact", {})
        resume.contact = {
            "phone": contact_data.get("phones", [""])[0] if contact_data.get("phones") else "",
            "email": contact_data.get("emails", [""])[0] if contact_data.get("emails") else "",
            "address": "",  # Not easily extracted from text
            "linkedin": contact_data.get("linkedin", [""])[0] if contact_data.get("linkedin") else "",
            "github": contact_data.get("github", [""])[0] if contact_data.get("github") else ""
        }
        
        # Skills
        skills_list = nlp_data.get("skills", [])
        resume.skills = [
            {
                "skill": s.get("skill", ""),
                "category": s.get("category", "other"),
                "proficiency": "intermediate"  # Default, could be inferred
            }
            for s in skills_list
        ]
        
        # Experience
        experience_list = nlp_data.get("experience", [])
        resume.experience = [
            {
                "company": e.get("company", ""),
                "role": e.get("role", ""),
                "start_date": "",
                "end_date": "",
                "description": "",
                "current": False
            }
            for e in experience_list[:10]  # Limit to 10
        ]
        
        # Education
        education_list = nlp_data.get("education", [])
        resume.education = [
            {
                "school": e.get("school", ""),
                "degree": e.get("degree", ""),
                "field_of_study": e.get("field_of_study", ""),
                "start_date": "",
                "end_date": "",
                "gpa": ""
            }
            for e in education_list[:5]  # Limit to 5
        ]
        
        # Summary (from section or first paragraph)
        sections_dict = sections or nlp_data.get("sections", {})
        resume.summary = sections_dict.get("summary", "")
        
        if not resume.summary:
            # Use first 300 chars of raw text as fallback
            resume.summary = raw_text[:300].replace('\n', ' ').strip()
        
        # Entities as achievements
        persons = nlp_data.get("entities", {}).get("persons", [])
        resume.achievements = [
            {"achievement": p.get("text", "") if isinstance(p, dict) else p}
            for p in persons[:5]
        ]
        
        self._log(f"Built JSON: {len(resume.skills)} skills, {len(resume.experience)} roles, {len(resume.education)} degrees")
        
        return resume
    
    def _generate_markdown(self, resume: ResumeJSON, raw_text: str) -> str:
        """Generate Markdown representation"""
        markdown = []
        
        # Title (extracted from first line or name)
        first_line = raw_text.split('\n')[0].strip()
        if first_line and len(first_line) < 100:
            markdown.append(f"# {first_line}\n")
        else:
            markdown.append("# Resume\n")
        
        # Contact
        contact_lines = []
        if resume.contact.get("email"):
            contact_lines.append(f"📧 {resume.contact['email']}")
        if resume.contact.get("phone"):
            contact_lines.append(f"📱 {resume.contact['phone']}")
        if resume.contact.get("linkedin"):
            contact_lines.append(f"🔗 [LinkedIn]({resume.contact['linkedin']})")
        if resume.contact.get("github"):
            contact_lines.append(f"🐙 [GitHub]({resume.contact['github']})")
        
        if contact_lines:
            markdown.append("## Contact\n")
            markdown.append(" | ".join(contact_lines))
            markdown.append("\n")
        
        # Summary
        if resume.summary:
            markdown.append("## Summary\n")
            markdown.append(resume.summary)
            markdown.append("\n")
        
        # Skills
        if resume.skills:
            markdown.append("## Skills\n")
            
            # Group by category
            by_category = {}
            for skill in resume.skills:
                cat = skill.get("category", "other")
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(skill.get("skill", ""))
            
            for category, skills_list in by_category.items():
                cat_name = category.replace("_", " ").title()
                markdown.append(f"### {cat_name}\n")
                markdown.append(", ".join(skills_list))
                markdown.append("\n")
        
        # Experience
        if resume.experience:
            markdown.append("## Professional Experience\n")
            
            for exp in resume.experience:
                markdown.append(f"### {exp.get('role', 'Position')} at {exp.get('company', 'Company')}\n")
                
                if exp.get("start_date") or exp.get("end_date"):
                    date_range = f"{exp.get('start_date', '')} - {exp.get('end_date', 'Present')}"
                    markdown.append(f"**{date_range}**\n")
                
                if exp.get("description"):
                    markdown.append(exp["description"])
                
                markdown.append("\n")
        
        # Education
        if resume.education:
            markdown.append("## Education\n")
            
            for edu in resume.education:
                degree = edu.get("degree", "Degree")
                field = edu.get("field_of_study", "")
                school = edu.get("school", "Institution")
                
                if field:
                    markdown.append(f"### {degree} in {field}\n")
                else:
                    markdown.append(f"### {degree}\n")
                
                markdown.append(f"**{school}**\n")
                
                if edu.get("start_date") or edu.get("end_date"):
                    date_range = f"{edu.get('start_date', '')} - {edu.get('end_date', '')}"
                    markdown.append(f"{date_range}\n")
                
                if edu.get("gpa"):
                    markdown.append(f"GPA: {edu['gpa']}\n")
                
                markdown.append("\n")
        
        # Certifications
        if resume.certifications:
            markdown.append("## Certifications\n")
            for cert in resume.certifications:
                markdown.append(f"- {cert.get('name', 'Certification')}")
                if cert.get("issuer"):
                    markdown.append(f" ({cert['issuer']})")
                markdown.append("\n")
            markdown.append("\n")
        
        # Languages
        if resume.languages:
            markdown.append("## Languages\n")
            for lang in resume.languages:
                markdown.append(f"- {lang.get('language', 'Language')}: {lang.get('proficiency', 'Proficient')}\n")
            markdown.append("\n")
        
        # Projects
        if resume.projects:
            markdown.append("## Projects\n")
            for proj in resume.projects:
                markdown.append(f"### {proj.get('name', 'Project')}\n")
                markdown.append(proj.get("description", ""))
                markdown.append("\n")
        
        return "".join(markdown)
    
    def _log(self, message: str):
        """Add to logs"""
        self.logs.append(f"[RECONSTRUCTOR] {message}")
        logger.info(message)