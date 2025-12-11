"""
This script analyzes the 'AI_High_Performer' target variable for class imbalance in a given CSV dataset. It normalizes the target, calculates class counts and percentages, detects imbalance, and generates a report with recommendations for resampling, without modifying the original data.
"""
import argparse # Import the `argparse` module for command-line interface (CLI) argument parsing.
import os
from pathlib import Path # Import the `Path` class from `pathlib` for object-oriented filesystem paths.
import sys # Import the `sys` module to access system-specific parameters and functions, such as `sys.exit` for exiting the script.

import pandas as pd # Import the `pandas` library, commonly used for data loading, manipulation, and analysis.


# Define a function `normalize_target` that takes a pandas Series as input and returns a normalized Series.
def normalize_target(series: pd.Series) -> pd.Series:
    # This function returns a pandas Series of `Int64` dtype, containing only 0s, 1s, and NA (Not Applicable) values.
    # Create a copy of the input series to prevent modifying the original data passed by the caller.
    s = series.copy()

    # Check if the series data type is boolean.
    if pd.api.types.is_bool_dtype(s):
        # If boolean, map `True` to 1 and `False` to 0, then cast the series to pandas nullable `Int64` type.
        s = s.replace({True: 1, False: 0}).astype("Int64")
        # Return the normalized series.
        return s

    # Check if the series data type is numeric.
    if pd.api.types.is_numeric_dtype(s):
        # Coerce the series to a numeric type, converting any invalid parsing into `NaN` (Not a Number).
        s_num = pd.to_numeric(s, errors="coerce")
        # Create a boolean mask to identify values that are not `NaN` and are not equal to 0 or 1.
        invalid_mask = (~s_num.isna()) & (~s_num.isin([0, 1]))
        # If any invalid numeric values are found, raise a `ValueError`.
        if invalid_mask.any():
            # Get unique invalid values and sort them for display.
            unique_invalid = sorted(s_num[invalid_mask].unique().tolist())
            # Raise an error indicating non-binary numeric values.
            raise ValueError(
                f"Target column contains non-binary numeric values: {unique_invalid[:10]}"
            )
        # Return the numeric series cast to pandas nullable `Int64`.
        return s_num.astype("Int64")

    # If the series data type is an object (typically strings), map common labels to 0 or 1.
    mapping = {
        "1": 1,
        "0": 0,
        "true": 1,
        "false": 0,
        "t": 1,
        "f": 0,
        "yes": 1,
        "no": 0,
        "y": 1,
        "n": 0,
        "high": 1,
        "low": 0,
        "positive": 1,
        "negative": 0,
        "pos": 1,
        "neg": 0,
    }
    # Convert the series to string type, remove leading/trailing whitespace, and convert to lowercase.
    s_str = s.astype(str).str.strip().str.lower()
    # Apply the mapping to the string series.
    s_mapped = s_str.map(mapping)
    # Preserve the original missing values from the input series.
    s_mapped = s_mapped.where(~series.isna())
    # Detect any values that were not successfully mapped to 0 or 1 and are not `NaN`.
    invalid_mask = (~s_mapped.isna()) & (~s_mapped.isin([0, 1]))
    # If any unrecognised labels are found, raise a `ValueError`.
    if invalid_mask.any():
        # Get unique invalid string values and sort them for display.
        unique_invalid = sorted(s_str[invalid_mask].unique().tolist())
        # Raise an error indicating non-binary values not recognized.
        raise ValueError(
            f"Target column contains non-binary values not recognized: {unique_invalid[:10]}"
        )
    # Return the mapped series cast to pandas nullable `Int64`.
    return s_mapped.astype("Int64")


# Define a helper function to format integers with thousands separators.
def format_int(value: int) -> str:
    """Formats an integer with thousands separators for readability."""
    # Return a formatted string with commas for readability.
    return f"{value:,}"


# Define the main function where the script's execution begins.
def main():
    # --- Command-Line Argument Parsing ---
    # Initialize the argument parser with a script description.
    parser = argparse.ArgumentParser(
        description=(
            "Analyze target variable AI_High_Performer for class imbalance and "
            "generate a report."
        )
    )
    # Add the '--path' argument for specifying the dataset CSV file.
    parser.add_argument(
        "--path",
        # Default path if not provided.
        default=os.path.join("data_CLEANED_FIXED.csv"),
        help=(
            "Path to the dataset CSV file. If not provided and the default "
            "does not exist, please pass the correct path via --path."
        ),
    )
    # Parse the arguments from the command line.
    args = parser.parse_args()

    # --- Data Loading ---
    # Create a `Path` object from the provided CSV path.
    csv_path = Path(args.path)
    # Check if the specified CSV file exists.
    if not csv_path.exists():
        # If the file does not exist, print an error message to standard error.
        print(
            f"Dataset not found at '{csv_path}'. Please provide a valid path using --path.",
            file=sys.stderr,
        )
        # Exit the script with an error code of 2.
        sys.exit(2)

    # Attempt to read the CSV file into a pandas DataFrame.
    try:
        df = pd.read_csv(csv_path)
    # Catch any exceptions that occur during CSV reading.
    except Exception as e:
        # Print an error message to standard error if reading fails.
        print(f"Failed to read CSV: {e}", file=sys.stderr)
        # Exit the script with an error code of 2.
        sys.exit(2)

    # --- Target Column Verification ---
    # Verify the existence of the target column, first case-sensitively, then case-insensitively.
    # Initialize `target_col` to `None`.
    target_col = None
    # Check if "AI_High_Performer" exists as an exact column name.
    if "AI_High_Performer" in df.columns:
        # If it exists, set it as the target column.
        target_col = "AI_High_Performer"
    else:
        # If not, create a mapping of lowercase column names to their original names.
        lower_map = {c.lower(): c for c in df.columns}
        # Check if the lowercase version of the target column name exists in the mapping.
        if "ai_high_performer" in lower_map:
            # If found, set the target column to its original case name.
            target_col = lower_map["ai_high_performer"]

    # If `target_col` is still `None`, it means the target column was not found.
    if target_col is None:
        # Print an error message listing available columns to standard error.
        print(
            "Target column 'AI_High_Performer' not found. Available columns: "
            + ", ".join(df.columns),
            file=sys.stderr,
        )
        # Exit the script with an error code of 3.
        sys.exit(3)

    # --- Target Normalization and Cleaning --- 
    # Normalize the target column to binary values, handling missing values by dropping them.
    try:
        # Call `normalize_target` to convert the target column to strictly 0/1, preserving NAs.
        target_series = normalize_target(df[target_col])
    # Catch any exceptions that occur during target normalization.
    except Exception as e:
        # Print an error message to standard error if normalization fails.
        print(f"Failed to normalize target column: {e}", file=sys.stderr)
        # Exit the script with an error code of 4.
        sys.exit(4)

    # Count the number of rows with missing target values.
    missing_target = int(target_series.isna().sum())
    # Create a new DataFrame `df_clean` containing only rows where the target is not missing.
    df_clean = df.loc[~target_series.isna()].copy()
    # Align the cleaned target series with the filtered DataFrame and cast to integer type.
    target_clean = target_series.loc[df_clean.index].astype(int)

    # Compute the total number of samples and the counts for each class.
    total_samples = int(df_clean.shape[0])
    high_count = int((target_clean == 1).sum())
    low_count = int((target_clean == 0).sum())

    # Perform a sanity check to ensure the sum of class counts equals the total number of samples.
    if high_count + low_count != total_samples:
        # If there's a mismatch, print an error message to standard error.
        print(
            "Counts mismatch after normalization. Aborting to ensure accuracy.",
            file=sys.stderr,
        )
        # Exit the script with an error code of 5.
        sys.exit(5)

    # --- Class Imbalance Detection ---
    # Calculate class percentages.
    # Compute exact percentages for the 'high' class, guarding against division by zero.
    pct_high_exact = (high_count / total_samples) * 100 if total_samples > 0 else 0.0
    # Compute exact percentages for the 'low' class, guarding against division by zero.
    pct_low_exact = (low_count / total_samples) * 100 if total_samples > 0 else 0.0
    # Round the 'high' class percentage to the nearest integer for display purposes.
    pct_high = round(pct_high_exact)
    # Calculate the 'low' class percentage as the complement of the 'high' class percentage.
    pct_low = 100 - pct_high

    # Detect class imbalance.
    # Set `imbalance_detected` to `True` if either class has less than 30% of the total samples.
    imbalance_detected = (pct_high_exact < 30.0) or (pct_low_exact < 30.0)

    # Generate dataset summary statistics for numeric columns.
    try:
        # Compute summary statistics for numeric columns and convert to a string.
        summary_stats = df.describe(include=["number"]).to_string()
    # Catch any exceptions that occur during `describe()` method call.
    except Exception:
        # If an error occurs, set `summary_stats` to a fallback message.
        summary_stats = "Summary statistics unavailable."

    # --- Report Generation ---
    # Assemble the human-readable report line by line.
    lines = []
    # Add the header title to the report.
    lines.append("Target Variable Analysis: AI_High_Performer")
    # Add an underline separator for visual clarity.
    lines.append("------------------------------------------")
    # Add the total number of samples to the report, formatted for readability.
    lines.append(f"Total samples: {format_int(total_samples)}")
    # Add the count and percentage of the 'High Performers' (class 1).
    lines.append(
        f"High Performers (1): {format_int(high_count)} ({pct_high}%)"
    )
    # Add the count and percentage of 'Not High Performers' (class 0).
    lines.append(
        f"Not High Performers (0): {format_int(low_count)} ({pct_low}%)"
    )

    # If any rows were dropped due to missing target values, add a note to the report.
    if missing_target > 0:
        lines.append(
            f"\nDropped rows due to missing target: {format_int(missing_target)}"
        )

    # If class imbalance was detected, include a warning and guidance in the report.
    if imbalance_detected:
        # Format the exact percentages for the warning detail.
        warn_detail = (
            f"{pct_high_exact:.1f}% positive, {pct_low_exact:.1f}% negative"
        )
        # Add a prominent warning line about significant class imbalance.
        lines.append(
            "\n\u26A0\uFE0F Warning: Significant class imbalance detected ("
            + warn_detail
            + ")."
        )
        # Recommend resampling techniques to address the imbalance.
        lines.append(
            "Recommendation: Consider applying resampling techniques like SMOTE or "
            "random under/over sampling during model training."
        )

    # Append a section header for dataset summary and the summary statistics table.
    lines.append("\nDataset Summary (numeric columns):")
    lines.append(summary_stats)

    # Join all the lines with newline characters to form the complete report text.
    report_text = "\n".join(lines) + "\n"

    # --- Output and File Saving ---
    # Define the path for the output report file.
    report_path = Path(os.path.join("imbalance_report.txt"))
    # Attempt to write the report text to the file.
    try:
        # Persist the report to disk using UTF-8 encoding.
        report_path.write_text(report_text, encoding="utf-8")
    # Catch any exceptions that occur during file writing.
    except Exception as e:
        # Print an error message to standard error if writing fails.
        print(f"Failed to write report: {e}", file=sys.stderr)
        # Exit the script with an error code of 6.
        sys.exit(6)

    # --- Console Output ---
    # Print a console overview of the analysis results.
    print(
        f"Total samples: {format_int(total_samples)} | "
        f"High: {format_int(high_count)} ({pct_high}%) | "
        f"Not High: {format_int(low_count)} ({pct_low}%) "

    )
    # If imbalance was detected, print a warning to the console.
    if imbalance_detected:
        print(
            f"WARNING: Imbalance detected ({pct_high_exact:.1f}% vs {pct_low_exact:.1f}%). "
            "Consider resampling (SMOTE, under/over sampling)."
        )
    # Inform the user where the detailed report file has been saved.
    print(f"Report saved to: {report_path.resolve()}")



# This is the standard entry point for Python scripts.
# This idiom ensures that `main()` is called only when the script is executed directly,
# not when imported as a module.
if __name__ == "__main__":
    # If the script is executed directly, call the `main` function.
    main()