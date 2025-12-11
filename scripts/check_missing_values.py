"""
This script is designed to identify and report missing values in a specified CSV file.

It utilizes the pandas library to read a CSV file into a DataFrame and then calculates
the sum of null values for each column. If missing values are found, it prints the
columns along with their respective counts of missing values. If no missing values
are present, it reports that the dataset is clean.

Usage:
    To run this script, simply execute it from the command line. Ensure the `file_path` variable
    within the `if __name__ == "__main__":` block is correctly set to your target CSV file.

    Example:
        python scripts/check_missing_values.py

Dependencies:
    - pandas: Used for data manipulation and reading CSV files.

Functions:
    - `check_missing_values(file_path)`: Reads a CSV file and reports on missing values.

"""
# Import the pandas library, commonly used for data manipulation and analysis.
import pandas as pd
import os


# Define a function `check_missing_values` that takes a file path as input.
def check_missing_values(file_path):
    """Reads a CSV file into a pandas DataFrame and reports on missing values.

    Args:
        file_path (str): The path to the CSV file to be analyzed.
    """
    # Read the CSV file specified by `file_path` into a pandas DataFrame.
    df = pd.read_csv(file_path)
    # Calculate the sum of null (missing) values for each column.
    missing_values = df.isnull().sum()
    # Filter the `missing_values` Series to only include columns that have more than 0 missing values.
    missing_values = missing_values[missing_values > 0]
    
    # Check if the `missing_values` Series is empty.
    if missing_values.empty:
        # If it's empty, print a message indicating no missing values were found.
        print("No missing values found in the dataset.")
    else:
        # If missing values are found, print a header and then the Series of columns with their respective missing value counts.
        print("Missing values found in the following columns:")
        print(missing_values)

# This is the standard entry point for Python scripts.
if __name__ == "__main__":
    # --- Script Execution Configuration and Call ---
    # Define the path to the dataset. This is the file that will be checked for missing values.
    file_path = os.path.join("data", "normalized_dataset_v3.csv")
    # Call the `check_missing_values` function with the specified file path to execute the missing value check.
    check_missing_values(file_path)