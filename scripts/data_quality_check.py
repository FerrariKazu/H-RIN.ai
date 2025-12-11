"""


This script performs a series of data quality checks on a specified CSV file.
It includes checks for data completeness (missing values), data consistency (data types,
numeric value ranges), data accuracy (outliers using the IQR method), and structural
integrity (duplicate rows). The script generates a detailed report and saves it to a text file

Usage:
    python data_quality_check.py

Dependencies:
    - pandas
    - numpy
    - pathlib

The script expects a CSV file at 'data/normalized_dataset_v2.csv' and
outputs a report to 'reports/data_quality_report.txt'.
"""

#!/usr/bin/env python3

# Standard library imports
from pathlib import Path # For object-oriented filesystem paths.
import os

# Third-party library imports
import pandas as pd # For data manipulation and analysis.
import numpy as np # For numerical operations, especially for selecting numeric columns.

def run_data_quality_checks(file_path: Path) -> str:
    """
    Runs a series of data quality checks on the given CSV file.

    Args:
        file_path (Path): The path to the CSV file to be checked.

    Returns:
        str: A formatted report string detailing the data quality findings.
    """
    # Print a message indicating which file is being processed.
    print(f"Running data quality checks on {file_path}")
    # Read the CSV file into a pandas DataFrame.
    df = pd.read_csv(file_path)

    # Initialize an empty list to store report messages.
    report = []

    # --- Data Completeness Check ---
    # This section checks for missing values in the dataset.
    report.append("--- Data Completeness ---")
    # Calculate the count of missing values for each column.
    missing_values = df.isnull().sum()
    # Calculate the percentage of missing values for each column.
    missing_percentage = (df.isnull().sum() / len(df)) * 100
    # Create a DataFrame to display missing counts and percentages.
    missing_df = pd.DataFrame({
        'Missing Count': missing_values,
        'Missing Percentage': missing_percentage
    })
    # Filter the DataFrame to show only columns with missing values and sort them.
    missing_df = missing_df[missing_df['Missing Count'] > 0].sort_values(by='Missing Count', ascending=False)

    # Check if there are any missing values and add to the report.
    if not missing_df.empty:
        report.append("Missing values found:")
        # Add the missing values DataFrame to the report.
        report.append(missing_df.to_string())
    else:
        report.append("No missing values found.")

    # Add total records and columns to the report for completeness.
    report.append(f"Total records: {len(df)}")
    report.append(f"Total columns: {len(df.columns)}")

    # --- Data Consistency Check ---
    # This section verifies data types and value ranges for consistency.
    report.append("\n--- Data Consistency ---")
    report.append("Data Types:")
    # Add data types of all columns to the report.
    report.append(df.dtypes.to_string())

    # Select only numerical columns for further consistency checks.
    numeric_cols = df.select_dtypes(include=np.number).columns
    if not numeric_cols.empty:
        report.append("\nNumeric Feature Value Ranges (Min/Max/Mean/Std):")
        # Add descriptive statistics for numerical columns to the report.
        report.append(df[numeric_cols].describe().to_string())

        # Example: Check for negative values in specific columns where they are not expected.
        # This is a domain-specific check for 'Experience (Years)', 'Projects Count', and 'Salary Expectation ($)'.
        for col in ['Experience (Years)', 'Projects Count', 'Salary Expectation ($)']:
            if col in df.columns and (df[col] < 0).any():
                report.append(f"WARNING: Negative values found in {col}.")

    # --- Data Accuracy Check (Outliers using IQR method) ---
    # This section identifies potential outliers in numerical columns using the Interquartile Range (IQR) method.
    report.append("\n--- Data Accuracy (Outliers) ---")
    # Iterate through each numerical column to check for outliers.
    for col in numeric_cols:
        # Calculate the first quartile (Q1).
        Q1 = df[col].quantile(0.25)
        # Calculate the third quartile (Q3).
        Q3 = df[col].quantile(0.75)
        # Calculate the Interquartile Range (IQR).
        IQR = Q3 - Q1
        # Calculate the lower bound for outlier detection.
        lower_bound = Q1 - 1.5 * IQR
        # Calculate the upper bound for outlier detection.
        upper_bound = Q3 + 1.5 * IQR
        # Identify outliers based on the IQR method.
        outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
        # If outliers are found, add a summary to the report.
        if not outliers.empty:
            report.append(f"Potential outliers in {col}: {len(outliers)} records ({len(outliers)/len(df)*100:.2f}% of data).")
            # report.append(outliers[[col]].head().to_string()) # Uncomment to see sample outliers

    # --- Structural Integrity Check ---
    # This section checks for duplicate rows and notes on encoding.
    report.append("\n--- Structural Integrity ---")
    # Count duplicate rows.
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        report.append(f"Duplicate rows found: {duplicates}")
    else:
        report.append("No duplicate rows found.")

    # Note on encoding, assuming pandas handles it for CSV.
    report.append("Encoding: Assumed UTF-8 (handled by pandas read_csv).")

    # Join all report messages into a single string and return the comprehensive report.
    return "\n".join(report)

# Main execution block
# This ensures the script runs the data quality checks when executed directly.
if __name__ == "__main__":
    # Define the input file path for the dataset.
    input_file = Path(os.path.join("data", "normalized_dataset_v2.csv"))
    # Define the output report file path where the quality report will be saved.
    output_report = Path(os.path.join("reports", "data_quality_report.txt"))

    # Check if the input file exists before proceeding.
    if not input_file.exists():
        print(f"Error: Input file not found at {input_file}")
    else:
        # Run the data quality checks and capture the generated report content.
        report_content = run_data_quality_checks(input_file)
        # Ensure the output directory for the report exists.
        output_report.parent.mkdir(parents=True, exist_ok=True)
        # Write the comprehensive report content to the specified output file.
        output_report.write_text(report_content)
        # Print a confirmation message indicating where the report has been saved.
        print(f"Data quality report saved to {output_report}")