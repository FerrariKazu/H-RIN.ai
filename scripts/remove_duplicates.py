#!/usr/bin/env python3  # Shebang line: specifies the interpreter for executing the script

import pandas as pd  # Import the pandas library for data manipulation
from pathlib import Path  # Import Path from pathlib for object-oriented filesystem paths
import os # Import os for path manipulation
import sys # Import sys for system-specific parameters and functions

# Define the root directory of the project
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def remove_duplicates(input_file: Path, output_file: Path):  # Function to remove duplicate rows from a CSV file
    print(f"Loading data from {input_file}")  # Print message indicating data loading
    df = pd.read_csv(input_file)  # Read the input CSV file into a pandas DataFrame

    initial_rows = len(df)  # Get the number of rows before deduplication
    df_cleaned = df.drop_duplicates()  # Remove duplicate rows from the DataFrame
    rows_after_deduplication = len(df_cleaned)  # Get the number of rows after deduplication

    print(f"Initial number of rows: {initial_rows}")  # Print initial row count
    print(f"Number of rows after removing duplicates: {rows_after_deduplication}")  # Print row count after deduplication
    print(f"Number of duplicate rows removed: {initial_rows - rows_after_deduplication}")  # Print count of removed duplicates

    output_file.parent.mkdir(parents=True, exist_ok=True)  # Ensure the output directory exists
    df_cleaned.to_csv(output_file, index=False)  # Save the cleaned DataFrame to a new CSV file
    print(f"Cleaned data saved to {output_file}")  # Print message indicating data saving

if __name__ == "__main__":  # Standard boilerplate to run main function when script is executed
    input_path = ROOT / "data" / "normalized_dataset_v2.csv"  # Define the input file path
    output_path = ROOT / "data" / "normalized_dataset_v3.csv"  # Define the output file path
    remove_duplicates(input_path, output_path)  # Call the remove_duplicates function with specified paths