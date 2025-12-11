import json
import os
import sys
from typing import List, Dict, Set

# Add project root to path to import existing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent.skill_normalization import normalize_skill, map_skill_to_feature, _load_registry

class SkillMapper:
    def __init__(self):
        self.skills, self.certs, self.domains = _load_registry()

    def normalize_list(self, raw_items: List[str]) -> List[str]:
        """
        Takes a list of raw skill/certification strings and returns a list of canonical feature keys.
        Example: ["Python Programming", "AWS Cert"] -> ["feat_skill_python", "feat_cert_aws"]
        """
        if not raw_items:
            return []

        normalized_features = set()
        
        for item in raw_items:
            # Use the existing robust normalization logic
            feat = normalize_skill(item)
            if feat:
                normalized_features.add(map_skill_to_feature(feat))
                
        return sorted(list(normalized_features))

    def get_display_name(self, feature_key: str) -> str:
        """
        Converts a feature key back to a human-readable display name.
        Example: "feat_skill_python" -> "Python"
        """
        if feature_key.startswith('feat_skill_'):
            return feature_key.replace('feat_skill_', '').replace('_', ' ').title()
        elif feature_key.startswith('feat_cert_'):
            return feature_key.replace('feat_cert_', '').replace('_', ' ').title()
        elif feature_key.startswith('feat_job_'):
            return feature_key.replace('feat_job_', '').replace('_', ' ').title()
        return feature_key

# Singleton instance
skill_mapper = SkillMapper()
