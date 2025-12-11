#!/usr/bin/env python3
"""
Phase 2: Advanced Feature Engineering
Create sophisticated feature combinations and engineering techniques
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler, PowerTransformer, QuantileTransformer
from sklearn.preprocessing import PolynomialFeatures
import warnings
warnings.filterwarnings('ignore')

# Load the prepared datasets
train_data = pd.read_csv('pipeline_v4/data/X_train_prepared.csv')
val_data = pd.read_csv('pipeline_v4/data/X_val_prepared.csv')
test_data = pd.read_csv('pipeline_v4/data/X_test_prepared.csv')

print("=== PHASE 2: ADVANCED FEATURE ENGINEERING ===")
print(f"Training data: {train_data.shape}")
print(f"Validation data: {val_data.shape}")
print(f"Test data: {test_data.shape}")

# Separate features and targets
X_train = train_data.drop('target_binary', axis=1)
y_train = train_data['target_binary']
X_val = val_data.drop('target_binary', axis=1)
y_val = val_data['target_binary']
X_test = test_data.drop('target_binary', axis=1)
y_test = test_data['target_binary']

print(f"\nOriginal features: {X_train.shape[1]}")

# Identify current feature types
def classify_features(df):
    """Classify features by type"""
    numeric_features = []
    binary_features = []
    interaction_features = []
    polynomial_features = []
    ratio_features = []
    
    for feature in df.columns:
        if 'interaction' in feature:
            interaction_features.append(feature)
        elif any(term in feature for term in ['_squared', '_cubed', '_sqrt']):
            polynomial_features.append(feature)
        elif 'ratio' in feature:
            ratio_features.append(feature)
        elif df[feature].nunique() <= 2 and set(df[feature].unique()).issubset({0, 1, 0.0, 1.0}):
            binary_features.append(feature)
        else:
            numeric_features.append(feature)
    
    return numeric_features, binary_features, interaction_features, polynomial_features, ratio_features

numeric_features, binary_features, interaction_features, polynomial_features, ratio_features = classify_features(X_train)

print(f"\nCurrent feature breakdown:")
print(f"   Numeric: {len(numeric_features)}")
print(f"   Binary: {len(binary_features)}")
print(f"   Interaction: {len(interaction_features)}")
print(f"   Polynomial: {len(polynomial_features)}")
print(f"   Ratio: {len(ratio_features)}")

# 1. ADVANCED INTERACTION FEATURES
print(f"\n=== 1. CREATING ADVANCED INTERACTION FEATURES ===")

# Create copies for feature engineering
X_train_eng = X_train.copy()
X_val_eng = X_val.copy()
X_test_eng = X_test.copy()

# Get top features from correlation analysis
try:
    correlation_results = pd.read_csv('pipeline_v4/plots/correlation_analysis_results.csv')
    top_features = correlation_results.head(10)['feature'].tolist()
    # Filter to existing features
    top_features = [f for f in top_features if f in X_train.columns]
except:
    top_features = numeric_features[:10]

print(f"Top features for interactions: {len(top_features)}")

# Create three-way interactions
for i in range(len(top_features)):
    for j in range(i+1, len(top_features)):
        for k in range(j+1, min(j+2, len(top_features))):  # Limit to avoid explosion
            feat1, feat2, feat3 = top_features[i], top_features[j], top_features[k]
            interaction_name = f"interaction3_{feat1.replace(' ', '_')}_{feat2.replace(' ', '_')}_{feat3.replace(' ', '_')}"
            
            X_train_eng[interaction_name] = X_train[feat1] * X_train[feat2] * X_train[feat3]
            X_val_eng[interaction_name] = X_val[feat1] * X_val[feat2] * X_val[feat3]
            X_test_eng[interaction_name] = X_test[feat1] * X_test[feat2] * X_test[feat3]

# Create ratio-based interactions
for i in range(len(top_features)):
    for j in range(i+1, len(top_features)):
        feat1, feat2 = top_features[i], top_features[j]
        
        # Avoid division by zero
        safe_div = X_train[feat2].replace(0, 1e-6)
        
        ratio_name = f"ratio_interaction_{feat1.replace(' ', '_')}_div_{feat2.replace(' ', '_')}"
        X_train_eng[ratio_name] = X_train[feat1] / safe_div
        X_val_eng[ratio_name] = X_val[feat1] / X_val[feat2].replace(0, 1e-6)
        X_test_eng[ratio_name] = X_test[feat1] / X_test[feat2].replace(0, 1e-6)

print(f"Three-way interactions created: {len([col for col in X_train_eng.columns if col.startswith('interaction3_')])}")
print(f"Ratio interactions created: {len([col for col in X_train_eng.columns if col.startswith('ratio_interaction_')])}")

# 2. ADVANCED POLYNOMIAL FEATURES
print(f"\n=== 2. CREATING ADVANCED POLYNOMIAL FEATURES ===")

# Create polynomial features for top numeric features
numeric_top = [f for f in top_features if f in numeric_features][:8]

for feature in numeric_top:
    # Higher degree polynomials
    X_train_eng[f"{feature}_4th"] = X_train[feature] ** 4
    X_train_eng[f"{feature}_5th"] = X_train[feature] ** 5
    
    # Logarithmic transformations (add 1 to handle zeros)
    X_train_eng[f"{feature}_log"] = np.log1p(X_train[feature])
    
    # Exponential transformations (scaled)
    X_train_eng[f"{feature}_exp"] = np.expm1(X_train[feature] / 100)
    
    # Apply same transformations to validation and test
    X_val_eng[f"{feature}_4th"] = X_val[feature] ** 4
    X_val_eng[f"{feature}_5th"] = X_val[feature] ** 5
    X_val_eng[f"{feature}_log"] = np.log1p(X_val[feature])
    X_val_eng[f"{feature}_exp"] = np.expm1(X_val[feature] / 100)
    
    X_test_eng[f"{feature}_4th"] = X_test[feature] ** 4
    X_test_eng[f"{feature}_5th"] = X_test[feature] ** 5
    X_test_eng[f"{feature}_log"] = np.log1p(X_test[feature])
    X_test_eng[f"{feature}_exp"] = np.expm1(X_test[feature] / 100)

print(f"Advanced polynomial features created for {len(numeric_top)} features")

# 3. DOMAIN-SPECIFIC ENGINEERING
print(f"\n=== 3. DOMAIN-SPECIFIC FEATURE ENGINEERING ===")

# Tech domain features
tech_features = ['feat_skill_python', 'feat_skill_sql', 'feat_skill_machine_learning', 'feat_skill_deep_learning', 'feat_skill_tableau']
available_tech = [f for f in tech_features if f in X_train.columns]

if len(available_tech) >= 2:
    # Tech skill diversity index
    tech_counts = X_train[available_tech].sum(axis=1)
    tech_diversity = 1 - (X_train[available_tech].var(axis=1) / (tech_counts + 1e-6))
    X_train_eng['tech_diversity_index'] = tech_diversity
    X_val_eng['tech_diversity_index'] = 1 - (X_val[available_tech].var(axis=1) / (X_val[available_tech].sum(axis=1) + 1e-6))
    X_test_eng['tech_diversity_index'] = 1 - (X_test[available_tech].var(axis=1) / (X_test[available_tech].sum(axis=1) + 1e-6))
    
    # Tech skill intensity
    X_train_eng['tech_intensity'] = tech_counts / len(available_tech)
    X_val_eng['tech_intensity'] = X_val[available_tech].sum(axis=1) / len(available_tech)
    X_test_eng['tech_intensity'] = X_test[available_tech].sum(axis=1) / len(available_tech)

# Management domain features
mgmt_features = ['feat_skill_project_management', 'feat_cert_pmp', 'feat_cert_scrum', 'feat_cert_csm', 'feat_cert_six_sigma']
available_mgmt = [f for f in mgmt_features if f in X_train.columns]

if len(available_mgmt) >= 2:
    # Management skill score
    mgmt_score = X_train[available_mgmt].sum(axis=1) / len(available_mgmt)
    X_train_eng['mgmt_skill_score'] = mgmt_score
    X_val_eng['mgmt_skill_score'] = X_val[available_mgmt].sum(axis=1) / len(available_mgmt)
    X_test_eng['mgmt_skill_score'] = X_test[available_mgmt].sum(axis=1) / len(available_mgmt)

# Experience-based features
if 'feat_years_experience_extracted' in X_train.columns:
    exp = X_train['feat_years_experience_extracted']
    
    # Experience efficiency (skills per year)
    if 'feat_num_skills_matched' in X_train.columns:
        skills = X_train['feat_num_skills_matched']
        X_train_eng['experience_efficiency'] = skills / (exp + 1)
        X_val_eng['experience_efficiency'] = X_val['feat_num_skills_matched'] / (X_val['feat_years_experience_extracted'] + 1)
        X_test_eng['experience_efficiency'] = X_test['feat_num_skills_matched'] / (X_test['feat_years_experience_extracted'] + 1)
    
    # Experience maturity (projects per year)
    if 'Projects Count' in X_train.columns:
        projects = X_train['Projects Count']
        X_train_eng['experience_maturity'] = projects / (exp + 1)
        X_val_eng['experience_maturity'] = X_val['Projects Count'] / (X_val['feat_years_experience_extracted'] + 1)
        X_test_eng['experience_maturity'] = X_test['Projects Count'] / (X_test['feat_years_experience_extracted'] + 1)

# 4. ADVANCED RATIO FEATURES
print(f"\n=== 4. CREATING ADVANCED RATIO FEATURES ===")

# Skill-to-certification ratios
skill_cols = [col for col in X_train.columns if col.startswith('feat_skill_')]
cert_cols = [col for col in X_train.columns if col.startswith('feat_cert_')]

if skill_cols and cert_cols:
    total_skills = X_train[skill_cols].sum(axis=1)
    total_certs = X_train[cert_cols].sum(axis=1)
    
    # Skill-to-certification ratio
    X_train_eng['skill_to_cert_ratio'] = total_skills / (total_certs + 1)
    X_val_eng['skill_to_cert_ratio'] = X_val[skill_cols].sum(axis=1) / (X_val[cert_cols].sum(axis=1) + 1)
    X_test_eng['skill_to_cert_ratio'] = X_test[skill_cols].sum(axis=1) / (X_test[cert_cols].sum(axis=1) + 1)
    
    # Certification density (certs per skill)
    X_train_eng['certification_density'] = total_certs / (total_skills + 1)
    X_val_eng['certification_density'] = X_val[cert_cols].sum(axis=1) / (X_val[skill_cols].sum(axis=1) + 1)
    X_test_eng['certification_density'] = X_test[cert_cols].sum(axis=1) / (X_test[skill_cols].sum(axis=1) + 1)

# 5. FEATURE SCALING AND NORMALIZATION
print(f"\n=== 5. APPLYING ADVANCED SCALING ===")

# Identify features that need scaling (high variance or skewed)
high_variance_features = []
skewed_features = []

for feature in X_train_eng.columns:
    if X_train_eng[feature].dtype in ['int64', 'float64']:
        variance = X_train_eng[feature].var()
        skewness = X_train_eng[feature].skew()
        
        if variance > 1000:  # High variance threshold
            high_variance_features.append(feature)
        if abs(skewness) > 2:  # High skewness threshold
            skewed_features.append(feature)

print(f"High variance features: {len(high_variance_features)}")
print(f"Skewed features: {len(skewed_features)}")

# Apply log transformation to highly skewed features
for feature in skewed_features[:5]:  # Limit to avoid over-transformation
    # Add small constant to handle zeros
    min_val = X_train_eng[feature].min()
    offset = abs(min_val) + 1 if min_val <= 0 else 0
    
    log_name = f"{feature}_log_scaled"
    X_train_eng[log_name] = np.log1p(X_train_eng[feature] + offset)
    X_val_eng[log_name] = np.log1p(X_val_eng[feature] + offset)
    X_test_eng[log_name] = np.log1p(X_test_eng[feature] + offset)

# Apply quantile transformation to high variance features
if high_variance_features:
    quantile_transformer = QuantileTransformer(output_distribution='normal', random_state=42)
    
    for feature in high_variance_features[:3]:  # Limit to avoid over-transformation
        qt_name = f"{feature}_quantile"
        
        # Fit on training data
        X_train_eng[qt_name] = quantile_transformer.fit_transform(X_train_eng[[feature]])
        X_val_eng[qt_name] = quantile_transformer.transform(X_val_eng[[feature]])
        X_test_eng[qt_name] = quantile_transformer.transform(X_test_eng[[feature]])

print(f"\nFinal feature count: {X_train_eng.shape[1]}")
print(f"New features created: {X_train_eng.shape[1] - X_train.shape[1]}")

# 6. SAVE ENGINEERED DATASETS
print(f"\n=== 6. SAVING ENGINEERED DATASETS ===")

# Create final datasets
train_final = pd.concat([X_train_eng, y_train], axis=1)
val_final = pd.concat([X_val_eng, y_val], axis=1)
test_final = pd.concat([X_test_eng, y_test], axis=1)

# Save datasets
train_final.to_csv('pipeline_v4/data/X_train_engineered.csv', index=False)
val_final.to_csv('pipeline_v4/data/X_val_engineered.csv', index=False)
test_final.to_csv('pipeline_v4/data/X_test_engineered.csv', index=False)

print(f"✅ Engineered datasets saved successfully!")
print(f"Training set: {train_final.shape}")
print(f"Validation set: {val_final.shape}")
print(f"Test set: {test_final.shape}")

# Create feature engineering summary
feature_summary = pd.DataFrame({
    'feature_type': ['original', 'interaction3', 'ratio_interaction', 'polynomial_advanced', 
                     'domain_specific', 'ratio_advanced', 'scaling_transforms'],
    'count': [X_train.shape[1],
              len([col for col in X_train_eng.columns if col.startswith('interaction3_')]),
              len([col for col in X_train_eng.columns if col.startswith('ratio_interaction_')]),
              len([col for col in X_train_eng.columns if any(term in col for term in ['_4th', '_5th', '_log', '_exp'])]),
              len([col for col in X_train_eng.columns if any(term in col for term in ['tech_', 'mgmt_', 'experience_'])]),
              len([col for col in X_train_eng.columns if any(term in col for term in ['_ratio', '_density'])]),
              len([col for col in X_train_eng.columns if any(term in col for term in ['_log_scaled', '_quantile'])])]
})

feature_summary.to_csv('pipeline_v4/plots/feature_engineering_summary_advanced.csv', index=False)
print(f"✅ Feature engineering summary saved!")

print(f"\n=== ADVANCED FEATURE ENGINEERING COMPLETE ===")
print(f"Total features created: {X_train_eng.shape[1]}")
print(f"Feature engineering multiplier: {X_train_eng.shape[1] / X_train.shape[1]:.1f}x")