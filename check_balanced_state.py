import pandas as pd
import numpy as np

# Load the balanced dataset
df = pd.read_csv('normalized_dataset_v4_balanced.csv')

print(f"Balanced dataset shape: {df.shape}")
print("\n=== JOB TYPE DISTRIBUTION ===")
job_cols = [col for col in df.columns if col.startswith('feat_job_')]
for col in job_cols:
    print(f"{col}: {df[col].mean():.1%}")

print("\n=== SKILLS COVERAGE ===")
skill_cols = ['feat_skill_excel', 'feat_skill_tableau', 'feat_skill_power_bi']
for col in skill_cols:
    print(f"{col}: {df[col].mean():.1%}")

print("\n=== DEGREE DISTRIBUTION ===")
print(f"Bachelor: {df['feat_degree_bachelor'].mean():.1%}")
print(f"Master: {df['feat_degree_master'].mean():.1%}")
print(f"MBA: {df['feat_degree_mba'].mean():.1%}")
print(f"PhD: {df['feat_degree_phd'].mean():.1%}")

print("\n=== CERTIFICATION DISTRIBUTION ===")
cert_cols = [col for col in df.columns if col.startswith('feat_cert_')]
for col in cert_cols:
    print(f"{col}: {df[col].mean():.1%}")

print(f"\n=== TARGET VARIABLE ===")
print(f"Hire ratio: {(df['Recruiter_Decision'] == 'Hire').mean():.1%}")

print(f"\n=== DATA QUALITY ===")
print(f"Missing values: {df.isnull().sum().sum()}")
print(f"Total records: {len(df)}")

# Check for any obvious issues
print(f"\n=== ISSUES IDENTIFIED ===")
if df.isnull().sum().sum() > 0:
    print("❌ Dataset contains missing values")
else:
    print("✅ No missing values")

if (df['Recruiter_Decision'] == 'Hire').mean() < 0.45 or (df['Recruiter_Decision'] == 'Hire').mean() > 0.55:
    print("❌ Hire ratio outside 45-55% range")
else:
    print("✅ Hire ratio within target range")

if df['feat_job_tech'].mean() > 0.35:
    print("❌ Tech jobs exceed 35% target")
else:
    print("✅ Tech jobs within target")

if df['feat_skill_excel'].mean() < 0.25:
    print("❌ Excel coverage below 25% target")
else:
    print("✅ Excel coverage meets target")

if df['feat_degree_bachelor'].mean() < 0.35:
    print("❌ Bachelor's degrees below 35% target")
else:
    print("✅ Bachelor's degrees meet target")