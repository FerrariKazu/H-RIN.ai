#!/usr/bin/env python3
"""
Phase 1: Comprehensive Correlation Analysis
Calculate Pearson, Spearman, and Kendall correlation coefficients
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr, spearmanr, kendalltau
import warnings
warnings.filterwarnings('ignore')

# Load the balanced dataset
df = pd.read_csv('pipeline_v4/data/normalized_dataset_v4_balanced.csv')
df['target_binary'] = (df['Recruiter_Decision'] == 'Hire').astype(int)

print("=== COMPREHENSIVE CORRELATION ANALYSIS ===")
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

# Function to calculate all correlation coefficients
def calculate_correlations(df, features, target):
    """Calculate Pearson, Spearman, and Kendall correlations"""
    results = []
    
    for feature in features:
        # Skip if feature has no variance
        if df[feature].std() == 0:
            continue
            
        # Pearson correlation
        pearson_corr, pearson_p = pearsonr(df[feature], df[target])
        
        # Spearman correlation
        spearman_corr, spearman_p = spearmanr(df[feature], df[target])
        
        # Kendall correlation
        kendall_corr, kendall_p = kendalltau(df[feature], df[target])
        
        results.append({
            'feature': feature,
            'pearson_corr': pearson_corr,
            'pearson_p': pearson_p,
            'spearman_corr': spearman_corr,
            'spearman_p': spearman_p,
            'kendall_corr': kendall_corr,
            'kendall_p': kendall_p
        })
    
    return pd.DataFrame(results)

# Calculate correlations for all features
print("\nCalculating correlations for all features...")
all_features = numeric_features + binary_features
correlation_results = calculate_correlations(df, all_features, 'target_binary')

# Sort by absolute Pearson correlation
correlation_results['abs_pearson'] = correlation_results['pearson_corr'].abs()
correlation_results = correlation_results.sort_values('abs_pearson', ascending=False)

print(f"\nCalculated correlations for {len(correlation_results)} features")

# Identify features with |correlation| > 0.3
significant_features = correlation_results[correlation_results['abs_pearson'] > 0.3]
print(f"\nFeatures with |correlation| > 0.3: {len(significant_features)}")

# Display top 15 features by correlation
print("\n=== TOP 15 FEATURES BY CORRELATION ===")
for i, row in correlation_results.head(15).iterrows():
    print(f"{row['feature']:25} | Pearson: {row['pearson_corr']:6.3f} | Spearman: {row['spearman_corr']:6.3f} | Kendall: {row['kendall_corr']:6.3f}")

# Save correlation results
correlation_results.to_csv('pipeline_v4/plots/correlation_analysis_results.csv', index=False)
print(f"\nCorrelation results saved to: pipeline_v4/plots/correlation_analysis_results.csv")

# Create correlation matrices
print("\nCreating correlation matrices...")

# Prepare data for matrix visualization
feature_data = df[all_features + ['target_binary']]
correlation_matrix_pearson = feature_data.corr(method='pearson')
correlation_matrix_spearman = feature_data.corr(method='spearman')
correlation_matrix_kendall = feature_data.corr(method='kendall')

# Create comprehensive correlation heatmap
fig, axes = plt.subplots(2, 2, figsize=(20, 16))

# Pearson correlation heatmap
sns.heatmap(correlation_matrix_pearson, annot=False, cmap='RdBu_r', center=0, 
            square=True, ax=axes[0,0], cbar_kws={'shrink': 0.8})
axes[0,0].set_title('Pearson Correlation Matrix', fontsize=14, fontweight='bold')

# Spearman correlation heatmap
sns.heatmap(correlation_matrix_spearman, annot=False, cmap='RdBu_r', center=0, 
            square=True, ax=axes[0,1], cbar_kws={'shrink': 0.8})
axes[0,1].set_title('Spearman Correlation Matrix', fontsize=14, fontweight='bold')

# Kendall correlation heatmap
sns.heatmap(correlation_matrix_kendall, annot=False, cmap='RdBu_r', center=0, 
            square=True, ax=axes[1,0], cbar_kws={'shrink': 0.8})
axes[1,0].set_title('Kendall Correlation Matrix', fontsize=14, fontweight='bold')

# Target correlations only
target_correlations = pd.DataFrame({
    'Pearson': correlation_matrix_pearson['target_binary'].drop('target_binary'),
    'Spearman': correlation_matrix_spearman['target_binary'].drop('target_binary'),
    'Kendall': correlation_matrix_kendall['target_binary'].drop('target_binary')
})

# Sort by absolute Pearson correlation
target_correlations['abs_pearson'] = target_correlations['Pearson'].abs()
target_correlations = target_correlations.sort_values('abs_pearson', ascending=False)

# Plot top 20 correlations with target
top_20_target = target_correlations.head(20)
top_20_target[['Pearson', 'Spearman', 'Kendall']].plot(kind='barh', ax=axes[1,1])
axes[1,1].set_title('Top 20 Features by Target Correlation', fontsize=14, fontweight='bold')
axes[1,1].set_xlabel('Correlation Coefficient')
axes[1,1].legend()

plt.tight_layout()
plt.savefig('pipeline_v4/plots/comprehensive_correlation_analysis.png', dpi=300, bbox_inches='tight')
plt.close()
print("Comprehensive correlation heatmaps saved to: pipeline_v4/plots/comprehensive_correlation_analysis.png")

# Create focused heatmap for top correlated features
top_features = target_correlations.head(15).index.tolist() + ['target_binary']
focused_matrix = correlation_matrix_pearson.loc[top_features, top_features]

plt.figure(figsize=(12, 10))
sns.heatmap(focused_matrix, annot=True, cmap='RdBu_r', center=0, 
            square=True, fmt='.2f', cbar_kws={'shrink': 0.8})
plt.title('Focused Correlation Matrix - Top 15 Features', fontsize=16, fontweight='bold')
plt.xticks(rotation=45, ha='right')
plt.yticks(rotation=0)
plt.tight_layout()
plt.savefig('pipeline_v4/plots/focused_correlation_heatmap.png', dpi=300, bbox_inches='tight')
plt.close()
print("Focused correlation heatmap saved to: pipeline_v4/plots/focused_correlation_heatmap.png")

# Detailed analysis of significant features
print("\n=== DETAILED ANALYSIS OF SIGNIFICANT FEATURES (|correlation| > 0.3) ===")
for i, row in significant_features.iterrows():
    print(f"\n{row['feature']}:")
    print(f"  Pearson:  {row['pearson_corr']:7.3f} (p={row['pearson_p']:.3f})")
    print(f"  Spearman: {row['spearman_corr']:7.3f} (p={row['spearman_p']:.3f})")
    print(f"  Kendall:  {row['kendall_corr']:7.3f} (p={row['kendall_p']:.3f})")

print(f"\n=== CORRELATION ANALYSIS COMPLETE ===")
print(f"Total features analyzed: {len(correlation_results)}")
print(f"Features with |correlation| > 0.3: {len(significant_features)}")
print(f"Top correlation coefficient: {correlation_results.iloc[0]['pearson_corr']:.3f}")
print(f"Plots saved to: pipeline_v4/plots/")