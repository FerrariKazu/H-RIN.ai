import pandas as pd
import numpy as np

# Load the dataset with missing certifications
df = pd.read_csv('normalized_dataset_v4_balanced.csv')

print("Before fixing certifications:")
print(f"feat_cert_csm: {df['feat_cert_csm'].mean():.1%}")
print(f"feat_cert_azure: {df['feat_cert_azure'].mean():.1%}")
print(f"feat_cert_gcp: {df['feat_cert_gcp'].mean():.1%}")

# Fix feat_cert_csm - need to reach 4%
current_csm = df['feat_cert_csm'].mean()
target_csm = 0.04
needed_csm = int((target_csm - current_csm) * len(df))

if needed_csm > 0:
    print(f"Need to add {needed_csm} CSM certifications")
    
    # Add CSM to appropriate job types (HR, Product, Operations)
    target_jobs = ['feat_job_hr', 'feat_job_product', 'feat_job_operations']
    
    for job_type in target_jobs:
        job_mask = df[job_type] == 1
        no_csm_mask = job_mask & (df['feat_cert_csm'] == 0)
        
        if no_csm_mask.sum() > 0:
            add_count = min(needed_csm, no_csm_mask.sum())
            indices = df[no_csm_mask].sample(add_count).index
            df.loc[indices, 'feat_cert_csm'] = 1
            needed_csm -= add_count
            
            if needed_csm <= 0:
                break

# Fix feat_cert_azure - need to reach 4%
current_azure = df['feat_cert_azure'].mean()
target_azure = 0.04
needed_azure = int((target_azure - current_azure) * len(df))

if needed_azure > 0:
    print(f"Need to add {needed_azure} Azure certifications")
    
    # Add Azure to tech roles
    tech_mask = df['feat_job_tech'] == 1
    no_azure_mask = tech_mask & (df['feat_cert_azure'] == 0)
    
    if no_azure_mask.sum() > 0:
        add_count = min(needed_azure, no_azure_mask.sum())
        indices = df[no_azure_mask].sample(add_count).index
        df.loc[indices, 'feat_cert_azure'] = 1

# Fix feat_cert_gcp - need to reach 4%
current_gcp = df['feat_cert_gcp'].mean()
target_gcp = 0.04
needed_gcp = int((target_gcp - current_gcp) * len(df))

if needed_gcp > 0:
    print(f"Need to add {needed_gcp} GCP certifications")
    
    # Add GCP to tech roles
    tech_mask = df['feat_job_tech'] == 1
    no_gcp_mask = tech_mask & (df['feat_cert_gcp'] == 0)
    
    if no_gcp_mask.sum() > 0:
        add_count = min(needed_gcp, no_gcp_mask.sum())
        indices = df[no_gcp_mask].sample(add_count).index
        df.loc[indices, 'feat_cert_gcp'] = 1

print("\nAfter fixing certifications:")
print(f"feat_cert_csm: {df['feat_cert_csm'].mean():.1%}")
print(f"feat_cert_azure: {df['feat_cert_azure'].mean():.1%}")
print(f"feat_cert_gcp: {df['feat_cert_gcp'].mean():.1%}")

# Save the final fixed dataset
df.to_csv('normalized_dataset_v4_balanced.csv', index=False)
print("\nFinal balanced dataset saved!")

# Final validation
print("\n=== FINAL VALIDATION ===")
print(f"Total records: {len(df)}")
print(f"Missing values: {df.isnull().sum().sum()}")
print(f"Hire ratio: {(df['Recruiter_Decision'] == 'Hire').mean():.1%}")

print("\nAll certifications:")
cert_cols = [col for col in df.columns if col.startswith('feat_cert_')]
for cert_col in cert_cols:
    coverage = df[cert_col].mean()
    status = "✅" if coverage >= 0.04 else "❌"
    print(f"{cert_col}: {coverage:.1%} {status}")

print("\n🎉 Dataset balancing complete!")