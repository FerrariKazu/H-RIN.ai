import spacy
import re
import dateparser
import logging
from typing import Dict, List, Any
from spacy.matcher import PhraseMatcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EntityExtractor:
    def __init__(self, model_name: str = "en_core_web_md"):
        """
        Initializes the EntityExtractor with a spaCy model.
        """
        logger.info(f"Loading spaCy model: {model_name}")
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            logger.warning(f"Model '{model_name}' not found. Downloading...")
            from spacy.cli import download
            download(model_name)
            self.nlp = spacy.load(model_name)
            
        self.matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        self._load_skills()

    def _load_skills(self):
        """
        Loads skill keywords into the PhraseMatcher.
        In a real app, this would load from a CSV or DB.
        """
        # Basic seed list - expand this or load from file
        skill_list = [
            "Python", "Java", "C++", "JavaScript", "React", "Node.js", "SQL", "NoSQL",
            "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Machine Learning", "Deep Learning",
            "NLP", "Data Analysis", "Project Management", "Agile", "Scrum", "Communication",
            "Leadership", "Git", "Linux", "TensorFlow", "PyTorch", "Pandas", "NumPy",
            "FastAPI", "Flask", "Django", "HTML", "CSS", "Tailwind"
        ]
        patterns = [self.nlp.make_doc(text) for text in skill_list]
        self.matcher.add("SKILL", patterns)

    def extract_contact_info(self, text: str) -> Dict[str, str]:
        """
        Extracts email, phone, and LinkedIn using Regex.
        """
        contact = {}
        
        # Email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            contact["email"] = email_match.group(0)
            
        # Phone (Simple regex, can be improved)
        # Matches: (123) 456-7890, 123-456-7890, +1 123 456 7890
        phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            contact["phone"] = phone_match.group(0)
            
        # LinkedIn
        linkedin_pattern = r'linkedin\.com/in/[a-zA-Z0-9-]+'
        linkedin_match = re.search(linkedin_pattern, text)
        if linkedin_match:
            contact["linkedin"] = linkedin_match.group(0)
            
        return contact

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Main method to extract all entities from text.
        """
        doc = self.nlp(text)
        
        # 1. NER (Persons, Orgs, GPEs)
        ner_entities = {
            "PERSON": [],
            "ORG": [],
            "GPE": [],
            "DATE": []
        }
        
        for ent in doc.ents:
            if ent.label_ in ner_entities:
                ner_entities[ent.label_].append(ent.text)
                
        # Deduplicate
        for key in ner_entities:
            ner_entities[key] = list(set(ner_entities[key]))
            
        # 2. Skills (PhraseMatcher)
        skills = []
        matches = self.matcher(doc)
        for match_id, start, end in matches:
            span = doc[start:end]
            skills.append(span.text)
        
        # 3. Contact Info
        contact_info = self.extract_contact_info(text)
        
        # 4. Name Heuristic (if not found in contact)
        # Usually the first PERSON entity is the candidate name
        name = ner_entities["PERSON"][0] if ner_entities["PERSON"] else None
        
        return {
            "name": name,
            "contact_info": contact_info,
            "skills_detected": list(set(skills)),
            "ner_entities": ner_entities
        }

    def extract_experience_entries(self, text: str) -> List[Dict]:
        """
        Attempts to parse work experience entries.
        This is hard with just NLP; usually relies on LLM for structure.
        We will extract dates and ORGs here as hints.
        """
        # Placeholder for complex logic
        # In this pipeline, we rely on LLM for the final structuring of this list.
        # But we can pass extracted dates/orgs to help it.
        return []

# Singleton instance
entity_extractor = EntityExtractor()
