"""
Advanced NLP Engine for Resume/CV Analysis
Uses SpaCy for NER and transformer-based section classification
"""

import spacy
import logging
import re
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

# Defer transformers import to avoid hanging on module load
# from transformers import pipeline

logger = logging.getLogger(__name__)


@dataclass
class ExtractedEntity:
    """Represents an extracted entity"""
    text: str
    entity_type: str
    confidence: float = 0.8
    section: Optional[str] = None


class NLPEngine:
    """Advanced NLP processing for resumes"""
    
    # Section patterns for classification
    SECTION_KEYWORDS = {
        'summary': ['summary', 'profile', 'objective', 'about', 'overview', 'professional summary', 'executive summary'],
        'contact': ['contact', 'email', 'phone', 'address', 'linkedin', 'github', 'website', 'social'],
        'experience': ['experience', 'employment', 'work history', 'professional experience', 'career', 'positions'],
        'education': ['education', 'academic', 'qualification', 'degree', 'university', 'college', 'school'],
        'skills': ['skills', 'competencies', 'expertise', 'technical skills', 'abilities', 'core competencies'],
        'projects': ['projects', 'portfolio', 'work samples', 'personal projects', 'notable work'],
        'certifications': ['certification', 'license', 'credential', 'accreditation', 'trained'],
        'awards': ['award', 'honor', 'achievement', 'recognition', 'accomplishment'],
        'publications': ['publication', 'paper', 'research', 'article', 'written'],
        'languages': ['language', 'linguistic', 'fluent', 'bilingual', 'multilingual'],
        'references': ['reference', 'referees']
    }
    
    # Common skill keywords (can be expanded)
    SKILL_KEYWORDS = [
        # Programming languages
        'python', 'java', 'javascript', 'typescript', 'csharp', 'c\\+\\+', 'c#', 'php', 'ruby', 'go', 'rust', 'kotlin', 'swift',
        'sql', 'r', 'scala', 'groovy', 'perl', 'haskell', 'elixir', 'clojure', 'dart',
        
        # Web frameworks
        'react', 'angular', 'vue', 'svelte', 'next\\.js', 'nextjs', 'gatsby', 'express', 'django', 'flask', 'fastapi',
        'spring', 'asp\\.net', 'aspnet', 'rails', 'laravel', 'symfony', 'node\\.js', 'nodejs',
        
        # Databases
        'postgresql', 'mysql', 'mongodb', 'cassandra', 'redis', 'elasticsearch', 'dynamodb', 'oracle', 'sqlite',
        'firestore', 'bigquery', 'snowflake', 'redshift',
        
        # Cloud & DevOps
        'aws', 'azure', 'gcp', 'google cloud', 'heroku', 'docker', 'kubernetes', 'jenkins', 'gitlab', 'github',
        'terraform', 'ansible', 'ci\\/cd', 'devops',
        
        # Data & ML
        'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy', 'spark',
        'hadoop', 'nlp', 'computer vision', 'ai', 'artificial intelligence', 'data science', 'analytics',
        
        # Other tools
        'git', 'linux', 'unix', 'bash', 'shell', 'rest', 'graphql', 'grpc', 'soap', 'xml', 'json',
        'agile', 'scrum', 'jira', 'confluence', 'slack', 'salesforce'
    ]
    
    def __init__(self):
        """Initialize NLP models"""
        self.nlp = None
        self.classifier = None
        self.logs = []
        self._nlp_loaded = False
        
        # Models will be loaded on first use (lazy loading)
        self._log("NLP Engine initialized (models load on first use)")
    
    def extract(self, text: str, known_sections: Optional[Dict] = None) -> Dict:
        """
        Extract structured information from text
        
        Args:
            text: Raw text from PDF
            known_sections: Pre-detected section boundaries (optional)
        
        Returns:
            Dict with extracted entities and structured data
        """
        self.logs = []
        
        # Lazy load Spacy model on first use
        if not self._nlp_loaded:
            self._load_nlp_model()
        
        if not text:
            return {"error": "Empty text provided"}
        
        # Basic cleaning
        text = self._clean_text(text)
        
        # Extract entities using SpaCy (with fallback if model not loaded)
        if self._nlp_loaded and self.nlp:
            entities = self._extract_entities(text)
            self._log(f"Extracted {len(entities)} entities using SpaCy NER")
        else:
            entities = {"persons": [], "organizations": [], "dates": [], "locations": []}
            self._log("⚠ SpaCy model not available, using basic extraction")
        
        # Detect sections
        sections = self._detect_sections(text, known_sections)
        self._log(f"Detected {len(sections)} sections")
        
        # Extract skills
        skills = self._extract_skills(text)
        self._log(f"Detected {len(skills)} skills")
        
        # Extract education
        education = self._extract_education(text, entities)
        self._log(f"Detected {len(education)} education entries")
        
        # Extract experience (dates and companies)
        experiences = self._extract_experience(text, entities)
        self._log(f"Detected {len(experiences)} experience entries")
        
        # Compile results
        result = {
            "entities": entities,
            "sections": sections,
            "skills": skills,
            "education": education,
            "experience": experiences,
            "logs": self.logs,
            "success": True
        }
        
        return result
    
    def _extract_entities(self, text: str) -> Dict[str, List]:
        """Extract named entities using SpaCy"""
        entities = {
            "persons": [],
            "organizations": [],
            "dates": [],
            "locations": [],
            "contact": []
        }
        
        if not self.nlp:
            return entities
        
        try:
            doc = self.nlp(text)
            
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    entities["persons"].append({
                        "text": ent.text,
                        "confidence": 0.85
                    })
                elif ent.label_ == "ORG":
                    entities["organizations"].append({
                        "text": ent.text,
                        "confidence": 0.85
                    })
                elif ent.label_ == "DATE":
                    entities["dates"].append({
                        "text": ent.text,
                        "confidence": 0.85
                    })
                elif ent.label_ == "GPE":  # Geopolitical entity
                    entities["locations"].append({
                        "text": ent.text,
                        "confidence": 0.85
                    })
            
            # Extract contact info using regex
            entities["contact"] = self._extract_contact_info(text)
            
            # Deduplicate
            for key in entities:
                if isinstance(entities[key], list) and key != "contact":
                    seen = set()
                    dedup = []
                    for item in entities[key]:
                        item_text = item.get("text", "") if isinstance(item, dict) else item
                        if item_text.lower() not in seen:
                            seen.add(item_text.lower())
                            dedup.append(item)
                    entities[key] = dedup
            
            return entities
        except Exception as e:
            self._log(f"Entity extraction failed: {e}", "ERROR")
            return entities
    
    def _extract_contact_info(self, text: str) -> Dict:
        """Extract contact information using regex"""
        contact = {
            "emails": [],
            "phones": [],
            "websites": [],
            "linkedin": [],
            "github": []
        }
        
        # Email
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        contact["emails"] = list(set(emails))
        
        # Phone (multiple formats)
        phones = re.findall(r'(?:\+?\d{1,3}[-.\s]?)?\(?(?:\d{3})\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
        contact["phones"] = list(set(phones))
        
        # LinkedIn
        linkedin = re.findall(r'linkedin\.com/in/[\w\-]+', text, re.IGNORECASE)
        contact["linkedin"] = list(set(linkedin))
        
        # GitHub
        github = re.findall(r'github\.com/[\w\-]+', text, re.IGNORECASE)
        contact["github"] = list(set(github))
        
        # Websites
        websites = re.findall(r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b', text)
        contact["websites"] = list(set(websites))
        
        return contact
    
    def _detect_sections(self, text: str, known_sections: Optional[Dict] = None) -> Dict[str, str]:
        """Detect resume sections"""
        sections = {}
        
        if known_sections:
            sections.update(known_sections)
        
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            
            # Check against keywords
            for section_name, keywords in self.SECTION_KEYWORDS.items():
                if any(kw in line_lower for kw in keywords):
                    # Check if line is a header (short, follows pattern)
                    if len(line) < 50 and (line[0].isupper() or line.isupper()):
                        if section_name not in sections:
                            # Get content until next section
                            content_lines = []
                            for j in range(i + 1, min(i + 50, len(lines))):
                                next_line = lines[j].lower().strip()
                                
                                # Stop if we hit another section
                                is_next_section = any(
                                    kw in next_line 
                                    for keywords_list in self.SECTION_KEYWORDS.values() 
                                    for kw in keywords_list
                                )
                                
                                if is_next_section and len(next_line) < 50:
                                    break
                                
                                content_lines.append(lines[j])
                            
                            sections[section_name] = '\n'.join(content_lines).strip()
        
        return sections
    
    def _extract_skills(self, text: str) -> List[Dict]:
        """Extract skills from text"""
        skills = []
        text_lower = text.lower()
        
        # Create regex pattern from keywords
        for skill in self.SKILL_KEYWORDS:
            if re.search(r'\b' + skill + r'\b', text_lower):
                skills.append({
                    "skill": skill.replace('\\', ''),
                    "confidence": 0.8,
                    "category": self._categorize_skill(skill)
                })
        
        # Remove duplicates
        seen = set()
        unique_skills = []
        for skill in skills:
            key = skill["skill"].lower()
            if key not in seen:
                seen.add(key)
                unique_skills.append(skill)
        
        return unique_skills
    
    def _categorize_skill(self, skill: str) -> str:
        """Categorize skill type"""
        categories = {
            "programming_languages": ['python', 'java', 'javascript', 'csharp', 'c\\+\\+', 'php', 'ruby', 'go', 'rust', 'sql', 'r'],
            "frameworks": ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'rails', 'node', 'express'],
            "databases": ['postgresql', 'mysql', 'mongodb', 'redis', 'dynamodb', 'oracle'],
            "cloud_devops": ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'ci'],
            "data_ml": ['machine learning', 'tensorflow', 'pytorch', 'pandas', 'spark', 'nlp'],
            "other": []
        }
        
        skill_lower = skill.lower()
        for category, keywords in categories.items():
            if any(kw in skill_lower for kw in keywords):
                return category
        
        return "other"
    
    def _extract_education(self, text: str, entities: Dict) -> List[Dict]:
        """Extract education information"""
        education = []
        
        # Degree patterns
        degree_patterns = [
            r"(?:bachelor|b\.s\.|b\.a\.|bs|ba)['\s]*(?:in|of)?\s+([a-z\s]+?)(?:\n|,|;)",
            r"(?:master|m\.s\.|m\.a\.|ms|ma)['\s]*(?:in|of)?\s+([a-z\s]+?)(?:\n|,|;)",
            r"(?:phd|ph\.d\.|doctorate)['\s]*(?:in|of)?\s+([a-z\s]+?)(?:\n|,|;)",
            r"(?:associate|a\.s\.)['\s]*(?:in|of)?\s+([a-z\s]+?)(?:\n|,|;)"
        ]
        
        text_lower = text.lower()
        
        for pattern in degree_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                degree_type = pattern.split('|')[0].replace('(?:', '').replace('[', '')
                field_of_study = match.group(1).strip() if match.lastindex else "General"
                
                education.append({
                    "degree": degree_type,
                    "field_of_study": field_of_study,
                    "school": "To be filled from context",
                    "confidence": 0.75
                })
        
        # Try to match schools from entities
        for org in entities.get("organizations", [])[:5]:
            org_text = org.get("text", "") if isinstance(org, dict) else org
            # Simple heuristic: universities often have "University", "College", "School"
            if any(word in org_text.lower() for word in ['university', 'college', 'school', 'academy', 'institute']):
                # Update last education entry if exists
                if education:
                    education[-1]["school"] = org_text
        
        return education
    
    def _extract_experience(self, text: str, entities: Dict) -> List[Dict]:
        """Extract work experience"""
        experience = []
        
        # Look for date patterns that indicate job periods
        date_pattern = r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[\w\s,]*(\d{4})'
        dates = re.finditer(date_pattern, text.lower(), re.IGNORECASE)
        
        date_list = [match.group(0) for match in dates]
        
        # Try to pair organizations with experience
        for org in entities.get("organizations", [])[:10]:
            org_text = org.get("text", "") if isinstance(org, dict) else org
            
            # Skip educational institutions
            if any(word in org_text.lower() for word in ['university', 'college', 'school']):
                continue
            
            experience.append({
                "company": org_text,
                "role": "Position not extracted",
                "dates_found": len(date_list) > 0,
                "confidence": 0.7
            })
        
        return experience
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Fix common OCR issues
        text = re.sub(r'I(\d)', r'1\1', text)  # I to 1
        text = re.sub(r'O(\d)', r'0\1', text)  # O to 0
        
        return text.strip()
    
    def _log(self, message: str, level: str = "INFO"):
        """Add to logs"""
        log_entry = f"[{level}] {message}"
        self.logs.append(log_entry)
        
        if level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
        else:
            logger.info(message)
    
    def _load_nlp_model(self):
        """Lazy load Spacy model on first use"""
        if self._nlp_loaded:
            return
        
        models_to_try = [
            "en_core_web_sm",
            "en_core_web_md",
            "en_core_web_lg"
        ]
        
        for model_name in models_to_try:
            try:
                self._log(f"Attempting to load SpaCy model: {model_name}...")
                self.nlp = spacy.load(model_name)
                self._nlp_loaded = True
                self._log(f"✓ SpaCy model '{model_name}' loaded successfully")
                return
            except OSError as e:
                self._log(f"Model '{model_name}' not available: {str(e)}")
                continue
        
        # If all models failed, provide helpful error message
        self._log(
            "⚠ No SpaCy models found. Install with one of:\n"
            "  pip install spacy && python -m spacy download en_core_web_sm\n"
            "  OR\n"
            "  conda install -c conda-forge spacy-model-en_core_web_sm",
            "WARNING"
        )
        self._nlp_loaded = False
