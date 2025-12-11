import pandas as pd
import numpy as np
import re
from typing import Dict, Any, List
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent.skill_normalization import build_feature_vector

def extract_salary(text: str) -> float:
    """Simple heuristic to extract salary expectation."""
    # Look for patterns like $100k, 100,000, etc.
    # This is a simplified version.
    matches = re.findall(r'\$(\d{2,3})k', text.lower())
    if matches:
        return float(matches[0]) * 1000
    
    matches = re.findall(r'\$(\d{1,3}(?:,\d{3})*)', text)
    if matches:
        try:
            val = float(matches[0].replace(',', ''))
            if val > 10000: # Filter out small numbers
                return val
        except:
            pass
            
    return 0.0

def build_features(text: str, structured_data: Dict[str, Any], config_features: List[str]) -> pd.DataFrame:
    """
    Constructs a DataFrame with the exact features expected by the model.
    
    Args:
        text: Raw resume text.
        structured_data: JSON output from LLM.
        config_features: List of feature names expected by the model.
        
    Returns:
        pd.DataFrame: Single-row DataFrame with all features.
    """
    # 1. Get base features from skill_normalization (feat_*)
    base_features = build_feature_vector(text)
    
    # 2. Augment with LLM-derived data
    # Projects Count
    projects = structured_data.get('projects', [])
    base_features['Projects Count'] = len(projects) if isinstance(projects, list) else 0
    
    # Experience (Years) - prefer LLM structured data if available and numeric
    # Otherwise fallback to regex extracted
    exp_years = 0.0
    if 'experience' in structured_data and isinstance(structured_data['experience'], list):
        # Sum up years from experience entries if possible, or just count entries?
        # The prompt asks for "years" in experience objects.
        total_years = 0.0
        for job in structured_data['experience']:
            y = job.get('years')
            if isinstance(y, (int, float)):
                total_years += y
            elif isinstance(y, str):
                # Try to parse "2019-2021" or "2 years"
                # Simple fallback
                if 'present' in y.lower() or 'current' in y.lower():
                    total_years += 1 # Assumption
                pass
        if total_years > 0:
            exp_years = total_years
    
    if exp_years == 0:
        exp_years = base_features.get('feat_years_experience_extracted', 0)
        
    base_features['Experience (Years)'] = exp_years
    
    # Salary
    base_features['Salary Expectation ($)'] = extract_salary(text)
    
    # Missing features handling
    # Some features in config might not be in base_features (e.g. feat_num_promotions)
    # We initialize them to 0
    final_features = {}
    for feature in config_features:
        if feature in base_features:
            final_features[feature] = base_features[feature]
        else:
            final_features[feature] = 0.0
            
    # Create DataFrame
    df = pd.DataFrame([final_features])
    
    # Ensure column order matches config
    df = df[config_features]
    
    return df
