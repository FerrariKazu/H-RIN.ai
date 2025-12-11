"""
This script is designed to check and display the data types of columns in a specified CSV file.

It utilizes the pandas library to read a CSV file into a DataFrame and then prints the data types
of each column, which is useful for initial data exploration and validation.

Usage:
    To run this script, simply execute it from the command line. Ensure the `file_path` variable
    within the `if __name__ == "__main__":` block is correctly set to your target CSV file.

    Example:
        python scripts/check_data_types.py

Dependencies:
    - pandas: Used for data manipulation and reading CSV files.

Functions:
    - `check_data_types(file_path)`: Reads a CSV file and prints the data types of its columns.

"""
# Import the pandas library, commonly used for data manipulation and analysis.
import pandas as pd
import os


# Define a function `check_data_types` that takes a file path as input.
def check_data_types(file_path):
    """Reads a CSV file into a pandas DataFrame and prints the data types of its columns.

    Args:
        file_path (str): The path to the CSV file to be analyzed.
    """
    # Read the CSV file specified by `file_path` into a pandas DataFrame.
    df = pd.read_csv(file_path)
    # Print a header indicating that the following output will be the data types of the columns.
    print("Data types of columns:")
    # Print the data types of each column in the DataFrame.
    print(df.dtypes)

# Main execution block:
# This section ensures the script runs only when executed directly,
# not when imported as a module. It defines the target CSV file
# and initiates the data type checking process.
if __name__ == "__main__":
    # Define the path to the dataset. This is the file that will be checked for data types.
    file_path = os.path.join("data", "normalized_dataset_v3.csv")
    # Call the `check_data_types` function with the specified file path to execute the data type check.
    check_data_types(file_path)