#!/usr/bin/env python3

import pandas as pd # Imports the pandas library for data manipulation.
import os # Imports the os module for path manipulation.
from pathlib import Path # Imports the Path class for object-oriented filesystem paths.

def generate_report_metrics(file_path: Path):
    # Reads the CSV file into a pandas DataFrame.
    df = pd.read_csv(file_path)

    # Initializes a dictionary to store various metrics.
    metrics = {
        "Resumes processed": int(len(df)), # Total number of resumes processed.
        # Distribution of 'Recruiter_Decision' labels.
        "Recruiter_Decision distribution": {str(k): int(v) for k, v in df["Recruiter_Decision"].value_counts().to_dict().items()},
        # Statistics for 'feat_num_skills_matched'.
        "feat_num_skills_matched": {
            "mean": float(df["feat_num_skills_matched"].mean()),
            "std": float(df["feat_num_skills_matched"].std()),
            "min": int(df["feat_num_skills_matched"].min()),
            "max": int(df["feat_num_skills_matched"].max()),
        },
        # Statistics for 'feat_years_experience_extracted'.
        "feat_years_experience_extracted": {
            "mean": float(df["feat_years_experience_extracted"].mean()),
            "std": float(df["feat_years_experience_extracted"].std()),
            "min": int(df["feat_years_experience_extracted"].min()),
            "max": int(df["feat_years_experience_extracted"].max()),
        },
        # Statistics for 'feat_text_len_chars'.
        "feat_text_len_chars": {
            "mean": float(df["feat_text_len_chars"].mean()),
            "std": float(df["feat_text_len_chars"].std()),
            "min": int(df["feat_text_len_chars"].min()),
            "max": int(df["feat_text_len_chars"].max()),
        },
        # Statistics for 'feat_text_len_words'.
        "feat_text_len_words": {
            "mean": float(df["feat_text_len_words"].mean()),
            "std": float(df["feat_text_len_words"].std()),
            "min": int(df["feat_text_len_words"].min()),
            "max": int(df["feat_text_len_words"].max()),
        },
        # Statistics for 'Experience (Years)'.
        "Experience (Years)": {
            "mean": float(df["Experience (Years)"].mean()),
            "std": float(df["Experience (Years)"].std()),
            "min": int(df["Experience (Years)"].min()),
            "max": int(df["Experience (Years)"].max()),
        },
        # Statistics for 'Salary Expectation ($)'.
        "Salary Expectation ($)": {
            "mean": float(df["Salary Expectation ($)"].mean()),
            "std": float(df["Salary Expectation ($)"].std()),
            "min": int(df["Salary Expectation ($)"].min()),
            "max": int(df["Salary Expectation ($)"].max()),
        },
        # Statistics for 'Projects Count'.
        "Projects Count": {
            "mean": float(df["Projects Count"].mean()),
            "std": float(df["Projects Count"].std()),
            "min": int(df["Projects Count"].min()),
            "max": int(df["Projects Count"].max()),
        },
        # Statistics for 'AI Score (0-100)'.
        "AI Score (0-100)": {
            "mean": float(df["AI Score (0-100)"].mean()),
            "std": float(df["AI Score (0-100)"].std()),
            "min": int(df["AI Score (0-100)"].min()),
            "max": int(df["AI Score (0-100)"].max()),
        },
    }

    # Identifies columns related to job domains.
    domain_cols = [c for c in df.columns if c.startswith("feat_job_")]
    # Calculates the sum for each job domain column.
    domain_counts = {col: int(df[col].sum()) for col in domain_cols}
    # Adds job domain counts to the metrics dictionary.
    metrics["Job domains"] = domain_counts

    return metrics # Returns the dictionary of computed metrics.

if __name__ == "__main__":
    # Defines the input file path.
    input_file = Path(os.path.join("data", "normalized_dataset_v3.csv"))
    # Checks if the input file exists.
    if not input_file.exists():
        # Prints an error message if the file is not found.
        print(f"Error: Input file not found at {input_file}")
    else:
        # Generates report metrics if the file exists.
        report_metrics = generate_report_metrics(input_file)
        import json # Imports the json module for pretty printing.
        # Prints the metrics in a human-readable JSON format.
        print(json.dumps(report_metrics, indent=4))