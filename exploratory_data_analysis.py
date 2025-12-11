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

# Create comprehensive visualization suite
fig = plt.figure(figsize=(20, 24))

# 1. Numeric features - Box plots
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

# 2. Numeric features - Histograms with overlays
print("Creating numeric features histograms...")
for i, feature in enumerate(numeric_top):
    ax = plt.subplot(6, 4, i+7)
    
    # Create overlapping histograms
    hire_data = df[df['target_binary'] == 1][feature]
    reject_data = df[df['target_binary'] == 0][feature]
    
    ax.hist(reject_data, bins=20, alpha=0.6, color='lightcoral', label='Reject', density=True)
    ax.hist(hire_data, bins=20, alpha=0.6, color='lightgreen', label='Hire', density=True)
    
    ax.set_title(f'{feature} Distribution', fontsize=10, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

# 3. Binary features - Bar plots
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

# 4. Binary features - Stacked bar plots
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

# 5. Correlation heatmap
print("Creating correlation heatmap...")
ax = plt.subplot(6, 4, 25)

# Select top features for heatmap
top_10_features = top_features[:10] + ['target_binary']
heatmap_data = df[top_10_features].corr()

sns.heatmap(heatmap_data, annot=True, cmap='RdBu_r', center=0, 
            square=True, fmt='.2f', cbar_kws={'shrink': 0.8})
ax.set_title('Top 10 Features Correlation Matrix', fontsize=10, fontweight='bold')

# 6. Feature importance comparison
print("Creating feature importance comparison...")
ax = plt.subplot(6, 4, 26)

# Load correlation results
correlation_results = pd.read_csv('pipeline_v4/plots/correlation_analysis_results.csv')
correlation_results['abs_corr'] = correlation_results['pearson_corr'].abs()
top_corr = correlation_results.nlargest(10, 'abs_corr')

# Load statistical results
statistical_results = pd.read_csv('pipeline_v4/plots/statistical_tests_results.csv')
statistical_results['abs_effect'] = statistical_results['effect_size'].abs()
top_stat = statistical_results.nlargest(10, 'abs_effect')

# Plot comparison
methods = ['Correlation', 'Effect Size']
features_corr = top_corr['feature'].tolist()
features_stat = top_stat['feature'].tolist()

# Create comparison data
comparison_data = []
for i, (corr_feat, stat_feat) in enumerate(zip(features_corr, features_stat)):
    comparison_data.append({
        'rank': i+1,
        'correlation_feature': corr_feat,
        'correlation_value': top_corr.iloc[i]['abs_corr'],
        'statistical_feature': stat_feat,
        'statistical_value': top_stat.iloc[i]['abs_effect']
    })

y_pos = np.arange(len(comparison_data))
ax.barh(y_pos, [d['correlation_value'] for d in comparison_data], 
        alpha=0.7, color='skyblue', label='Correlation')
ax.barh(y_pos, [d['statistical_value'] for d in comparison_data], 
        alpha=0.7, color='orange', label='Effect Size')

ax.set_yticks(y_pos)
ax.set_yticklabels([f"{i+1}" for i in range(len(comparison_data))])
ax.set_xlabel('Importance Score')
ax.set_title('Feature Importance Comparison', fontsize=10, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3)

# 7. Distribution comparison for top feature
print("Creating distribution comparison for top feature...")
ax = plt.subplot(6, 4, 27)

top_feature = top_features[0]
hire_data = df[df['target_binary'] == 1][top_feature]
reject_data = df[df['target_binary'] == 0][top_feature]

if top_feature in numeric_features:
    ax.hist(reject_data, bins=30, alpha=0.6, color='lightcoral', label='Reject', density=True)
    ax.hist(hire_data, bins=30, alpha=0.6, color='lightgreen', label='Hire', density=True)
    ax.set_title(f'{top_feature} Distribution Comparison', fontsize=10, fontweight='bold')
else:
    # For binary features, show proportions
    contingency = pd.crosstab(df[top_feature], df['target_binary'], normalize='index')
    contingency.plot(kind='bar', ax=ax, color=['lightcoral', 'lightgreen'], alpha=0.7)
    ax.set_title(f'{top_feature} Proportion Comparison', fontsize=10, fontweight='bold')

ax.legend()
ax.grid(True, alpha=0.3)

# 8. Statistical summary
print("Creating statistical summary...")
ax = plt.subplot(6, 4, 28)

# Summary statistics
stats_summary = {
    'Total Records': len(df),
    'Hire Count': (df['target_binary'] == 1).sum(),
    'Reject Count': (df['target_binary'] == 0).sum(),
    'Hire %': f"{(df['target_binary'] == 1).mean() * 100:.1f}%",
    'Numeric Features': len(numeric_features),
    'Binary Features': len(binary_features),
    'Total Features': len(numeric_features) + len(binary_features)
}

# Create text summary
text_content = "Dataset Summary:\n"
for key, value in stats_summary.items():
    text_content += f"{key}: {value}\n"

ax.text(0.1, 0.9, text_content, transform=ax.transAxes, fontsize=10, 
        verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')
ax.set_title('Statistical Summary', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig('pipeline_v4/plots/comprehensive_eda_analysis.png', dpi=300, bbox_inches='tight')
plt.close()
print("Comprehensive EDA analysis saved to: pipeline_v4/plots/comprehensive_eda_analysis.png")

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
        axes[0,1].set_title(f'{feature} - Distribution')
        axes[0,1].legend()
        axes[0,1].grid(True, alpha=0.3)
        
        # Violin plot
        data_for_violin = [reject_data, hire_data]
        axes[1,0].violinplot(data_for_violin, positions=[1, 2], showmeans=True, showmedians=True)
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
        axes[1,0].imshow(expected, cmap='Blues', alpha=0.7)
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