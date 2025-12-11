#!/usr/bin/env python3
"""
Phase 1: Feature Predictive Power Assessment
Conduct univariate statistical tests and calculate mutual information scores
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.feature_selection import mutual_info_classif
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Load the balanced dataset
df = pd.read_csv('pipeline_v4/data/normalized_dataset_v4_balanced.csv')
df['target_binary'] = (df['Recruiter_Decision'] == 'Hire').astype(int)

print("=== FEATURE PREDICTIVE POWER ASSESSMENT ===")
print(f"Dataset shape: {df.shape}")

# Identify feature types
numeric_features = []
binary_features = []
target_col = 'target_binary'

for col in df.columns:
    if col in ['Recruiter_Decision', 'target_binary']:
        continue
    elif df[col].dtype in ['int64', 'float64']:
        if df[col].nunique() <= 2 and set(df[col].unique()).issubset({0, 1}):
            binary_features.append(col)
        else:
            numeric_features.append(col)

print(f"\nFeature breakdown:")
print(f"Numeric features: {len(numeric_features)}")
print(f"Binary features: {len(binary_features)}")

# Function to perform univariate statistical tests
def perform_univariate_tests(df, features, target_col):
    """Perform t-tests for numeric and chi-square for binary features"""
    results = []
    
    for feature in features:
        feature_data = df[feature]
        target_data = df[target_col]
        
        # Determine if feature is numeric or binary
        if feature in numeric_features:
            # Separate data by target class
            hire_group = feature_data[target_data == 1]
            reject_group = feature_data[target_data == 0]
            
            # Perform independent t-test
            t_stat, p_value = stats.ttest_ind(hire_group, reject_group)
            
            # Calculate effect size (Cohen's d)
            pooled_std = np.sqrt(((len(hire_group) - 1) * hire_group.var() + 
                                 (len(reject_group) - 1) * reject_group.var()) / 
                                (len(hire_group) + len(reject_group) - 2))
            cohens_d = (hire_group.mean() - reject_group.mean()) / pooled_std
            
            # Calculate means for each group
            hire_mean = hire_group.mean()
            reject_mean = reject_group.mean()
            
            results.append({
                'feature': feature,
                'feature_type': 'numeric',
                'test_type': 't-test',
                'statistic': t_stat,
                'p_value': p_value,
                'effect_size': cohens_d,
                'hire_mean': hire_mean,
                'reject_mean': reject_mean,
                'significant': p_value < 0.05
            })
            
        elif feature in binary_features:
            # Create contingency table
            contingency_table = pd.crosstab(feature_data, target_data)
            
            # Perform chi-square test
            chi2_stat, p_value, dof, expected = stats.chi2_contingency(contingency_table)
            
            # Calculate Cramér's V as effect size
            n = contingency_table.sum().sum()
            cramers_v = np.sqrt(chi2_stat / (n * (min(contingency_table.shape) - 1)))
            
            # Calculate proportions for each group
            hire_prop = contingency_table[1].sum() / contingency_table.sum().sum() if 1 in contingency_table.columns else 0
            reject_prop = contingency_table[0].sum() / contingency_table.sum().sum() if 0 in contingency_table.columns else 0
            
            results.append({
                'feature': feature,
                'feature_type': 'binary',
                'test_type': 'chi-square',
                'statistic': chi2_stat,
                'p_value': p_value,
                'effect_size': cramers_v,
                'hire_mean': hire_prop,
                'reject_mean': reject_prop,
                'significant': p_value < 0.05
            })
    
    return pd.DataFrame(results)

# Function to calculate mutual information
def calculate_mutual_information(df, features, target_col):
    """Calculate mutual information scores"""
    # Prepare data for mutual information
    X = df[features]
    y = df[target_col]
    
    # Calculate mutual information
    mi_scores = mutual_info_classif(X, y, random_state=42)
    
    # Create results dataframe
    mi_results = pd.DataFrame({
        'feature': features,
        'mutual_info': mi_scores
    })
    
    return mi_results

# Perform univariate tests
print("\nPerforming univariate statistical tests...")
all_features = numeric_features + binary_features
statistical_results = perform_univariate_tests(df, all_features, 'target_binary')

# Perform mutual information calculation
print("Calculating mutual information scores...")
mutual_info_results = calculate_mutual_information(df, all_features, 'target_binary')

# Merge results
combined_results = statistical_results.merge(mutual_info_results, on='feature', how='left')

# Sort by effect size (absolute value for numeric, direct for binary)
combined_results['abs_effect_size'] = combined_results['effect_size'].abs()
combined_results = combined_results.sort_values('abs_effect_size', ascending=False)

print(f"\n=== TOP 15 FEATURES BY EFFECT SIZE ===")
print(f"{'Feature':<30} | {'Type':<8} | {'Effect Size':<12} | {'P-value':<10} | {'Mutual Info':<12}")
print("-" * 80)

for i, row in combined_results.head(15).iterrows():
    print(f"{row['feature']:<30} | {row['feature_type']:<8} | {row['effect_size']:<12.3f} | {row['p_value']:<10.3e} | {row['mutual_info']:<12.3f}")

# Save results
combined_results.to_csv('pipeline_v4/plots/statistical_tests_results.csv', index=False)
print(f"\nStatistical test results saved to: pipeline_v4/plots/statistical_tests_results.csv")

# Create visualization of top features
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Top 10 by effect size
top_10_effect = combined_results.head(10)
colors = ['red' if not sig else 'green' for sig in top_10_effect['significant']]

axes[0,0].barh(range(len(top_10_effect)), top_10_effect['abs_effect_size'], color=colors)
axes[0,0].set_yticks(range(len(top_10_effect)))
axes[0,0].set_yticklabels(top_10_effect['feature'], fontsize=8)
axes[0,0].set_xlabel('Effect Size (Absolute Value)')
axes[0,0].set_title('Top 10 Features by Effect Size')
axes[0,0].grid(True, alpha=0.3)

# Top 10 by mutual information
top_10_mi = combined_results.nlargest(10, 'mutual_info')
axes[0,1].barh(range(len(top_10_mi)), top_10_mi['mutual_info'], color='skyblue')
axes[0,1].set_yticks(range(len(top_10_mi)))
axes[0,1].set_yticklabels(top_10_mi['feature'], fontsize=8)
axes[0,1].set_xlabel('Mutual Information Score')
axes[0,1].set_title('Top 10 Features by Mutual Information')
axes[0,1].grid(True, alpha=0.3)

# P-value distribution
axes[1,0].hist(combined_results['p_value'], bins=30, alpha=0.7, color='orange')
axes[1,0].axvline(x=0.05, color='red', linestyle='--', label='α = 0.05')
axes[1,0].set_xlabel('P-value')
axes[1,0].set_ylabel('Frequency')
axes[1,0].set_title('P-value Distribution')
axes[1,0].legend()
axes[1,0].grid(True, alpha=0.3)

# Effect size vs Mutual Information scatter
significant_features = combined_results[combined_results['significant']]
non_significant = combined_results[~combined_results['significant']]

axes[1,1].scatter(significant_features['abs_effect_size'], significant_features['mutual_info'], 
                 alpha=0.7, color='green', label='Significant', s=30)
axes[1,1].scatter(non_significant['abs_effect_size'], non_significant['mutual_info'], 
                 alpha=0.7, color='red', label='Non-significant', s=30)
axes[1,1].set_xlabel('Effect Size (Absolute)')
axes[1,1].set_ylabel('Mutual Information')
axes[1,1].set_title('Effect Size vs Mutual Information')
axes[1,1].legend()
axes[1,1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('pipeline_v4/plots/predictive_power_analysis.png', dpi=300, bbox_inches='tight')
plt.close()
print("Predictive power analysis plots saved to: pipeline_v4/plots/predictive_power_analysis.png")

# Detailed analysis of top predictive features
print("\n=== DETAILED ANALYSIS OF TOP PREDICTIVE FEATURES ===")

print("\nTop 5 by Effect Size:")
for i, row in combined_results.head(5).iterrows():
    print(f"\n{i+1}. {row['feature']} ({row['feature_type']}):")
    print(f"   Effect Size: {row['effect_size']:.3f}")
    print(f"   P-value: {row['p_value']:.3e}")
    print(f"   Mutual Information: {row['mutual_info']:.3f}")
    if row['feature_type'] == 'numeric':
        print(f"   Hire Mean: {row['hire_mean']:.3f}, Reject Mean: {row['reject_mean']:.3f}")
    else:
        print(f"   Hire Proportion: {row['hire_mean']:.3f}, Reject Proportion: {row['reject_mean']:.3f}")

# Summary statistics
print(f"\n=== SUMMARY STATISTICS ===")
print(f"Total features tested: {len(combined_results)}")
print(f"Significant features (p < 0.05): {combined_results['significant'].sum()}")
print(f"Percentage significant: {(combined_results['significant'].sum() / len(combined_results)) * 100:.1f}%")
print(f"Mean effect size: {combined_results['abs_effect_size'].mean():.3f}")
print(f"Max effect size: {combined_results['abs_effect_size'].max():.3f}")
print(f"Mean mutual information: {combined_results['mutual_info'].mean():.3f}")
print(f"Max mutual information: {combined_results['mutual_info'].max():.3f}")

print(f"\n=== PREDICTIVE POWER ASSESSMENT COMPLETE ===")