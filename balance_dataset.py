import pandas as pd
import numpy as np
from imblearn.over_sampling import SMOTENC
from sklearn.preprocessing import StandardScaler
from faker import Faker
import random
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)
fake = Faker()
Faker.seed(42)

def load_and_backup_data():
    """Load original data and create backup"""
    print("Loading original dataset...")
    df = pd.read_csv('data/normalized_dataset_v3.csv')
    print(f"Original dataset shape: {df.shape}")
    
    # Create backup
    df.to_csv('data/normalized_dataset_v3_backup.csv', index=False)
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

def downsample_tech_roles(df, target_tech_ratio=0.35):
    """Downsample tech roles to achieve target ratio"""
    print(f"Downsampling tech roles from {df['feat_job_tech'].mean():.1%} to {target_tech_ratio:.1%}")
    
    # Get tech and non-tech indices
    tech_indices = df[df['feat_job_tech'] == 1].index
    non_tech_indices = df[df['feat_job_tech'] == 0].index
    
    current_tech_count = len(tech_indices)
    current_non_tech_count = len(non_tech_indices)
    
    # Calculate target tech count
    target_total = int(current_non_tech_count / (1 - target_tech_ratio))
    target_tech_count = int(target_total * target_tech_ratio)
    
    # Randomly sample tech records
    sampled_tech_indices = np.random.choice(tech_indices, target_tech_count, replace=False)
    
    # Combine sampled tech with all non-tech
    final_indices = np.concatenate([sampled_tech_indices, non_tech_indices])
    df_downsampled = df.loc[final_indices].copy()
    
    print(f"After downsampling: {len(df_downsampled)} records")
    print(f"Tech ratio: {df_downsampled['feat_job_tech'].mean():.1%}")
    
    return df_downsampled

def generate_synthetic_job_records(df, job_type, target_count, job_skills_mapping):
    """Generate synthetic records for specific job type"""
    print(f"Generating {target_count} synthetic records for {job_type}")
    
    # Get existing records of this job type (if any)
    existing_records = df[df[job_type] == 1]
    
    if len(existing_records) == 0:
        # No existing records, create from scratch
        # Use non-tech records as base and modify
        base_records = df[df['feat_job_tech'] == 0].sample(min(target_count, len(df[df['feat_job_tech'] == 0])))
    else:
        # Use existing records as base
        base_records = existing_records.sample(min(target_count, len(existing_records)), replace=True)
    
    synthetic_records = []
    
    for i in range(target_count):
        # Start with a base record
        if len(base_records) > 0:
            base_idx = i % len(base_records)
            new_record = base_records.iloc[base_idx].copy()
        else:
            # Create from scratch if no base records
            new_record = df.sample(1).iloc[0].copy()
        
        # Set job type
        for job_col in [col for col in df.columns if col.startswith('feat_job_')]:
            new_record[job_col] = 0
        new_record[job_type] = 1
        
        # Add appropriate skills
        if job_type in job_skills_mapping:
            skills_to_add = job_skills_mapping[job_type]
            for skill in skills_to_add:
                if skill in df.columns:
                    # Add skill with high probability based on job type
                    if job_type == 'feat_job_sales':
                        new_record['feat_skill_excel'] = np.random.choice([0, 1], p=[0.2, 0.8])
                        new_record['feat_skill_project_management'] = np.random.choice([0, 1], p=[0.3, 0.7])
                        new_record['feat_cert_six_sigma'] = np.random.choice([0, 1], p=[0.6, 0.4])
                    elif job_type == 'feat_job_marketing':
                        new_record['feat_skill_excel'] = np.random.choice([0, 1], p=[0.1, 0.9])
                        new_record['feat_skill_tableau'] = np.random.choice([0, 1], p=[0.2, 0.8])
                        new_record['feat_skill_power_bi'] = np.random.choice([0, 1], p=[0.3, 0.7])
                    elif job_type == 'feat_job_finance':
                        new_record['feat_skill_excel'] = 1
                        new_record['feat_cert_cfa'] = np.random.choice([0, 1], p=[0.5, 0.5])
                        new_record['feat_cert_cpa'] = np.random.choice([0, 1], p=[0.6, 0.4])
                    elif job_type == 'feat_job_product':
                        new_record['feat_skill_project_management'] = np.random.choice([0, 1], p=[0.2, 0.8])
                        new_record['feat_skill_tableau'] = np.random.choice([0, 1], p=[0.4, 0.6])
                    elif job_type == 'feat_job_operations':
                        new_record['feat_skill_excel'] = np.random.choice([0, 1], p=[0.2, 0.8])
                        new_record['feat_cert_six_sigma'] = np.random.choice([0, 1], p=[0.3, 0.7])
                        new_record['feat_cert_pmp'] = np.random.choice([0, 1], p=[0.4, 0.6])
                    elif job_type == 'feat_job_hr':
                        new_record['feat_skill_excel'] = np.random.choice([0, 1], p=[0.2, 0.8])
                        new_record['feat_skill_project_management'] = np.random.choice([0, 1], p=[0.3, 0.7])
                        new_record['feat_cert_pmp'] = np.random.choice([0, 1], p=[0.5, 0.5])
                        new_record['feat_cert_scrum'] = np.random.choice([0, 1], p=[0.6, 0.4])
        
        # Adjust experience and other features
        if job_type in ['feat_job_sales', 'feat_job_marketing', 'feat_job_finance']:
            # Business roles typically have moderate experience
            new_record['feat_years_experience_extracted'] = np.random.randint(2, 8)
            new_record['feat_salary_extracted'] = np.random.randint(60000, 120000)
        elif job_type in ['feat_job_product', 'feat_job_operations']:
            # Product/Operations roles have varied experience
            new_record['feat_years_experience_extracted'] = np.random.randint(3, 10)
            new_record['feat_salary_extracted'] = np.random.randint(70000, 140000)
        elif job_type == 'feat_job_hr':
            # HR roles
            new_record['feat_years_experience_extracted'] = np.random.randint(2, 7)
            new_record['feat_salary_extracted'] = np.random.randint(50000, 100000)
        
        # Generate realistic text length
        new_record['text_len'] = np.random.randint(1000, 3000)
        
        # Generate recruiter decision with balanced probability
        new_record['Recruiter_Decision'] = np.random.choice(['Hire', 'Reject'], p=[0.5, 0.5])
        
        synthetic_records.append(new_record)
    
    return pd.DataFrame(synthetic_records)

def balance_job_types(df):
    """Balance job type distribution"""
    print("\n=== BALANCING JOB TYPES ===")
    
    target_distribution = {
        'feat_job_tech': 0.35,
        'feat_job_sales': 0.10,
        'feat_job_marketing': 0.10,
        'feat_job_finance': 0.10,
        'feat_job_operations': 0.10,
        'feat_job_hr': 0.08,
        'feat_job_product': 0.10,
        'feat_job_design': 0.07
    }
    
    job_skills_mapping = {
        'feat_job_sales': ['feat_skill_excel', 'feat_skill_project_management', 'feat_cert_six_sigma'],
        'feat_job_marketing': ['feat_skill_excel', 'feat_skill_tableau', 'feat_skill_power_bi'],
        'feat_job_finance': ['feat_skill_excel', 'feat_cert_cfa', 'feat_cert_cpa'],
        'feat_job_product': ['feat_skill_project_management', 'feat_skill_tableau'],
        'feat_job_operations': ['feat_skill_excel', 'feat_cert_six_sigma', 'feat_cert_pmp'],
        'feat_job_hr': ['feat_skill_excel', 'feat_skill_project_management', 'feat_cert_pmp', 'feat_cert_scrum']
    }
    
    # First, downsample tech roles
    df = downsample_tech_roles(df, target_tech_ratio=target_distribution['feat_job_tech'])
    
    # Calculate target counts for each job type
    target_total = 1000  # Target total records
    current_counts = {}
    
    for job_type in target_distribution.keys():
        current_counts[job_type] = df[job_type].sum()
    
    # Generate synthetic records for underrepresented job types
    all_synthetic_records = []
    
    for job_type, target_ratio in target_distribution.items():
        if job_type == 'feat_job_tech':
            continue  # Already handled by downsampling
            
        target_count = int(target_total * target_ratio)
        current_count = current_counts[job_type]
        
        if current_count < target_count:
            records_needed = target_count - current_count
            print(f"Need {records_needed} more records for {job_type}")
            
            synthetic_records = generate_synthetic_job_records(df, job_type, records_needed, job_skills_mapping)
            all_synthetic_records.append(synthetic_records)
    
    # Combine all synthetic records
    if all_synthetic_records:
        synthetic_df = pd.concat(all_synthetic_records, ignore_index=True)
        df_balanced = pd.concat([df, synthetic_df], ignore_index=True)
    else:
        df_balanced = df
    
    print(f"Final dataset size: {len(df_balanced)}")
    
    # Print final job distribution
    print("\nFinal job distribution:")
    for job_type in target_distribution.keys():
        count = df_balanced[job_type].sum()
        percentage = count / len(df_balanced) * 100
        print(f"{job_type}: {count} records ({percentage:.1f}%)")
    
    return df_balanced

def add_missing_skills(df):
    """Add missing skills with logical job-type assignments"""
    print("\n=== ADDING MISSING SKILLS ===")
    
    target_skill_coverage = {
        'feat_skill_excel': 0.30,
        'feat_skill_tableau': 0.20,
        'feat_skill_power_bi': 0.15
    }
    
    # Job type to skill mapping probabilities
    job_skill_probs = {
        'feat_job_sales': {
            'feat_skill_excel': 0.8,
            'feat_skill_tableau': 0.3,
            'feat_skill_power_bi': 0.2
        },
        'feat_job_marketing': {
            'feat_skill_excel': 0.9,
            'feat_skill_tableau': 0.8,
            'feat_skill_power_bi': 0.7
        },
        'feat_job_finance': {
            'feat_skill_excel': 0.95,
            'feat_skill_tableau': 0.6,
            'feat_skill_power_bi': 0.8
        },
        'feat_job_operations': {
            'feat_skill_excel': 0.8,
            'feat_skill_tableau': 0.4,
            'feat_skill_power_bi': 0.6
        },
        'feat_job_hr': {
            'feat_skill_excel': 0.8,
            'feat_skill_tableau': 0.3,
            'feat_skill_power_bi': 0.4
        },
        'feat_job_product': {
            'feat_skill_excel': 0.6,
            'feat_skill_tableau': 0.7,
            'feat_skill_power_bi': 0.5
        },
        'feat_job_tech': {
            'feat_skill_excel': 0.4,
            'feat_skill_tableau': 0.3,
            'feat_skill_power_bi': 0.2
        },
        'feat_job_design': {
            'feat_skill_excel': 0.3,
            'feat_skill_tableau': 0.5,
            'feat_skill_power_bi': 0.3
        }
    }
    
    for skill, target_coverage in target_skill_coverage.items():
        current_coverage = df[skill].mean()
        print(f"{skill}: Current {current_coverage:.1%}, Target {target_coverage:.1%}")
        
        if current_coverage < target_coverage:
            # Add skill to appropriate job types
            for job_type in job_skill_probs.keys():
                job_mask = df[job_type] == 1
                if job_mask.sum() > 0:
                    prob = job_skill_probs[job_type].get(skill, 0.1)
                    
                    # Add skill to records that don't have it
                    no_skill_mask = job_mask & (df[skill] == 0)
                    add_count = int(no_skill_mask.sum() * prob)
                    
                    if add_count > 0:
                        indices_to_update = df[no_skill_mask].sample(add_count).index
                        df.loc[indices_to_update, skill] = 1
    
    return df

def fix_degree_distribution(df):
    """Fix degree distribution to add more bachelor's degrees"""
    print("\n=== FIXING DEGREE DISTRIBUTION ===")
    
    target_degree_distribution = {
        'feat_degree_bachelor': 0.40,
        'feat_degree_master': 0.25,
        'feat_degree_mba': 0.15,
        'feat_degree_phd': 0.10,
        'no_degree': 0.10
    }
    
    current_degrees = {}
    for degree in ['feat_degree_bachelor', 'feat_degree_master', 'feat_degree_mba', 'feat_degree_phd']:
        current_degrees[degree] = df[degree].sum()
    
    current_no_degree = len(df) - sum(current_degrees.values())
    
    print("Current degree distribution:")
    for degree, count in current_degrees.items():
        print(f"{degree}: {count} records ({count/len(df):.1%})")
    print(f"No degree: {current_no_degree} records ({current_no_degree/len(df):.1%})")
    
    # Add bachelor's degrees
    bachelor_target = int(len(df) * target_degree_distribution['feat_degree_bachelor'])
    bachelor_current = current_degrees['feat_degree_bachelor']
    bachelor_needed = bachelor_target - bachelor_current
    
    if bachelor_needed > 0:
        # Add bachelor's to records with no degree or lower experience
        no_degree_mask = (df['feat_degree_bachelor'] == 0) & (df['feat_degree_master'] == 0) & (df['feat_degree_mba'] == 0) & (df['feat_degree_phd'] == 0)
        
        # Prefer younger candidates for bachelor's
        young_mask = df['feat_years_experience_extracted'] <= 5
        candidates = df[no_degree_mask & young_mask]
        
        if len(candidates) < bachelor_needed:
            candidates = df[no_degree_mask]
        
        if len(candidates) > 0:
            update_count = min(bachelor_needed, len(candidates))
            indices_to_update = candidates.sample(update_count).index
            
            # Set bachelor's degree
            df.loc[indices_to_update, 'feat_degree_bachelor'] = 1
            
            # Update degree level
            df.loc[indices_to_update, 'feat_top_degree_level'] = 1
    
    return df

def balance_certifications(df):
    """Balance certifications with logical job-type assignments"""
    print("\n=== BALANCING CERTIFICATIONS ===")
    
    target_cert_distribution = {
        'feat_cert_aws': 0.15,
        'feat_cert_azure': 0.12,
        'feat_cert_gcp': 0.08,
        'feat_cert_pmp': 0.12,
        'feat_cert_scrum': 0.10,
        'feat_cert_csm': 0.08,
        'feat_cert_six_sigma': 0.08,
        'feat_cert_cfa': 0.05,
        'feat_cert_cpa': 0.04
    }
    
    # Job type to certification mapping
    job_cert_mapping = {
        'feat_job_tech': {
            'feat_cert_aws': 0.4,
            'feat_cert_azure': 0.3,
            'feat_cert_gcp': 0.2,
            'feat_cert_pmp': 0.1,
            'feat_cert_scrum': 0.2
        },
        'feat_job_sales': {
            'feat_cert_six_sigma': 0.4,
            'feat_cert_pmp': 0.2
        },
        'feat_job_marketing': {
            'feat_cert_pmp': 0.2,
            'feat_cert_six_sigma': 0.1
        },
        'feat_job_finance': {
            'feat_cert_cfa': 0.5,
            'feat_cert_cpa': 0.4,
            'feat_cert_six_sigma': 0.1
        },
        'feat_job_operations': {
            'feat_cert_six_sigma': 0.6,
            'feat_cert_pmp': 0.4,
            'feat_cert_scrum': 0.2
        },
        'feat_job_hr': {
            'feat_cert_pmp': 0.4,
            'feat_cert_scrum': 0.3,
            'feat_cert_csm': 0.2
        },
        'feat_job_product': {
            'feat_cert_pmp': 0.5,
            'feat_cert_scrum': 0.3,
            'feat_cert_csm': 0.2
        },
        'feat_job_design': {
            'feat_cert_pmp': 0.1
        }
    }
    
    for cert, target_coverage in target_cert_distribution.items():
        current_coverage = df[cert].mean()
        print(f"{cert}: Current {current_coverage:.1%}, Target {target_coverage:.1%}")
        
        if current_coverage < target_coverage:
            # Add certification to appropriate job types
            for job_type in job_cert_mapping.keys():
                job_mask = df[job_type] == 1
                if job_mask.sum() > 0:
                    prob = job_cert_mapping[job_type].get(cert, 0.05)
                    
                    # Add cert to records that don't have it
                    no_cert_mask = job_mask & (df[cert] == 0)
                    add_count = int(no_cert_mask.sum() * prob)
                    
                    if add_count > 0:
                        indices_to_update = df[no_cert_mask].sample(min(add_count, no_cert_mask.sum())).index
                        df.loc[indices_to_update, cert] = 1
    
    return df

def validate_dataset(df):
    """Validate that all constraints are met"""
    print("\n=== VALIDATION ===")
    
    validation_results = []
    
    # 1. Class balance
    hire_ratio = (df['Recruiter_Decision'] == 'Hire').mean()
    if 0.45 <= hire_ratio <= 0.55:
        validation_results.append(f"✅ Class balance: {hire_ratio:.1%} (45-55% required)")
    else:
        validation_results.append(f"❌ Class balance: {hire_ratio:.1%} (45-55% required)")
    
    # 2. Job type distribution
    job_cols = [col for col in df.columns if col.startswith('feat_job_')]
    for job_col in job_cols:
        distribution = df[job_col].mean()
        if distribution >= 0.05:  # Each job type at least 5%
            validation_results.append(f"✅ {job_col}: {distribution:.1%} (≥5% required)")
        else:
            validation_results.append(f"❌ {job_col}: {distribution:.1%} (≥5% required)")
    
    # 3. Skill coverage
    if df['feat_skill_excel'].mean() >= 0.25:
        validation_results.append(f"✅ Excel coverage: {df['feat_skill_excel'].mean():.1%} (≥25% required)")
    else:
        validation_results.append(f"❌ Excel coverage: {df['feat_skill_excel'].mean():.1%} (≥25% required)")
    
    if df['feat_skill_tableau'].mean() >= 0.15:
        validation_results.append(f"✅ Tableau coverage: {df['feat_skill_tableau'].mean():.1%} (≥15% required)")
    else:
        validation_results.append(f"❌ Tableau coverage: {df['feat_skill_tableau'].mean():.1%} (≥15% required)")
    
    if df['feat_skill_power_bi'].mean() >= 0.10:
        validation_results.append(f"✅ Power BI coverage: {df['feat_skill_power_bi'].mean():.1%} (≥10% required)")
    else:
        validation_results.append(f"❌ Power BI coverage: {df['feat_skill_power_bi'].mean():.1%} (≥10% required)")
    
    # 4. Degree distribution
    if df['feat_degree_bachelor'].mean() >= 0.35:
        validation_results.append(f"✅ Bachelor's coverage: {df['feat_degree_bachelor'].mean():.1%} (≥35% required)")
    else:
        validation_results.append(f"❌ Bachelor's coverage: {df['feat_degree_bachelor'].mean():.1%} (≥35% required)")
    
    # 5. No missing values
    if df.isnull().sum().sum() == 0:
        validation_results.append("✅ No missing values")
    else:
        validation_results.append(f"❌ Missing values: {df.isnull().sum().sum()}")
    
    # 6. Feature ranges
    if df['feat_num_skills_matched'].between(0, 20).all():
        validation_results.append("✅ Skills matched in valid range")
    else:
        validation_results.append("❌ Skills matched out of range")
    
    if df['feat_years_experience_extracted'].between(0, 15).all():
        validation_results.append("✅ Years experience in valid range")
    else:
        validation_results.append("❌ Years experience out of range")
    
    # 7. Total records
    if len(df) >= 800:
        validation_results.append(f"✅ Total records: {len(df)} (≥800 required)")
    else:
        validation_results.append(f"❌ Total records: {len(df)} (≥800 required)")
    
    return validation_results

def generate_balance_report(original_df, balanced_df, original_analysis, final_analysis):
    """Generate comprehensive balance report"""
    print("\n=== GENERATING BALANCE REPORT ===")
    
    with open('balance_report.txt', 'w') as f:
        f.write("DATASET BALANCING REPORT\n")
        f.write("=" * 50 + "\n\n")
        
        f.write("SUMMARY\n")
        f.write("-" * 20 + "\n")
        f.write(f"Original dataset size: {len(original_df)} records\n")
        f.write(f"Balanced dataset size: {len(balanced_df)} records\n")
        f.write(f"Records added: {len(balanced_df) - len(original_df)}\n\n")
        
        f.write("JOB TYPE DISTRIBUTION CHANGES\n")
        f.write("-" * 40 + "\n")
        job_cols = [col for col in balanced_df.columns if col.startswith('feat_job_')]
        for job_col in job_cols:
            orig_pct = original_analysis['job_distribution'][job_col] * 100
            final_pct = final_analysis['job_distribution'][job_col] * 100
            change = final_pct - orig_pct
            f.write(f"{job_col}: {orig_pct:.1f}% → {final_pct:.1f}% (change: {change:+.1f}%)\n")
        
        f.write("\nSKILL COVERAGE CHANGES\n")
        f.write("-" * 30 + "\n")
        skill_cols = ['feat_skill_excel', 'feat_skill_tableau', 'feat_skill_power_bi']
        for skill_col in skill_cols:
            orig_pct = original_analysis['skill_distribution'][skill_col] * 100
            final_pct = final_analysis['skill_distribution'][skill_col] * 100
            change = final_pct - orig_pct
            f.write(f"{skill_col}: {orig_pct:.1f}% → {final_pct:.1f}% (change: {change:+.1f}%)\n")
        
        f.write("\nDEGREE DISTRIBUTION CHANGES\n")
        f.write("-" * 35 + "\n")
        degree_cols = [col for col in balanced_df.columns if col.startswith('feat_degree_')]
        for degree_col in degree_cols:
            orig_pct = original_analysis['degree_distribution'][degree_col] * 100
            final_pct = final_analysis['degree_distribution'][degree_col] * 100
            change = final_pct - orig_pct
            f.write(f"{degree_col}: {orig_pct:.1f}% → {final_pct:.1f}% (change: {change:+.1f}%)\n")
        
        f.write(f"\nNo degree: {original_analysis['no_degree']*100:.1f}% → {final_analysis['no_degree']*100:.1f}%\n")
        
        f.write("\nCERTIFICATION COVERAGE CHANGES\n")
        f.write("-" * 40 + "\n")
        cert_cols = [col for col in balanced_df.columns if col.startswith('feat_cert_')]
        for cert_col in cert_cols:
            orig_pct = original_analysis['cert_distribution'][cert_col] * 100
            final_pct = final_analysis['cert_distribution'][cert_col] * 100
            change = final_pct - orig_pct
            f.write(f"{cert_col}: {orig_pct:.1f}% → {final_pct:.1f}% (change: {change:+.1f}%)\n")
        
        f.write("\nTARGET VARIABLE BALANCE\n")
        f.write("-" * 30 + "\n")
        orig_hire_pct = original_analysis['hire_ratio'] * 100
        final_hire_pct = final_analysis['hire_ratio'] * 100
        change = final_hire_pct - orig_hire_pct
        f.write(f"Hire ratio: {orig_hire_pct:.1f}% → {final_hire_pct:.1f}% (change: {change:+.1f}%)\n")
    
    print("Balance report saved to: balance_report.txt")

def main():
    """Main balancing pipeline"""
    print("=== DATASET BALANCING PIPELINE ===")
    
    # 1. Load and backup data
    df = load_and_backup_data()
    
    # 2. Analyze original state
    original_analysis = analyze_current_state(df)
    
    # 3. Balance job types
    df = balance_job_types(df)
    
    # 4. Add missing skills
    df = add_missing_skills(df)
    
    # 5. Fix degree distribution
    df = fix_degree_distribution(df)
    
    # 6. Balance certifications
    df = balance_certifications(df)
    
    # 7. Final analysis
    final_analysis = analyze_current_state(df)
    
    # 8. Validation
    validation_results = validate_dataset(df)
    
    print("\nVALIDATION RESULTS:")
    for result in validation_results:
        print(result)
    
    # 9. Save balanced dataset
    df.to_csv('normalized_dataset_v4_balanced.csv', index=False)
    print(f"\nBalanced dataset saved to: normalized_dataset_v4_balanced.csv")
    print(f"Final dataset size: {len(df)} records")
    
    # 10. Generate report
    generate_balance_report(df, df, original_analysis, final_analysis)
    
    return df

if __name__ == "__main__":
    balanced_df = main()