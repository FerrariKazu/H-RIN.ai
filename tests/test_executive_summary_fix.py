"""
Tests for the Executive Summary Engine Fix

Verifies that the `force_json=False` parameter is correctly used to ensure
the Experience Summary and AI Executive Assessment sections are always populated
with plain-text summaries from the LLM.
"""

import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add the project root to the Python path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.pipeline.executive_summary import ExecutiveSummaryEngine
from backend.pipeline.llm_analyzer import LLMAnalyzer

class TestExecutiveSummaryFix(unittest.TestCase):

    def setUp(self):
        """Set up a mock LLM analyzer and the summary engine for each test."""
        # Create a mock LLMAnalyzer instance
        self.mock_llm_analyzer = MagicMock(spec=LLMAnalyzer)
        
        # This is the core of the test. We simulate the behavior of the _call_llm
        # method. When called for summaries (force_json=False), it should return
        # a simple string. Otherwise, it can return None or a JSON string.
        def mock_call_llm(prompt: str, force_json: bool = True):
            if not force_json:
                # This simulates the LLM returning a plain-text paragraph
                if "experience" in prompt.lower():
                    return "This is the generated experience summary."
                if "assessment" in prompt.lower() or "evaluating" in prompt.lower():
                    return "This is the generated AI executive assessment."
            # If force_json is True, it's for a different part of the pipeline,
            # so we don't need to return a specific value for this test.
            return "{}"

        self.mock_llm_analyzer._call_llm.side_effect = mock_call_llm
        
        # Initialize the engine with the mock analyzer
        self.engine = ExecutiveSummaryEngine(llm_analyzer=self.mock_llm_analyzer)

    def test_single_cv_populates_all_sections(self):
        """
        Verify that for a single CV, both summary sections are populated with text.
        """
        print("\nRunning test: test_single_cv_populates_all_sections")
        
        # A single candidate's parsed data
        single_candidate = [
            {
                "candidate_id": "c1", "document_id": "d1", "name": "John Doe",
                "email": "j.doe@email.com", "phone": "111-222-3333",
                "seniority_level": "Senior", "years_experience": 8,
                "preliminary_fit_score": 85
            }
        ]
        
        # Process the candidate in 'single' mode
        result = self.engine.process_candidates(single_candidate, mode="single")
        
        # 1. Check that the call was made correctly for Experience Summary
        # The first text call should be for the experience summary
        experience_call_args = self.mock_llm_analyzer._call_llm.call_args_list[0]
        self.assertEqual(experience_call_args.kwargs, {'force_json': False})
        
        # 2. Check that the call was made correctly for AI Assessment
        # The second text call should be for the AI assessment
        assessment_call_args = self.mock_llm_analyzer._call_llm.call_args_list[1]
        self.assertEqual(assessment_call_args.kwargs, {'force_json': False})
        
        # 3. Assert that the experience summary is not empty or the fallback
        self.assertIn("experience summary", result["experience_summary"])
        self.assertNotIn("Unable to generate", result["experience_summary"])
        print(f"  - Experience Summary OK: '{result['experience_summary']}'")

        # 4. Assert that the AI assessment is not empty or the fallback
        self.assertIn("AI executive assessment", result["ai_executive_assessment"])
        self.assertNotIn("Unable to generate", result["ai_executive_assessment"])
        print(f"  - AI Assessment OK: '{result['ai_executive_assessment']}'")
        
        # 5. Assert that the candidate profile is present
        self.assertEqual(len(result["candidates"]), 1)
        self.assertEqual(result["candidates"][0]["name"], "John Doe")
        print("  - Candidate Profile OK")

    def test_multiple_cvs_populates_all_sections(self):
        """
        Verify that for multiple CVs, both summary sections are populated with comparative text.
        """
        print("\nRunning test: test_multiple_cvs_populates_all_sections")

        # Multiple candidates' parsed data
        multiple_candidates = [
            {
                "candidate_id": "c1", "document_id": "d1", "name": "John Doe",
                "email": "j.doe@email.com", "phone": "111-222-3333",
                "seniority_level": "Senior", "years_experience": 8,
                "preliminary_fit_score": 85
            },
            {
                "candidate_id": "c2", "document_id": "d2", "name": "Jane Smith",
                "email": "j.smith@email.com", "phone": "444-555-6666",
                "seniority_level": "Mid", "years_experience": 5,
                "preliminary_fit_score": 75
            }
        ]
        
        # Process the candidates in 'batch' mode
        result = self.engine.process_candidates(multiple_candidates, mode="batch")
        
        # 1. Check calls were made with force_json=False
        self.mock_llm_analyzer._call_llm.assert_any_call(unittest.mock.ANY, force_json=False)
        
        # 2. Assert that the experience summary is correct
        self.assertIn("experience summary", result["experience_summary"])
        self.assertNotIn("Unable to generate", result["experience_summary"])
        print(f"  - Experience Summary OK: '{result['experience_summary']}'")

        # 3. Assert that the AI assessment is correct
        self.assertIn("AI executive assessment", result["ai_executive_assessment"])
        self.assertNotIn("Unable to generate", result["ai_executive_assessment"])
        print(f"  - AI Assessment OK: '{result['ai_executive_assessment']}'")
        
        # 4. Assert that candidate profiles are present
        self.assertEqual(len(result["candidates"]), 2)
        self.assertEqual(result["candidates"][1]["name"], "Jane Smith")
        print("  - Candidate Profiles OK")

if __name__ == '__main__':
    unittest.main()
