# Import the argparse module for parsing command-line arguments.
import argparse
# Import the Path class from the pathlib module for working with file paths.
from pathlib import Path
import os

# Import the pandas library for data manipulation and analysis.
import pandas as pd


# Define a multi-line string template for the feature extraction updates summary in Markdown format.
SUMMARY_TEMPLATE = """
# Feature Extraction Updates

## Issues Found
- Years-of-experience extraction was too coarse (integer-only, missed forms like "5+ years", spelled numbers, and "since YEAR").
- Numeric features showed clipping (e.g., decimals ignored) and limited variance in counts for numbers/bullets.
- Certification and skill flags had narrow vocabularies; AWS bias present.
- Recruiter decision label definition needed confirmation across aliases.

## Fixes Applied
- Implemented robust years-of-experience parsing (numeric + spelled-out + date-based) with decimals.
- Counted numeric tokens including decimals and thousands separators; refined bullet detection.
- Expanded skill/cert vocabularies with non-overlapping aliases; enforced strict certification mapping.
- Confirmed recruiter decision mapping: strings {{hire, accept, advance, yes, move forward}} → 1; {{reject, decline, no}} → 0.

## Features Dropped or Renamed
- None dropped in the normalized dataset; near-constant features are flagged in the numeric audit for review.
- Column rename previously confirmed: `Recruiter Decision` → `Recruiter_Decision` (values preserved).

## Class Distribution (Post-Fix)
- AI_High_Performer: pos={ai_pos} ({ai_pos_pct:.1f}%), neg={ai_neg} ({ai_neg_pct:.1f}%)
- Recruiter_Decision: pos={rec_pos}, neg={rec_neg}

## Notes
- Plots regenerated and overwritten under `plots/normalized/`.
- Numeric features audit saved to `reports/audits/numeric_features_audit.txt`.
"""


def main():
    # Create an ArgumentParser object for command-line argument parsing.
    ap = argparse.ArgumentParser()
    # Add an argument for the input normalized CSV file path, with a default value.
    ap.add_argument("--input", default=str(Path(os.path.join("data", "normalized_dataset_v2.csv"))), help="Path to normalized CSV")
    # Add an argument for the output Markdown file path, with a default value.
    ap.add_argument("--out", default=str(Path(os.path.join("reports", "feature_extraction_updates.md"))), help="Output markdown path")
    # Parse the command-line arguments.
    args = ap.parse_args()

    # Read the normalized dataset from the specified input CSV file into a pandas DataFrame.
    df = pd.read_csv(args.input)
    # Initialize variables for class distribution calculation.
    ai_col = None
    # Iterate through DataFrame columns to find the 'ai_high_performer' column (case-insensitive).
    for c in df.columns:
        if c.lower() == "ai_high_performer":
            ai_col = c
            break
    # Check for 'Recruiter_Decision' column, if present, assign it to rec_col.
    rec_col = "Recruiter_Decision" if "Recruiter_Decision" in df.columns else None

    # Initialize counts and percentages for AI_High_Performer and Recruiter_Decision.
    ai_pos = ai_neg = rec_pos = rec_neg = 0
    ai_pos_pct = ai_neg_pct = 0.0
    # Calculate class distribution for AI_High_Performer if the column exists.
    if ai_col:
        ai_pos = int((df[ai_col] == 1).sum())
        ai_neg = int((df[ai_col] == 0).sum())
        total = max(1, ai_pos + ai_neg)
        ai_pos_pct = ai_pos * 100.0 / total
        ai_neg_pct = ai_neg * 100.0 / total
    # Calculate class distribution for Recruiter_Decision if the column exists.
    if rec_col:
        rec_pos = int((df[rec_col] == 1).sum())
        rec_neg = int((df[rec_col] == 0).sum())

    # Format the SUMMARY_TEMPLATE with the calculated class distribution values.
    text = SUMMARY_TEMPLATE.format(
        ai_pos=ai_pos, ai_pos_pct=ai_pos_pct, ai_neg=ai_neg, ai_neg_pct=ai_neg_pct,
        rec_pos=rec_pos, rec_neg=rec_neg,
    )
    # Create a Path object for the output Markdown file.
    out_path = Path(args.out)
    # Create parent directories for the output file if they don't exist.
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Write the formatted summary text to the output Markdown file.
    out_path.write_text(text, encoding="utf-8")
    # Print a confirmation message with the path to the generated report.
    print(f"Wrote summary to: {out_path}")


# Check if the script is being run directly (not imported as a module).
if __name__ == "__main__":
    # Call the main function to execute the script's logic.
    main()