import spacy
from transformers import pipeline
import logging

logger = logging.getLogger(__name__)

class NLPEngine:
    def __init__(self):
        # Spacy for fast NER
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            logger.warning("Spacy model 'en_core_web_sm' not found. Download it via: python -m spacy download en_core_web_sm")
            self.nlp = None

        # Zero-shot classification for section identification (optional, heavier)
        # self.classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

    def extract(self, text):
        entities = {
            "persons": [],
            "orgs": [],
            "dates": [],
            "skills_detected": [] # To be filled by heuristic or skills DB
        }

        if not self.nlp:
            return {"entities": entities, "error": "Spacy model missing"}

        doc = self.nlp(text)
        
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                entities["persons"].append(ent.text)
            elif ent.label_ == "ORG":
                entities["orgs"].append(ent.text)
            elif ent.label_ == "DATE":
                entities["dates"].append(ent.text)

        # Basic Skill Heuristics (Regex/List based could go here)
        # For now, just a placeholder list
        common_skills = ["Python", "Java", "SQL", "React", "AWS", "Docker", "Machine Learning"]
        for token in doc:
            if token.text in common_skills:
                entities["skills_detected"].append(token.text)
        
        # Deduplicate
        entities["skills_detected"] = list(set(entities["skills_detected"]))
        entities["persons"] = list(set(entities["persons"]))
        entities["orgs"] = list(set(entities["orgs"]))

        return {"entities": entities}
