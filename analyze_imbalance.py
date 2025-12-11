import pandas as pd

file_path = r'c:\Users\FerrariKazu\Documents\AI Folder\P3\AM-DS-01\models\pipeline_v3\normalized_dataset_v3.csv'
df = pd.read_csv(file_path)

# Assuming 'Recruiter_Decision' is the target variable
print("Distribution of 'Recruiter_Decision':")
print(df['Recruiter_Decision'].value_counts())

# Also check for 'AI Score (Uniform 0-100)' distribution if it's a target
print("\nDistribution of 'AI Score (Uniform 0-100)':")
print(df['AI Score (Uniform 0-100)'].value_counts())