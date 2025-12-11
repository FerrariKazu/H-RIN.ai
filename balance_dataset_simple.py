import pandas as pd
import numpy as np
import os
from collections import Counter
import random

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

def load_and_backup_data():
    """Load original data and create backup"""
    print("Loading original dataset...")
    df = pd.read_csv(os.path.join('data', 'normalized_dataset_v3.csv'))
    print(f"Original dataset shape: {df.shape}")
    
    # Create backup
    df.to_csv(os.path.join('data', 'normalized_dataset_v3_backup.csv'), index=False)
    print("Backup created: data/normalized_dataset_v3_backup.csv")
    
    return df

def analyze_current_state(df):
    """Analyze current distributions for comparison"""
    analysis = {}
    
    # Job types
    job_cols = [col for col in df.columns if col.startswith('feat_job_')]
    analysis['job_distribution'] = {col: df[col].mean() for col in job_cols}
    
    # Skills
    skill_cols = [col for col in df.columns if col.startswith('feat_skill_')]
    analysis['skill_distribution'] = {col: df[col].mean() for col in skill_cols}
    
    # Degrees
    degree_cols = [col for col in df.columns if col.startswith('feat_degree_')]
    analysis['degree_distribution'] = {col: df[col].mean() for col in degree_cols}
    analysis['no_degree'] = 1 - df[degree_cols].any(axis=1).mean()
    
    # Certifications
    cert_cols = [col for col in df.columns if col.startswith('feat_cert_')]
    analysis['cert_distribution'] = {col: df[col].mean() for col in cert_cols}
    
    # Target variable
    if 'Recruiter_Decision' in df.columns:
        analysis['hire_ratio'] = (df['Recruiter_Decision'] == 'Hire').mean()
    
    return analysis

def create_synthetic_records(df, target_total=1000):
    """Create synthetic records to balance the dataset"""
    print(f"Creating synthetic records to reach {target_total} total records...")
    
    current_total = len(df)
    records_needed = target_total - current_total
    
    if records_needed <= 0:
        return df
    
    # Get existing non-tech records as templates
    non_tech_records = df[df['feat_job_tech'] == 0]
    
    synthetic_records = []
    
    # Define job type targets
    job_targets = {
        'feat_job_sales': int(target_total * 0.10),
        'feat_job_marketing': int(target_total * 0.10),
        'feat_job_finance': int(target_total * 0.10),
        'feat_job_operations': int(target_total * 0.10),
        'feat_job_hr': int(target_total * 0.08),
        'feat_job_product': int(target_total * 0.10),
        'feat_job_design': int(target_total * 0.07)
    }
    
    # Calculate how many more of each job type we need
    current_job_counts = {}
    for job_type in job_targets.keys():
        current_job_counts[job_type] = df[job_type].sum()
    
    # Generate synthetic records for each job type
    for job_type, target_count in job_targets.items():
        needed = target_count - current_job_counts[job_type]
        if needed > 0:
            print(f"Generating {needed} synthetic records for {job_type}")
            
            for i in range(needed):
                # Use existing non-tech record as template
                template = non_tech_records.sample(1).iloc[0].copy()
                
                # Reset all job types
                for job_col in [col for col in df.columns if col.startswith('feat_job_')]:
                    template[job_col] = 0
                
                # Set this job type
                template[job_type] = 1
                
                # Add appropriate skills based on job type
                if job_type == 'feat_job_sales':
                    template['feat_skill_excel'] = np.random.choice([0, 1], p=[0.2, 0.8])
                    template['feat_skill_project_management'] = np.random.choice([0, 1], p=[0.3, 0.7])
                    template['feat_cert_six_sigma'] = np.random.choice([0, 1], p=[0.6, 0.4])
                    template['feat_years_experience_extracted'] = np.random.randint(2, 8)
                    template['feat_salary_extracted'] = np.random.randint(60000, 120000)
                    
                elif job_type == 'feat_job_marketing':
                    template['feat_skill_excel'] = np.random.choice([0, 1], p=[0.1, 0.9])
                    template['feat_skill_tableau'] = np.random.choice([0, 1], p=[0.2, 0.8])
                    template['feat_skill_power_bi'] = np.random.choice([0, 1], p=[0.3, 0.7])
                    template['feat_years_experience_extracted'] = np.random.randint(2, 8)
                    template['feat_salary_extracted'] = np.random.randint(60000, 120000)
                    
                elif job_type == 'feat_job_finance':
                    template['feat_skill_excel'] = 1
                    template['feat_cert_cfa'] = np.random.choice([0, 1], p=[0.5, 0.5])
                    template['feat_cert_cpa'] = np.random.choice([0, 1], p=[0.6, 0.4])
                    template['feat_years_experience_extracted'] = np.random.randint(3, 10)
                    template['feat_salary_extracted'] = np.random.randint(70000, 140000)
                    
                elif job_type == 'feat_job_operations':
                    template['feat_skill_excel'] = np.random.choice([0, 1], p=[0.2, 0.8])
                    template['feat_cert_six_sigma'] = np.random.choice([0, 1], p=[0.3, 0.7])
                    template['feat_cert_pmp'] = np.random.choice([0, 1], p=[0.4, 0.6])
                    template['feat_years_experience_extracted'] = np.random.randint(3, 10)
                    template['feat_salary_extracted'] = np.random.randint(70000, 140000)
                    
                elif job_type == 'feat_job_hr':
                    template['feat_skill_excel'] = np.random.choice([0, 1], p=[0.2, 0.8])
                    template['feat_skill_project_management'] = np.random.choice([0, 1], p=[0.3, 0.7])
                    template['feat_cert_pmp'] = np.random.choice([0, 1], p=[0.5, 0.5])
                    template['feat_cert_scrum'] = np.random.choice([0, 1], p=[0.6, 0.4])
                    template['feat_years_experience_extracted'] = np.random.randint(2, 7)
                    template['feat_salary_extracted'] = np.random.randint(50000, 100000)
                    
                elif job_type == 'feat_job_product':
                    template['feat_skill_project_management'] = np.random.choice([0, 1], p=[0.2, 0.8])
                    template['feat_skill_tableau'] = np.random.choice([0, 1], p=[0.4, 0.6])
                    template['feat_years_experience_extracted'] = np.random.randint(3, 10)
                    template['feat_salary_extracted'] = np.random.randint(70000, 140000)
                    
                elif job_type == 'feat_job_design':
                    template['feat_years_experience_extracted'] = np.random.randint(2, 8)
                    template['feat_salary_extracted'] = np.random.randint(60000, 120000)
                
                # Generate random text length
                template['text_len'] = np.random.randint(1000, 3000)
                
                # Generate balanced recruiter decision
                template['Recruiter_Decision'] = np.random.choice(['Hire', 'Reject'], p=[0.5, 0.5])
                
                synthetic_records.append(template)
    
    # Combine synthetic records with original
    if synthetic_records:
        synthetic_df = pd.DataFrame(synthetic_records)
        final_df = pd.concat([df, synthetic_df], ignore_index=True)
    else:
        final_df = df
    
    print(f"Created {len(synthetic_records)} synthetic records")
    print(f"Final dataset size: {len(final_df)} records")
    
    return final_df

def downsample_tech_roles(df, target_tech_ratio=0.35):
    """Downsample tech roles to achieve target ratio"""
    print(f"Downsampling tech roles to {target_tech_ratio:.1%}")
    
    tech_indices = df[df['feat_job_tech'] == 1].index
    non_tech_indices = df[df['feat_job_tech'] == 0].index
    
    current_non_tech_count = len(non_tech_indices)
    target_tech_count = int(current_non_tech_count * target_tech_ratio / (1 - target_tech_ratio))
    
    if len(tech_indices) > target_tech_count:
        # Randomly sample tech records
        sampled_tech_indices = np.random.choice(tech_indices, target_tech_count, replace=False)
        
        # Combine with all non-tech
        final_indices = np.concatenate([sampled_tech_indices, non_tech_indices])
        df_downsampled = df.loc[final_indices].copy()
        
        print(f"Downsampled from {len(tech_indices)} to {target_tech_count} tech records")
        return df_downsampled
    
    return df

def add_missing_skills_simple(df):
    """Add missing skills with simple logic"""
    print("Adding missing skills...")
    
    # Excel - target 30%
    current_excel = df['feat_skill_excel'].mean()
    target_excel = 0.30
    
    if current_excel < target_excel:
        needed = int((target_excel - current_excel) * len(df))
        
        # Add Excel to business roles
        business_roles = ['feat_job_sales', 'feat_job_marketing', 'feat_job_finance', 'feat_job_operations', 'feat_job_hr']
        for role in business_roles:
            role_mask = df[role] == 1
            no_excel_mask = role_mask & (df['feat_skill_excel'] == 0)
            
            if no_excel_mask.sum() > 0:
                add_count = min(int(no_excel_mask.sum() * 0.8), needed)
                if add_count > 0:
                    indices = df[no_excel_mask].sample(add_count).index
                    df.loc[indices, 'feat_skill_excel'] = 1
                    needed -= add_count
    
    # Tableau - target 20%
    current_tableau = df['feat_skill_tableau'].mean()
    target_tableau = 0.20
    
    if current_tableau < target_tableau:
        needed = int((target_tableau - current_tableau) * len(df))
        
        # Add Tableau to marketing and product roles
        target_roles = ['feat_job_marketing', 'feat_job_product', 'feat_job_finance']
        for role in target_roles:
            role_mask = df[role] == 1
            no_tableau_mask = role_mask & (df['feat_skill_tableau'] == 0)
            
            if no_tableau_mask.sum() > 0:
                add_count = min(int(no_tableau_mask.sum() * 0.7), needed)
                if add_count > 0:
                    indices = df[no_tableau_mask].sample(add_count).index
                    df.loc[indices, 'feat_skill_tableau'] = 1
                    needed -= add_count
    
    # Power BI - target 15%
    current_powerbi = df['feat_skill_power_bi'].mean()
    target_powerbi = 0.15
    
    if current_powerbi < target_powerbi:
        needed = int((target_powerbi - current_powerbi) * len(df))
        
        # Add Power BI to marketing, finance, operations
        target_roles = ['feat_job_marketing', 'feat_job_finance', 'feat_job_operations']
        for role in target_roles:
            role_mask = df[role] == 1
            no_powerbi_mask = role_mask & (df['feat_skill_power_bi'] == 0)
            
            if no_powerbi_mask.sum() > 0:
                add_count = min(int(no_powerbi_mask.sum() * 0.6), needed)
                if add_count > 0:
                    indices = df[no_powerbi_mask].sample(add_count).index
                    df.loc[indices, 'feat_skill_power_bi'] = 1
                    needed -= add_count
    
    return df

def fix_degrees_simple(df):
    """Fix degree distribution"""
    print("Fixing degree distribution...")
    
    # Add bachelor's degrees - target 40%
    current_bachelor = df['feat_degree_bachelor'].mean()
    target_bachelor = 0.40
    
    if current_bachelor < target_bachelor:
        needed = int((target_bachelor - current_bachelor) * len(df))
        
        # Add to records with no degree and lower experience
        no_degree_mask = (df['feat_degree_bachelor'] == 0) & (df['feat_degree_master'] == 0) & (df['feat_degree_mba'] == 0) & (df['feat_degree_phd'] == 0)
        young_mask = df['feat_years_experience_extracted'] <= 5
        
        candidates = df[no_degree_mask & young_mask]
        if len(candidates) < needed:
            candidates = df[no_degree_mask]
        
        if len(candidates) > 0:
            update_count = min(needed, len(candidates))
            indices = candidates.sample(update_count).index
            
            df.loc[indices, 'feat_degree_bachelor'] = 1
            df.loc[indices, 'feat_top_degree_level'] = 1
    
    return df

def balance_certifications_simple(df):
    """Balance certifications"""
    print("Balancing certifications...")
    
    cert_targets = {
        'feat_cert_pmp': 0.12,
        'feat_cert_scrum': 0.10,
        'feat_cert_csm': 0.08,
        'feat_cert_six_sigma': 0.08,
        'feat_cert_cfa': 0.05,
        'feat_cert_cpa': 0.04
    }
    
    # Job to cert mapping
    job_cert_probs = {
        'feat_job_sales': {'feat_cert_six_sigma': 0.4, 'feat_cert_pmp': 0.2},
        'feat_job_marketing': {'feat_cert_pmp': 0.2},
        'feat_job_finance': {'feat_cert_cfa': 0.5, 'feat_cert_cpa': 0.4, 'feat_cert_six_sigma': 0.1},
        'feat_job_operations': {'feat_cert_six_sigma': 0.6, 'feat_cert_pmp': 0.4, 'feat_cert_scrum': 0.2},
        'feat_job_hr': {'feat_cert_pmp': 0.4, 'feat_cert_scrum': 0.3, 'feat_cert_csm': 0.2},
        'feat_job_product': {'feat_cert_pmp': 0.5, 'feat_cert_scrum': 0.3, 'feat_cert_csm': 0.2}
    }
    
    for cert, target in cert_targets.items():
        current = df[cert].mean()
        if current < target:
            needed = int((target - current) * len(df))
            
            for job_type, cert_probs in job_cert_probs.items():
                if cert in cert_probs:
                    job_mask = df[job_type] == 1
                    no_cert_mask = job_mask & (df[cert] == 0)
                    
                    if no_cert_mask.sum() > 0:
                        prob = cert_probs[cert]
                        add_count = min(int(no_cert_mask.sum() * prob), needed)
                        
                        if add_count > 0:
                            indices = df[no_cert_mask].sample(add_count).index
                            df.loc[indices, cert] = 1
                            needed -= add_count
                            
                            if needed <= 0:
                                break
    
    return df

def validate_final_dataset(df):
    """Final validation"""
    print("\n=== FINAL VALIDATION ===")
    
    # 1. Class balance
    hire_ratio = (df['Recruiter_Decision'] == 'Hire').mean()
    print(f"Hire ratio: {hire_ratio:.1%} (target: 45-55%)")
    
    # 2. Job type distribution
    job_cols = [col for col in df.columns if col.startswith('feat_job_')]
    print("\nJob type distribution:")
    for job_col in job_cols:
        distribution = df[job_col].mean()
        print(f"{job_col}: {distribution:.1%} (target: ≥5%)")
    
    # 3. Skill coverage
    print(f"\nExcel coverage: {df['feat_skill_excel'].mean():.1%} (target: ≥25%)")
    print(f"Tableau coverage: {df['feat_skill_tableau'].mean():.1%} (target: ≥15%)")
    print(f"Power BI coverage: {df['feat_skill_power_bi'].mean():.1%} (target: ≥10%)")
    
    # 4. Degree distribution
    print(f"\nBachelor's coverage: {df['feat_degree_bachelor'].mean():.1%} (target: ≥35%)")
    
    # 5. Total records
    print(f"\nTotal records: {len(df)} (target: ≥800)")
    
    # 6. No missing values
    missing = df.isnull().sum().sum()
    print(f"Missing values: {missing}")
    
    return {
        'hire_ratio': hire_ratio,
        'excel_coverage': df['feat_skill_excel'].mean(),
        'tableau_coverage': df['feat_skill_tableau'].mean(),
        'powerbi_coverage': df['feat_skill_power_bi'].mean(),
        'bachelor_coverage': df['feat_degree_bachelor'].mean(),
        'total_records': len(df),
        'missing_values': missing
    }

def generate_simple_report(original_df, balanced_df, original_analysis, final_validation):
    """Generate simple balance report"""
    print("\n=== GENERATING REPORT ===")
    
    with open(os.path.join('balance_report.txt'), 'w', encoding='utf-8') as f:
        f.write("DATASET BALANCING REPORT\n")
        f.write("=" * 50 + "\n\n")
        
        f.write("SUMMARY\n")
        f.write("-" * 20 + "\n")
        f.write(f"Original dataset size: {len(original_df)} records\n")
        f.write(f"Balanced dataset size: {len(balanced_df)} records\n")
        f.write(f"Records added: {len(balanced_df) - len(original_df)}\n\n")
        
        f.write("VALIDATION RESULTS\n")
        f.write("-" * 25 + "\n")
        f.write(f"Hire ratio: {final_validation['hire_ratio']:.1%} (target: 45-55%)\n")
        f.write(f"Excel coverage: {final_validation['excel_coverage']:.1%} (target: >=25%)\n")
        f.write(f"Tableau coverage: {final_validation['tableau_coverage']:.1%} (target: >=15%)\n")
        f.write(f"Power BI coverage: {final_validation['powerbi_coverage']:.1%} (target: >=10%)\n")
        f.write(f"Bachelor's coverage: {final_validation['bachelor_coverage']:.1%} (target: >=35%)\n")
        f.write(f"Total records: {final_validation['total_records']} (target: >=800)\n")
        f.write(f"Missing values: {final_validation['missing_values']}\n")
    
    print("Report saved to: balance_report.txt")

def main():
    """Main balancing pipeline - simplified version"""
    print("=== SIMPLIFIED DATASET BALANCING PIPELINE ===")
    
    # 1. Load and backup data
    df = load_and_backup_data()
    
    # 2. Analyze original state
    original_analysis = analyze_current_state(df)
    
    # 3. Create synthetic records for missing job types
    df = create_synthetic_records(df, target_total=1000)
    
    # 4. Downsample tech roles to 35%
    df = downsample_tech_roles(df, target_tech_ratio=0.35)
    
    # 5. Add missing skills
    df = add_missing_skills_simple(df)
    
    # 6. Fix degree distribution
    df = fix_degrees_simple(df)
    
    # 7. Balance certifications
    df = balance_certifications_simple(df)
    
    # 8. Final validation
    final_validation = validate_final_dataset(df)
    
    # 9. Save balanced dataset
    df.to_csv(os.path.join('normalized_dataset_v4_balanced.csv'), index=False)
    print(f"\nBalanced dataset saved to: normalized_dataset_v4_balanced.csv")
    
    # 10. Generate report
    generate_simple_report(df, df, original_analysis, final_validation)
    
    return df

if __name__ == "__main__":
    balanced_df = main()