import re
import logging
from typing import Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def preprocess_text(text: str) -> str:
    """
    Cleans and normalizes raw text from PDF extraction.
    
    Args:
        text (str): Raw text input.
        
    Returns:
        str: Cleaned text.
    """
    if not text:
        return ""
        
    # Normalize unicode characters (e.g., non-breaking spaces)
    text = text.replace('\xa0', ' ')
    
    # Replace multiple newlines/spaces with single space (optional, but good for some NLP)
    # For resumes, we might want to keep some structure, but let's clean excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove non-printable characters
    text = ''.join(char for char in text if char.isprintable())
    
    return text

def segment_sections(text: str) -> Dict[str, str]:
    """
    Segments the resume text into standard sections based on headers.
    
    Args:
        text (str): The full resume text.
        
    Returns:
        Dict[str, str]: Dictionary mapping section names to their content.
    """
    # Common section headers
    headers = {
        "experience": ["experience", "work history", "employment", "professional experience"],
        "education": ["education", "academic background", "qualifications"],
        "skills": ["skills", "technical skills", "core competencies", "technologies"],
        "projects": ["projects", "key projects"],
        "certifications": ["certifications", "licenses", "courses"],
        "awards": ["awards", "honors"],
        "summary": ["summary", "profile", "objective", "about me"]
    }
    
    # Create a regex pattern to find headers
    # We look for lines that are short and contain these keywords, possibly surrounded by special chars
    # This is a heuristic approach.
    
    # In a real-world scenario with raw text that has lost formatting, identifying headers is tricky.
    # We'll assume the text passed here might still have some newlines if we didn't strip them all in preprocess_text.
    # If preprocess_text strips all newlines, segmentation becomes very hard. 
    # Let's adjust preprocess_text to KEEP newlines for segmentation, or assume input to this function is roughly the raw text.
    
    # For this implementation, let's assume 'text' passed here is the CLEANED version but ideally with some structure preserved.
    # However, the current preprocess_text flattens everything. 
    # Let's modify the approach: The caller should pass raw-ish text to segment_sections, 
    # or preprocess_text should be less aggressive.
    
    # Let's assume we work with the flattened text for now and look for keywords that likely start sections.
    # A better approach for flattened text is finding the indices of the keywords.
    
    text_lower = text.lower()
    section_indices = {}
    
    for section, keywords in headers.items():
        for kw in keywords:
            # We look for the keyword as a distinct word or phrase
            # Using simple find for now, but regex with word boundaries is better
            # pattern = r'\b' + re.escape(kw) + r'\b'
            # match = re.search(pattern, text_lower)
            
            # Simplified: just find the substring
            idx = text_lower.find(kw)
            if idx != -1:
                # Store the earliest occurrence of any keyword for this section
                if section not in section_indices or idx < section_indices[section]:
                    section_indices[section] = idx
                    
    # Sort sections by position
    sorted_sections = sorted(section_indices.items(), key=lambda x: x[1])
    
    segments = {}
    
    # If no sections found, return everything as "summary" or "uncategorized"
    if not sorted_sections:
        return {"uncategorized": text}
        
    # Capture content between sections
    for i in range(len(sorted_sections)):
        section_name, start_idx = sorted_sections[i]
        
        # End index is the start of the next section, or end of string
        if i < len(sorted_sections) - 1:
            end_idx = sorted_sections[i+1][1]
        else:
            end_idx = len(text)
            
        # Extract content (excluding the header itself roughly)
        # We add len(section_name) to start_idx as a rough heuristic, 
        # but since we matched a specific keyword, we should probably add len(matched_keyword).
        # For simplicity, we just take from start_idx.
        content = text[start_idx:end_idx].strip()
        segments[section_name] = content
        
    # Also capture text BEFORE the first section (usually Contact Info / Header)
    first_section_start = sorted_sections[0][1]
    if first_section_start > 0:
        segments["contact_info"] = text[:first_section_start].strip()
        
    return segments
