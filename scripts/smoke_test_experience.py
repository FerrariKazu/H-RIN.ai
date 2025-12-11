from datetime import datetime  # Import datetime for current year calculations
import sys  # Import sys module for system-specific parameters and functions
from pathlib import Path  # Import Path from pathlib for object-oriented filesystem paths

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent.parent  # Define the root directory of the project
if str(ROOT) not in sys.path:  # Check if the root directory is not in sys.path
    sys.path.insert(0, str(ROOT))  # Add the root directory to sys.path

from agent.skill_normalization import extract_numeric_features  # Import function to extract numeric features
from scripts.engineer_resume_features import parse_years_experience  # Import function to parse years of experience


def main():  # Main function to run smoke tests for experience extraction
    now = datetime.now()  # Get the current datetime
    cases = [  # Define test cases for parse_years_experience
        ("5 years of experience", 5.0),  # Test case 1
        ("7.5 yrs in data science", 7.5),  # Test case 2
        ("10+ years in engineering", 10.0),  # Test case 3
        ("three years experience", 3.0),  # Test case 4
        ("Five yrs in analytics", 5.0),  # Test case 5
    ]

    for txt, expected in cases:  # Iterate through test cases
        got = parse_years_experience(txt)  # Parse years of experience from text
        assert abs(got - expected) < 1e-6, f"parse_years_experience failed: {txt} -> {got}"  # Assert equality with a tolerance

    # Since-year checks (bounds)
    yrs = parse_years_experience("Experience since 2018")  # Parse years of experience from a "since year" phrase
    assert yrs >= (now.year - 2018) - 0.01  # Assert lower bound for years of experience
    assert yrs <= (now.year - 2018) + 0.99  # Assert upper bound for years of experience

    # Agent extractor check
    txt = "Senior Data Scientist with 7 years of experience."  # Sample text for agent extractor
    fv = extract_numeric_features(txt)  # Extract numeric features from text
    assert abs(fv['feat_years_experience_extracted'] - 7.0) < 1e-6  # Assert extracted years of experience

    print("Smoke tests passed for experience extraction.")  # Print success message


if __name__ == "__main__":  # Standard boilerplate to run main function when script is executed
    main()  # Call the main function