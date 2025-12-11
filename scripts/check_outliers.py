"""
This script is designed to detect and report outliers in specified numerical columns of a CSV file
using the Interquartile Range (IQR) method.

It reads a CSV file into a pandas DataFrame and then iterates through a predefined list of
numerical features. For each feature, it calculates the Q1 (25th percentile), Q3 (75th percentile),
and the IQR. Outliers are identified as values falling below `Q1 - 1.5 * IQR` or above
`Q3 + 1.5 * IQR`.

Usage:
    To run this script, simply execute it from the command line. Ensure the `file_path` variable
    and `numerical_features` list within the `if __name__ == "__main__":` block are correctly
    set to your target CSV file and the columns you wish to analyze.

    Example:
        python scripts/check_outliers.py

Dependencies:
    - pandas: Used for data manipulation and reading CSV files.

Functions:
    - `check_outliers(file_path, numerical_cols)`: Reads a CSV file and reports on outliers
      in the specified numerical columns.

"""
# Import the pandas library, commonly used for data manipulation and analysis.
import pandas as pd
import os


# Define a function `check_outliers` that takes the file path and a list of numerical columns as input.
def check_outliers(file_path, numerical_cols):
    """Detects and reports outliers in specified numerical columns of a CSV file using the IQR method.

    Args:
        file_path (str): The path to the CSV file to be analyzed.
        numerical_cols (list): A list of column names (strings) to check for outliers.
    """
    # Read the CSV file specified by `file_path` into a pandas DataFrame.
    df = pd.read_csv(file_path)
    
    # Print a header indicating the start of the outlier checking process.
    print("Checking for outliers using IQR method:")
    # Iterate through each column name provided in the `numerical_cols` list.
    for col in numerical_cols:
        # Check if the column exists in the DataFrame and if its data type is numeric.
        if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
            # Calculate the first quartile (25th percentile) of the column's data.
            Q1 = df[col].quantile(0.25)
            # Calculate the third quartile (75th percentile) of the column's data.
            Q3 = df[col].quantile(0.75)
            # Calculate the Interquartile Range (IQR).
            IQR = Q3 - Q1
            # Calculate the lower bound for outlier detection.
            lower_bound = Q1 - 1.5 * IQR
            # Calculate the upper bound for outlier detection.
            upper_bound = Q3 + 1.5 * IQR
            
            # Identify outliers: values that fall below the lower bound or above the upper bound.
            outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
            
            # Check if any outliers were found.
            if not outliers.empty:
                # If outliers are found, print details about them.
                print(f"\nOutliers found in column '{col}':")
                print(f"  - Lower Bound: {lower_bound}")
                print(f"  - Upper Bound: {upper_bound}")
                print(f"  - Number of outliers: {len(outliers)}")
                print(f"  - Outlier values (first 5):\n{outliers[col].head()}")
            else:
                # If no outliers are found, print a corresponding message.
                print(f"\nNo outliers found in column '{col}'.")
        # Handle cases where the specified column is not found in the dataset.
        elif col not in df.columns:
            print(f"\nColumn '{col}' not found in the dataset.")
        # Handle cases where the specified column is not numeric.
        else:
            print(f"\nColumn '{col}' is not a numeric type, skipping outlier check.")

# This block ensures the `check_outliers` function is called only when the script is executed directly.
# It configures the file path and the list of numerical features to be analyzed.
if __name__ == "__main__":
    # Define the path to the dataset. This is the file that will be checked for outliers.
    file_path = os.path.join("data", "normalized_dataset_v3.csv")
    # Define a list of key numerical columns to be checked for outliers.
    numerical_features = [
        "feat_num_skills_matched",
        "feat_years_experience_extracted",
        "AI Score (0-100)",
        "Experience (Years)",
        "Salary Expectation ($)",
        "Projects Count",
        "feat_text_len_chars",
        "feat_text_len_words"
    ]
    # Call the `check_outliers` function with the specified file path and numerical features to execute the outlier check.
    check_outliers(file_path, numerical_features)