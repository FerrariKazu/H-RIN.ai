import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter

def analyze_dataset():
    """Analyze the current dataset to understand imbalances"""
    
    # Load the dataset
    print("Loading data/normalized_dataset_v3.csv...")
    df = pd.read_csv('data/normalized_dataset_v3.csv')
    
    print(f"Dataset shape: {df.shape}")
    print(f"Total records: {len(df)}")
    print(f"Total features: {df.shape[1]}")
    print("\n" + "="*50)
    
    # 1. Job Type Analysis
    print("1. JOB TYPE DISTRIBUTION")
    print("-" * 30)
    job_columns = [col for col in df.columns if col.startswith('feat_job_')]
    job_counts = {}
    
    for col in job_columns:
        count = df[col].sum()
        percentage = (count / len(df)) * 100
        job_counts[col] = {'count': count, 'percentage': percentage}
        print(f"{col}: {count} records ({percentage:.1f}%)")
    
    print(f"\nTotal job assignments: {sum([job_counts[col]['count'] for col in job_columns])}")
    print("Note: Each person can have multiple job types")
    print("\n" + "="*50)
    
    # 2. Skills Analysis
    print("2. SKILLS DISTRIBUTION")
    print("-" * 30)
    skill_columns = [col for col in df.columns if col.startswith('feat_skill_')]
    skill_counts = {}
    
    for col in skill_columns:
        count = df[col].sum()
        percentage = (count / len(df)) * 100
        skill_counts[col] = {'count': count, 'percentage': percentage}
        print(f"{col}: {count} records ({percentage:.1f}%)")
    
    print("\n" + "="*50)
    
    # 3. Degree Analysis
    print("3. DEGREE DISTRIBUTION")
    print("-" * 30)
    degree_columns = [col for col in df.columns if col.startswith('feat_degree_')]
    degree_counts = {}
    
    for col in degree_columns:
        count = df[col].sum()
        percentage = (count / len(df)) * 100
        degree_counts[col] = {'count': count, 'percentage': percentage}
        print(f"{col}: {count} records ({percentage:.1f}%)")
    
    # Calculate no degree
    no_degree = len(df) - sum([degree_counts[col]['count'] for col in degree_columns])
    no_degree_pct = (no_degree / len(df)) * 100
    print(f"No degree: {no_degree} records ({no_degree_pct:.1f}%)")
    
    print("\n" + "="*50)
    
    # 4. Certification Analysis
    print("4. CERTIFICATION DISTRIBUTION")
    print("-" * 30)
    cert_columns = [col for col in df.columns if col.startswith('feat_cert_')]
    cert_counts = {}
    
    for col in cert_columns:
        count = df[col].sum()
        percentage = (count / len(df)) * 100
        cert_counts[col] = {'count': count, 'percentage': percentage}
        print(f"{col}: {count} records ({percentage:.1f}%)")
    
    print("\n" + "="*50)
    
    # 5. Target Variable Analysis
    print("5. RECRUITER DECISION DISTRIBUTION")
    print("-" * 30)
    if 'Recruiter_Decision' in df.columns:
        decision_counts = df['Recruiter_Decision'].value_counts()
        for decision, count in decision_counts.items():
            percentage = (count / len(df)) * 100
            print(f"{decision}: {count} records ({percentage:.1f}%)")
    else:
        print("Recruiter_Decision column not found")
    
    print("\n" + "="*50)
    
    # 6. Missing Values Analysis
    print("6. MISSING VALUES ANALYSIS")
    print("-" * 30)
    missing_counts = df.isnull().sum()
    total_missing = missing_counts.sum()
    print(f"Total missing values: {total_missing}")
    
    if total_missing > 0:
        print("\nColumns with missing values:")
        for col, count in missing_counts[missing_counts > 0].items():
            percentage = (count / len(df)) * 100
            print(f"{col}: {count} missing ({percentage:.1f}%)")
    else:
        print("No missing values found!")
    
    print("\n" + "="*50)
    
    # 7. Key Numeric Features Analysis
    print("7. KEY NUMERIC FEATURES")
    print("-" * 30)
    numeric_cols = ['feat_num_skills_matched', 'feat_years_experience_extracted', 
                   'feat_num_projects_extracted', 'feat_salary_extracted', 'text_len']
    
    for col in numeric_cols:
        if col in df.columns:
            print(f"\n{col}:")
            print(f"  Min: {df[col].min()}")
            print(f"  Max: {df[col].max()}")
            print(f"  Mean: {df[col].mean():.2f}")
            print(f"  Std: {df[col].std():.2f}")
    
    print("\n" + "="*50)
    
    # 8. Top Degree Level Analysis
    print("8. TOP DEGREE LEVEL DISTRIBUTION")
    print("-" * 30)
    if 'feat_top_degree_level' in df.columns:
        degree_level_counts = df['feat_top_degree_level'].value_counts().sort_index()
        for level, count in degree_level_counts.items():
            percentage = (count / len(df)) * 100
            level_name = {0: 'No degree', 1: 'Bachelor', 2: 'Master/MBA', 3: 'PhD'}.get(level, f'Level {level}')
            print(f"{level_name}: {count} records ({percentage:.1f}%)")
    
    return {
        'job_counts': job_counts,
        'skill_counts': skill_counts,
        'degree_counts': degree_counts,
        'cert_counts': cert_counts,
        'total_records': len(df),
        'missing_values': total_missing
    }

if __name__ == "__main__":
    results = analyze_dataset()