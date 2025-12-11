#!/usr/bin/env python3
"""
Phase 2: Feature Engineering and Preparation
Create powerful combined features and prepare data for modeling
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.feature_selection import SelectKBest, f_classif, RFE
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import mutual_info_score
import warnings
warnings.filterwarnings('ignore')

# Load the balanced dataset
df = pd.read_csv('pipeline_v4/data/normalized_dataset_v4_balanced.csv')
df['target_binary'] = (df['Recruiter_Decision'] == 'Hire').astype(int)

print("=== PHASE 2: FEATURE ENGINEERING AND PREPARATION ===")
print(f"Original dataset shape: {df.shape}")

# Identify feature types
numeric_features = []
binary_features = []
categorical_features = []
target_col = 'target_binary'

for col in df.columns:
    if col in ['Recruiter_Decision', 'target_binary']:
        continue
    elif df[col].dtype in ['int64', 'float64']:
        if df[col].nunique() <= 2 and set(df[col].unique()).issubset({0, 1}):
            binary_features.append(col)
        else:
            numeric_features.append(col)
    else:
        categorical_features.append(col)

print(f"\nFeature breakdown:")
print(f"Numeric features: {len(numeric_features)}")
print(f"Binary features: {len(binary_features)}")
print(f"Categorical features: {len(categorical_features)}")

# 1. FEATURE ENGINEERING
print("\n=== 1. CREATING COMBINED FEATURES ===")

# Create a copy for feature engineering
df_engineered = df.copy()

# 1.1 Interaction terms between top predictive features
print("Creating interaction terms...")

# Get top features from correlation analysis
correlation_results = pd.read_csv('pipeline_v4/plots/correlation_analysis_results.csv')
top_features = correlation_results.head(10)['feature'].tolist()

# Create interaction terms for top numeric features
numeric_top = [f for f in top_features if f in numeric_features][:5]
for i in range(len(numeric_top)):
    for j in range(i+1, len(numeric_top)):
        feat1, feat2 = numeric_top[i], numeric_top[j]
        interaction_name = f"interaction_{feat1.replace(' ', '_')}_{feat2.replace(' ', '_')}"
        df_engineered[interaction_name] = df_engineered[feat1] * df_engineered[feat2]

# 1.2 Ratio-based features
print("Creating ratio-based features...")

# Experience to skills ratio
if 'feat_years_experience_extracted' in df_engineered.columns and 'feat_num_skills_matched' in df_engineered.columns:
    df_engineered['ratio_experience_to_skills'] = df_engineered['feat_years_experience_extracted'] / (df_engineered['feat_num_skills_matched'] + 1)

# Salary to experience ratio
if 'feat_salary_extracted' in df_engineered.columns and 'feat_years_experience_extracted' in df_engineered.columns:
    df_engineered['ratio_salary_to_experience'] = df_engineered['feat_salary_extracted'] / (df_engineered['feat_years_experience_extracted'] + 1)

# Text length to skills ratio
if 'text_len' in df_engineered.columns and 'feat_num_skills_matched' in df_engineered.columns:
    df_engineered['ratio_text_to_skills'] = df_engineered['text_len'] / (df_engineered['feat_num_skills_matched'] + 1)

# 1.3 Polynomial features for continuous variables
print("Creating polynomial features...")

continuous_vars = ['feat_years_experience_extracted', 'feat_num_skills_matched', 'feat_salary_extracted', 'text_len']
for var in continuous_vars:
    if var in df_engineered.columns:
        df_engineered[f"{var}_squared"] = df_engineered[var] ** 2
        df_engineered[f"{var}_cubed"] = df_engineered[var] ** 3
        df_engineered[f"{var}_sqrt"] = np.sqrt(df_engineered[var] + 1)  # +1 to avoid negative values

# 1.4 Domain-specific feature combinations
print("Creating domain-specific combinations...")

# Tech skill combinations
tech_skills = ['feat_skill_python', 'feat_skill_sql', 'feat_skill_machine_learning', 'feat_skill_deep_learning']
available_tech_skills = [skill for skill in tech_skills if skill in df_engineered.columns]
if len(available_tech_skills) >= 2:
    df_engineered['tech_skill_count'] = df_engineered[available_tech_skills].sum(axis=1)
    df_engineered['tech_skill_ratio'] = df_engineered['tech_skill_count'] / len(available_tech_skills)

# Management skill combinations
mgmt_skills = ['feat_skill_project_management', 'feat_cert_pmp', 'feat_cert_scrum', 'feat_cert_csm']
available_mgmt_skills = [skill for skill in mgmt_skills if skill in df_engineered.columns]
if len(available_mgmt_skills) >= 2:
    df_engineered['mgmt_skill_count'] = df_engineered[available_mgmt_skills].sum(axis=1)

# Certification combinations
certifications = [col for col in df_engineered.columns if col.startswith('feat_cert_')]
if certifications:
    df_engineered['total_certifications'] = df_engineered[certifications].sum(axis=1)
    df_engineered['certification_ratio'] = df_engineered['total_certifications'] / len(certifications)

# Job type combinations
job_types = [col for col in df_engineered.columns if col.startswith('feat_job_')]
if job_types:
    df_engineered['job_type_count'] = df_engineered[job_types].sum(axis=1)

print(f"Feature engineering complete. New shape: {df_engineered.shape}")
print(f"New features created: {df_engineered.shape[1] - df.shape[1]}")

# 2. FEATURE SELECTION
print("\n=== 2. FEATURE SELECTION PROCESS ===")

# Prepare data for feature selection
X = df_engineered.drop(['Recruiter_Decision', 'target_binary'], axis=1)
y = df_engineered['target_binary']

print(f"Features before selection: {X.shape[1]}")

# 2.1 Univariate feature selection
print("Performing univariate feature selection...")
selector = SelectKBest(score_func=f_classif, k=30)
X_selected_univariate = selector.fit_transform(X, y)
selected_features_univariate = X.columns[selector.get_support()].tolist()

print(f"Top 30 features by univariate selection: {len(selected_features_univariate)}")

# 2.2 Mutual Information
print("Calculating mutual information scores...")
mi_scores = mutual_info_classif(X, y, random_state=42)
mi_results = pd.DataFrame({'feature': X.columns, 'mi_score': mi_scores})
mi_results = mi_results.sort_values('mi_score', ascending=False)
top_mi_features = mi_results.head(30)['feature'].tolist()

# 2.3 Recursive Feature Elimination
print("Performing recursive feature elimination...")
# Use a simple model for RFE
rfe_model = LogisticRegression(random_state=42, max_iter=1000)
rfe = RFE(estimator=rfe_model, n_features_to_select=30, step=1)
X_selected_rfe = rfe.fit_transform(X, y)
selected_features_rfe = X.columns[rfe.get_support()].tolist()

# 2.4 Random Forest Feature Importance
print("Calculating Random Forest feature importance...")
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X, y)
rf_importance = pd.DataFrame({'feature': X.columns, 'importance': rf_model.feature_importances_})
rf_importance = rf_importance.sort_values('importance', ascending=False)
top_rf_features = rf_importance.head(30)['feature'].tolist()

# 2.5 Consensus feature selection
print("Creating consensus feature selection...")
all_selected = {
    'univariate': set(selected_features_univariate),
    'mutual_info': set(top_mi_features),
    'rfe': set(selected_features_rfe),
    'random_forest': set(top_rf_features)
}

# Count how many methods selected each feature
feature_counts = {}
for method, features in all_selected.items():
    for feature in features:
        feature_counts[feature] = feature_counts.get(feature, 0) + 1

consensus_features = [feature for feature, count in feature_counts.items() if count >= 3]
print(f"Consensus features (selected by ≥3 methods): {len(consensus_features)}")

# Create feature selection summary
feature_selection_summary = pd.DataFrame({
    'feature': X.columns,
    'univariate': X.columns.isin(selected_features_univariate),
    'mutual_info': X.columns.isin(top_mi_features),
    'rfe': X.columns.isin(selected_features_rfe),
    'random_forest': X.columns.isin(top_rf_features),
    'consensus': X.columns.isin(consensus_features),
    'selection_count': [feature_counts.get(f, 0) for f in X.columns]
})

feature_selection_summary = feature_selection_summary.sort_values('selection_count', ascending=False)
feature_selection_summary.to_csv('pipeline_v4/plots/feature_selection_summary.csv', index=False)
print("Feature selection summary saved to: pipeline_v4/plots/feature_selection_summary.csv")

# 3. DATA PREPARATION FOR MODELING
print("\n=== 3. DATA PREPARATION FOR MODELING ===")

# Use consensus features for final dataset
final_features = consensus_features
X_final = X[final_features]

print(f"Final selected features: {len(final_features)}")
print("Selected features:")
for i, feature in enumerate(final_features, 1):
    print(f"{i:2d}. {feature}")

# Split data
print("\nSplitting data into train/validation/test sets...")
X_temp, X_test, y_temp, y_test = train_test_split(X_final, y, test_size=0.15, random_state=42, stratify=y)
X_train, X_val, y_train, y_val = train_test_split(X_temp, y_temp, test_size=0.176, random_state=42, stratify=y_temp)

print(f"Training set: {X_train.shape[0]} samples ({X_train.shape[0]/len(X_final)*100:.1f}%)")
print(f"Validation set: {X_val.shape[0]} samples ({X_val.shape[0]/len(X_final)*100:.1f}%)")
print(f"Test set: {X_test.shape[0]} samples ({X_test.shape[0]/len(X_final)*100:.1f}%)")

# Standardize numerical features
print("\nStandardizing numerical features...")
scaler = StandardScaler()

# Identify numerical columns in final features
numerical_cols = [col for col in final_features if col in numeric_features]
print(f"Numerical columns to scale: {len(numerical_cols)}")

if numerical_cols:
    X_train_scaled = X_train.copy()
    X_val_scaled = X_val.copy()
    X_test_scaled = X_test.copy()
    
    X_train_scaled[numerical_cols] = scaler.fit_transform(X_train[numerical_cols])
    X_val_scaled[numerical_cols] = scaler.transform(X_val[numerical_cols])
    X_test_scaled[numerical_cols] = scaler.transform(X_test[numerical_cols])
else:
    X_train_scaled = X_train
    X_val_scaled = X_val
    X_test_scaled = X_test

# Save prepared data
print("\nSaving prepared datasets...")
pd.concat([X_train_scaled, y_train], axis=1).to_csv('pipeline_v4/data/X_train_prepared.csv', index=False)
pd.concat([X_val_scaled, y_val], axis=1).to_csv('pipeline_v4/data/X_val_prepared.csv', index=False)
pd.concat([X_test_scaled, y_test], axis=1).to_csv('pipeline_v4/data/X_test_prepared.csv', index=False)

print("Prepared datasets saved to pipeline_v4/data/")

# 4. CREATE VISUALIZATIONS
print("\n=== 4. CREATING VISUALIZATIONS ===")

# Feature selection comparison plot
fig, axes = plt.subplots(2, 2, figsize=(15, 12))

# Method comparison
method_counts = feature_selection_summary[['univariate', 'mutual_info', 'rfe', 'random_forest']].sum()
axes[0,0].bar(method_counts.index, method_counts.values, color=['skyblue', 'lightgreen', 'orange', 'red'], alpha=0.7)
axes[0,0].set_title('Features Selected by Each Method')
axes[0,0].set_ylabel('Number of Features')
axes[0,0].tick_params(axis='x', rotation=45)
axes[0,0].grid(True, alpha=0.3)

# Selection count distribution
selection_counts = feature_selection_summary['selection_count'].value_counts().sort_index()
axes[0,1].bar(selection_counts.index, selection_counts.values, color='purple', alpha=0.7)
axes[0,1].set_title('Feature Selection Count Distribution')
axes[0,1].set_xlabel('Number of Methods')
axes[0,1].set_ylabel('Number of Features')
axes[0,1].grid(True, alpha=0.3)

# Top features by selection count
top_consensus = feature_selection_summary.head(15)
y_pos = np.arange(len(top_consensus))
axes[1,0].barh(y_pos, top_consensus['selection_count'], color='green', alpha=0.7)
axes[1,0].set_yticks(y_pos)
axes[1,0].set_yticklabels(top_consensus['feature'], fontsize=8)
axes[1,0].set_title('Top 15 Features by Selection Count')
axes[1,0].set_xlabel('Number of Methods')
axes[1,0].grid(True, alpha=0.3)

# Class distribution in splits
split_info = pd.DataFrame({
    'Train': [y_train.sum(), len(y_train) - y_train.sum()],
    'Validation': [y_val.sum(), len(y_val) - y_val.sum()],
    'Test': [y_test.sum(), len(y_test) - y_test.sum()]
}, index=['Hire', 'Reject'])

split_info.plot(kind='bar', ax=axes[1,1], color=['lightgreen', 'lightcoral'], alpha=0.7)
axes[1,1].set_title('Class Distribution in Data Splits')
axes[1,1].set_ylabel('Count')
axes[1,1].legend()
axes[1,1].tick_params(axis='x', rotation=0)
axes[1,1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('pipeline_v4/plots/feature_engineering_summary.png', dpi=300, bbox_inches='tight')
plt.close()
print("Feature engineering summary saved to: pipeline_v4/plots/feature_engineering_summary.png")

print(f"\n=== FEATURE ENGINEERING AND PREPARATION COMPLETE ===")
print(f"Original features: {df.shape[1] - 2}")
print(f"Engineered features: {df_engineered.shape[1] - df.shape[1]}")
print(f"Final selected features: {len(final_features)}")
print(f"Data splits: Train {len(X_train)}, Val {len(X_val)}, Test {len(X_test)}")
print("All data prepared and saved successfully!")