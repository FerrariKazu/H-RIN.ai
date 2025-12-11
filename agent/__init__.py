"""
Initializes the agent package, exporting the `build_feature_vector` function for resume text processing.
"""
from .skill_normalization import build_feature_vector

__all__ = ["build_feature_vector"]