#!/usr/bin/env python3
"""
Phase 1: Exploratory Data Analysis with Visualizations
Create comprehensive visualizations showing feature distributions by class
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Load the balanced dataset
df = pd.read_csv('pipeline_v4/data/normalized_dataset_v4_balanced.csv')
df['target_binary'] = (df['Recruiter_Decision'] == 'Hire').astype(int)

print("=== EXPLORATORY DATA ANALYSIS WITH VISUALIZATIONS ===")
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

# Get top predictive features from previous analysis
correlation_results = pd.read_csv('pipeline_v4/plots/correlation_analysis_results.csv')
top_features = correlation_results.head(15)['feature'].tolist()

# Create comprehensive visualization suite - FIXED SUBPLOT LAYOUT
fig = plt.figure(figsize=(20, 18))

# 1. Numeric features - Box plots (positions 1-6)
print("\nCreating numeric features box plots...")
numeric_top = [f for f in top_features if f in numeric_features][:6]

for i, feature in enumerate(numeric_top):
    ax = plt.subplot(6, 4, i+1)
    
    # Create box plot
    hire_data = df[df['target_binary'] == 1][feature]
    reject_data = df[df['target_binary'] == 0][feature]
    
    box_data = [reject_data, hire_data]
    box_plot = ax.boxplot(box_data, labels=['Reject', 'Hire'], patch_artist=True)
    
    # Color the boxes
    colors = ['lightcoral', 'lightgreen']
    for patch, color in zip(box_plot['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax.set_title(f'{feature}', fontsize=10, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # Add statistical test result
    t_stat, p_val = stats.ttest_ind(hire_data, reject_data)
    significance = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "ns"
    ax.text(0.02, 0.98, f'p={p_val:.3f} {significance}', transform=ax.transAxes, 
            verticalalignment='top', fontsize=8, bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

# 2. Numeric features - Histograms with overlays (positions 7-12)
print("Creating numeric features histograms...")
for i, feature in enumerate(numeric_top):
    ax = plt.subplot(6, 4, i+7)
    
    # Create overlapping histograms
    hire_data = df[df['target_binary'] == 1][feature]
    reject_data = df[df['target_binary'] == 0][feature]
    
    axes[0,1].hist(reject_data, bins=20, alpha=0.6, color='lightcoral', label='Reject', density=True)
    axes[0,1].hist(hire_data, bins=20, alpha=0.6, color='lightgreen', label='Hire', density=True)
    axes[0,1].set_title(f'{feature} Distribution')
    axes[0,1].legend()
    axes[0,1].grid(True, alpha=0.3)

# 3. Binary features - Bar plots (positions 13-18)
print("Creating binary features bar plots...")
binary_top = [f for f in top_features if f in binary_features][:6]

for i, feature in enumerate(binary_top):
    ax = plt.subplot(6, 4, i+13)
    
    # Calculate proportions
    contingency = pd.crosstab(df[feature], df['target_binary'], normalize='index')
    
    contingency.plot(kind='bar', ax=ax, color=['lightcoral', 'lightgreen'], alpha=0.7)
    ax.set_title(f'{feature}', fontsize=10, fontweight='bold')
    ax.legend(['Reject', 'Hire'])
    ax.set_xlabel('Feature Value')
    ax.set_ylabel('Proportion')
    ax.grid(True, alpha=0.3)
    plt.setp(ax.get_xticklabels(), rotation=0)

# 4. Binary features - Stacked bar plots (positions 19-24)
print("Creating binary features stacked bar plots...")
for i, feature in enumerate(binary_top):
    ax = plt.subplot(6, 4, i+19)
    
    # Calculate counts
    contingency_counts = pd.crosstab(df[feature], df['target_binary'])
    
    contingency_counts.plot(kind='bar', stacked=True, ax=ax, 
                             color=['lightcoral', 'lightgreen'], alpha=0.7)
    ax.set_title(f'{feature} Counts', fontsize=10, fontweight='bold')
    ax.legend(['Reject', 'Hire'])
    ax.set_xlabel('Feature Value')
    ax.set_ylabel('Count')
    ax.grid(True, alpha=0.3)
    plt.setp(ax.get_xticklabels(), rotation=0)

plt.tight_layout()
plt.savefig('pipeline_v4/plots/comprehensive_eda_analysis.png', dpi=300, bbox_inches='tight')
plt.close()
print("Comprehensive EDA analysis saved to: pipeline_v4/plots/comprehensive_eda_analysis.png")

# Create separate figure for correlation heatmap
fig2, ax = plt.subplots(1, 1, figsize=(12, 10))

# Select top features for heatmap
top_10_features = top_features[:10] + ['target_binary']
heatmap_data = df[top_10_features].corr()

sns.heatmap(heatmap_data, annot=True, cmap='RdBu_r', center=0, 
            square=True, fmt='.2f', cbar_kws={'shrink': 0.8})
ax.set_title('Top 10 Features Correlation Matrix', fontsize=14, fontweight='bold')
plt.xticks(rotation=45, ha='right')
plt.yticks(rotation=0)
plt.tight_layout()
plt.savefig('pipeline_v4/plots/focused_correlation_heatmap.png', dpi=300, bbox_inches='tight')
plt.close()
print("Focused correlation heatmap saved to: pipeline_v4/plots/focused_correlation_heatmap.png")

# Create separate figure for feature importance comparison
fig3, ax = plt.subplots(1, 1, figsize=(10, 8))

# Load correlation results
correlation_results = pd.read_csv('pipeline_v4/plots/correlation_analysis_results.csv')
correlation_results['abs_corr'] = correlation_results['pearson_corr'].abs()
top_corr = correlation_results.nlargest(10, 'abs_corr')

# Load statistical results
statistical_results = pd.read_csv('pipeline_v4/plots/statistical_tests_results.csv')
statistical_results['abs_effect'] = statistical_results['effect_size'].abs()
top_stat = statistical_results.nlargest(10, 'abs_effect')

# Plot comparison
x_pos = np.arange(len(top_corr))
width = 0.35

ax.bar(x_pos - width/2, top_corr['abs_corr'], width, label='Correlation', alpha=0.7, color='skyblue')
ax.bar(x_pos + width/2, top_stat['abs_effect'], width, label='Effect Size', alpha=0.7, color='orange')

ax.set_xlabel('Feature Rank')
ax.set_ylabel('Importance Score')
ax.set_title('Feature Importance Comparison: Correlation vs Effect Size')
ax.set_xticks(x_pos)
ax.set_xticklabels([f"{i+1}" for i in range(len(top_corr))])
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('pipeline_v4/plots/feature_importance_comparison.png', dpi=300, bbox_inches='tight')
plt.close()
print("Feature importance comparison saved to: pipeline_v4/plots/feature_importance_comparison.png")

# Create individual feature analysis plots for top features
print("\nCreating individual feature analysis for top 5 features...")

top_5_features = top_features[:5]

for i, feature in enumerate(top_5_features):
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    hire_data = df[df['target_binary'] == 1][feature]
    reject_data = df[df['target_binary'] == 0][feature]
    
    if feature in numeric_features:
        # Box plot
        axes[0,0].boxplot([reject_data, hire_data], labels=['Reject', 'Hire'], 
                         patch_artist=True, boxprops=dict(facecolor='lightblue', alpha=0.7))
        axes[0,0].set_title(f'{feature} - Box Plot')
        axes[0,0].grid(True, alpha=0.3)
        
        # Histogram
        axes[0,1].hist(reject_data, bins=20, alpha=0.6, color='lightcoral', label='Reject', density=True)
        axes[0,1].hist(hire_data, bins=20, alpha=0.6, color='lightgreen', label='Hire', density=True)
        axes[0,1].set_title(f'{feature} Distribution')
        axes[0,1].legend()
        axes[0,1].grid(True, alpha=0.3)
        
        # Violin plot
        data_for_violin = [reject_data, hire_data]
        parts = axes[1,0].violinplot(data_for_violin, positions=[1, 2], showmeans=True, showmedians=True)
        for pc, color in zip(parts['bodies'], ['lightcoral', 'lightgreen']):
            pc.set_facecolor(color)
            pc.set_alpha(0.7)
        axes[1,0].set_xticks([1, 2])
        axes[1,0].set_xticklabels(['Reject', 'Hire'])
        axes[1,0].set_title(f'{feature} - Violin Plot')
        axes[1,0].grid(True, alpha=0.3)
        
        # Q-Q plot
        stats.probplot(reject_data, dist="norm", plot=axes[1,1])
        axes[1,1].set_title(f'{feature} - Q-Q Plot (Reject)')
        axes[1,1].grid(True, alpha=0.3)
        
    else:  # Binary feature
        # Bar plot of proportions
        contingency = pd.crosstab(df[feature], df['target_binary'], normalize='index')
        contingency.plot(kind='bar', ax=axes[0,0], color=['lightcoral', 'lightgreen'], alpha=0.7)
        axes[0,0].set_title(f'{feature} - Proportions')
        axes[0,0].legend(['Reject', 'Hire'])
        axes[0,0].grid(True, alpha=0.3)
        
        # Stacked bar plot
        contingency_counts = pd.crosstab(df[feature], df['target_binary'])
        contingency_counts.plot(kind='bar', stacked=True, ax=axes[0,1], 
                               color=['lightcoral', 'lightgreen'], alpha=0.7)
        axes[0,1].set_title(f'{feature} - Stacked Counts')
        axes[0,1].legend(['Reject', 'Hire'])
        axes[0,1].grid(True, alpha=0.3)
        
        # Chi-square test visualization
        chi2, p_val, dof, expected = stats.chi2_contingency(contingency_counts)
        im = axes[1,0].imshow(expected, cmap='Blues', alpha=0.7)
        axes[1,0].set_title(f'{feature} - Expected vs Observed\n(χ²={chi2:.2f}, p={p_val:.3f})')
        axes[1,0].set_xticks([0, 1])
        axes[1,0].set_xticklabels(['Reject', 'Hire'])
        axes[1,0].set_yticks([0, 1])
        axes[1,0].set_yticklabels(['0', '1'])
        
        # Effect size visualization
        cramers_v = np.sqrt(chi2 / (contingency_counts.sum().sum() * (min(contingency_counts.shape) - 1)))
        axes[1,1].bar(['Cramér\'s V'], [cramers_v], color='orange', alpha=0.7)
        axes[1,1].set_title(f'{feature} - Effect Size\n(Cramér\'s V = {cramers_v:.3f})')
        axes[1,1].set_ylabel('Effect Size')
        axes[1,1].grid(True, alpha=0.3)
    
    plt.suptitle(f'Detailed Analysis: {feature}', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f'pipeline_v4/plots/detailed_{feature.replace("(", "").replace(")", "").replace(" ", "_")}_analysis.png', 
                dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Detailed analysis for {feature} saved to: pipeline_v4/plots/detailed_{feature.replace('(', '').replace(')', '').replace(' ', '_')}_analysis.png")

print(f"\n=== EXPLORATORY DATA ANALYSIS COMPLETE ===")
print(f"Created comprehensive visualization suite")
print(f"Individual feature analyses for top 5 features")
print(f"All plots saved to: pipeline_v4/plots/")