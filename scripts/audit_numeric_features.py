"""
This script audits specified numeric features in a dataset, generating a detailed report. It calculates descriptive statistics, identifies frequent values, flags near-constant features, and saves the results to a text file.
"""
import argparse # Import the `argparse` module for command-line argument parsing.
from pathlib import Path # Import the `Path` class from `pathlib` for object-oriented filesystem paths.
import os
import numpy as np # Import `numpy` for numerical operations, though it's not directly used in this snippet, it's a common dependency for data analysis.
import pandas as pd # Import `pandas` for data manipulation and analysis, especially with DataFrames.


# Define a list of numeric features that will be audited.
NUMERIC_FEATURES = [
    "feat_text_len_words",
    "feat_text_len_chars",
    "feat_num_numbers",
    "feat_num_bullets",
    "feat_num_skills_matched",
]


# Define the main function to audit numeric features in a pandas DataFrame.
def audit_numeric_features(df: pd.DataFrame) -> str:
    """Audits specified numeric features in a DataFrame and returns a formatted report string.

    Args:
        df (pd.DataFrame): The input DataFrame containing the numeric features to audit.

    Returns:
        str: A multi-line string containing the audit report.
    """
    # Initialize an empty list to store lines of the audit report.
    lines = []
    # Add the title of the report.
    lines.append("Numeric Features Audit")
    # Add a separator for readability.
    lines.append("----------------------")
    # Add the total number of rows in the DataFrame to the report, formatted with a comma for thousands.
    lines.append(f"Rows: {len(df):,}")
    # Add an empty line for spacing.
    lines.append("")

    # Iterate over each feature name in the `NUMERIC_FEATURES` list.
    for col in NUMERIC_FEATURES:
        # Check if the current column exists in the DataFrame.
        if col not in df.columns:
            # If the column is missing, add a warning message to the report.
            lines.append(f"[WARN] Missing column: {col}")
            # Skip to the next feature.
            continue
        # Convert the column to numeric, coercing any errors to NaN.
        s = pd.to_numeric(df[col], errors="coerce")
        # Generate descriptive statistics for the series.
        desc = s.describe()
        # Add the feature name to the report.
        lines.append(f"Feature: {col}")
        # Add the descriptive statistics (count, mean, std, min, 25%, 50%, 75%, max) to the report, formatted to three decimal places.
        lines.append(
            f"  count={int(desc['count'])}, mean={desc['mean']:.3f}, std={desc['std']:.3f}, min={desc['min']:.3f}, 25%={desc['25%']:.3f}, 50%={desc['50%']:.3f}, 75%={desc['75%']:.3f}, max={desc['max']:.3f}"
        )
        # Calculate value frequencies for the top 5 most frequent values, including NaN.
        vc = s.value_counts(dropna=False).head(5)
        # Add a header for top values.
        lines.append("  top values:")
        # Iterate over the top values and their counts.
        for val, cnt in vc.items():
            # Label NaN values as "NaN" for display, otherwise convert the value to string.
            label = "NaN" if pd.isna(val) else str(val)
            # Add the value and its count to the report.
            lines.append(f"    {label}: {cnt}")
        # Near-constant detection: check if one value occupies >= 98% of the rows.
        total = int(s.shape[0])
        # Avoid division by zero if the series is empty.
        if total > 0:
            # Calculate the fraction of the most frequent value.
            max_frac = vc.iloc[0] / total
            # If the most frequent value constitutes 98% or more of the data, flag it as near-constant.
            if max_frac >= 0.98:
                lines.append(f"  [FLAG] Near-constant: {vc.index[0]} covers {max_frac:.2%} of rows")
        # Add an empty line for spacing between features.
        lines.append("")
    # Join all collected lines with newline characters to form the complete report string.
    return "\n".join(lines)


# Define the main execution function for the script.
def main():
    # Create an ArgumentParser object for command-line arguments.
    ap = argparse.ArgumentParser(description="Audit numeric features in a dataset.")
    # Add an argument for the input CSV file path, making it required.
    ap.add_argument("--input", required=True, help="Path to normalized dataset CSV")
    # Add an argument for the output audit report path, with a default value.
    ap.add_argument("--out", default=os.path.join("reports", "audits", "numeric_features_audit.txt"), help="Audit report output path")
    # Parse the command-line arguments.
    args = ap.parse_args()

    # --- Data Loading ---
    # Read the input CSV file into a pandas DataFrame.
    df = pd.read_csv(args.input)

    # --- Report Generation ---
    # Generate the audit report by calling `audit_numeric_features`.
    report = audit_numeric_features(df)

    # --- File Writing ---
    # Create a Path object for the output report file.
    out_path = Path(args.out)
    # Create parent directories for the output file if they don't exist.
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Write the generated report text to the output file using UTF-8 encoding.
    out_path.write_text(report, encoding="utf-8")
    # Print a confirmation message to the console indicating where the report was saved.
    print(f"Wrote numeric features audit to: {out_path}")


# Standard boilerplate to ensure `main()` is called when the script is executed.
if __name__ == "__main__":
    main()