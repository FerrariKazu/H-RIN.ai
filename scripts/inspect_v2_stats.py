import pandas as pd # Imports the pandas library for data manipulation.
import os # Imports the os module for path manipulation.
from pathlib import Path # Imports the Path class for object-oriented filesystem paths.

def main():
    # Defines the path to the normalized dataset v2 CSV file.
    p = Path(os.path.join('data', 'normalized_dataset_v2.csv'))
    # Checks if the file exists.
    if not p.exists():
        # Prints an error message if the file is not found.
        print('File not found:', p)
        return # Exits the function if the file is not found.
    # Reads the CSV file into a pandas DataFrame.
    df = pd.read_csv(p)
    # Computes value counts for 'Recruiter_Decision' column if it exists, otherwise an empty dictionary.
    counts = df['Recruiter_Decision'].value_counts().to_dict() if 'Recruiter_Decision' in df.columns else {}
    # Prints the counts of 'Recruiter_Decision'.
    print('Recruiter_Decision counts:', counts)
    # Defines a helper function to calculate the mean of a column.
    def mean(col):
        # Converts the column to numeric, coercing errors, and returns the mean or 0 if empty.
        return float(pd.to_numeric(df.get(col), errors='coerce').mean() or 0)
    # Prints the mean of 'feat_text_len_words'.
    print('feat_text_len_words mean:', mean('feat_text_len_words'))
    # Prints the mean of 'feat_text_len_chars'.
    print('feat_text_len_chars mean:', mean('feat_text_len_chars'))
    # Prints the mean of 'feat_years_experience_extracted'.
    print('feat_years_experience_extracted mean:', mean('feat_years_experience_extracted'))
    # Checks for the presence of 'feat_num_numbers' and 'feat_num_bullets' columns.
    for col in ['feat_num_numbers', 'feat_num_bullets']:
        print(col, 'present?', col in df.columns)

if __name__ == '__main__':
    main() # Calls the main function when the script is executed.