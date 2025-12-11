#!/usr/bin/env python3
"""
Phase 2: Advanced Feature Selection
Apply multiple feature selection methods and create consensus selection
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_selection import SelectKBest, f_classif, RFE, SelectFromModel
from sklearn.linear_model import LogisticRegression, LassoCV, Lasso
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')

# Load the engineered datasets
X_train = pd.read_csv('pipeline_v4/data/X_train_engineered.csv').drop('target_binary', axis=1)
y_train = pd.read_csv('pipeline_v4/data/X_train_engineered.csv')['target_binary']
X_val = pd.read_csv('pipeline_v4/data/X_val_engineered.csv').drop('target_binary', axis=1)
y_val = pd.read_csv('pipeline_v4/data/X_val_engineered.csv')['target_binary']
X_test = pd.read_csv('pipeline_v4/data/X_test_engineered.csv').drop('target_binary', axis=1)
y_test = pd.read_csv('pipeline_v4/data/X_test_engineered.csv')['target_binary']

print("=== PHASE 2: ADVANCED FEATURE SELECTION ===")
print(f"Training data: {X_train.shape}")
print(f"Validation data: {X_val.shape}")
print(f"Test data: {X_test.shape}")

# 1. UNIVARIATE FEATURE SELECTION
print("\n=== 1. UNIVARIATE FEATURE SELECTION ===")

# F-statistic based selection
selector_f = SelectKBest(score_func=f_classif, k=50)
X_train_f = selector_f.fit_transform(X_train, y_train)
selected_f = X_train.columns[selector_f.get_support()].tolist()
f_scores = selector_f.scores_

print(f"F-statistic selected features: {len(selected_f)}")
print(f"Top 10 F-statistic features:")
f_results = pd.DataFrame({'feature': X_train.columns, 'f_score': f_scores})
f_results = f_results.sort_values('f_score', ascending=False)
for i, row in f_results.head(10).iterrows():
    print(f"   {row['feature'][:50]:<50} | F-score: {row['f_score']:.2f}")

# 2. LASSO-BASED FEATURE SELECTION
print("\n=== 2. LASSO-BASED FEATURE SELECTION ===")

# Standardize features for LASSO
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)

# LASSO with cross-validation
lasso_cv = LassoCV(cv=5, random_state=42, max_iter=2000)
lasso_cv.fit(X_train_scaled, y_train)

# Get feature importance from LASSO coefficients
lasso_coef = lasso_cv.coef_
lasso_importance = np.abs(lasso_coef)

# Select non-zero coefficients
selected_lasso = X_train.columns[lasso_importance > 0].tolist()

print(f"LASSO selected features: {len(selected_lasso)}")
print(f"LASSO alpha (regularization): {lasso_cv.alpha_:.4f}")

# LASSO results
lasso_results = pd.DataFrame({
    'feature': X_train.columns,
    'coefficient': lasso_coef,
    'importance': lasso_importance
}).sort_values('importance', ascending=False)

print(f"Top 10 LASSO features:")
for i, row in lasso_results.head(10).iterrows():
    print(f"   {row['feature'][:50]:<50} | Coef: {row['coefficient']:8.4f} | Importance: {row['importance']:.4f}")

# 3. RANDOM FOREST FEATURE IMPORTANCE
print("\n=== 3. RANDOM FOREST FEATURE IMPORTANCE ===")

# Random Forest with cross-validation
rf_model = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
rf_model.fit(X_train, y_train)

# Get feature importances
rf_importances = rf_model.feature_importances_
rf_results = pd.DataFrame({
    'feature': X_train.columns,
    'importance': rf_importances
}).sort_values('importance', ascending=False)

# Select top features by importance threshold
rf_threshold = rf_importances.mean() + rf_importances.std()
selected_rf = rf_results[rf_results['importance'] > rf_threshold]['feature'].tolist()

print(f"Random Forest selected features: {len(selected_rf)}")
print(f"RF importance threshold: {rf_threshold:.4f}")
print(f"Top 10 RF features:")
for i, row in rf_results.head(10).iterrows():
    print(f"   {row['feature'][:50]:<50} | Importance: {row['importance']:.4f}")

# 4. GRADIENT BOOSTING FEATURE IMPORTANCE
print("\n=== 4. GRADIENT BOOSTING FEATURE IMPORTANCE ===")

# Gradient Boosting
gb_model = GradientBoostingClassifier(n_estimators=100, random_state=42)
gb_model.fit(X_train, y_train)

# Get feature importances
gb_importances = gb_model.feature_importances_
gb_results = pd.DataFrame({
    'feature': X_train.columns,
    'importance': gb_importances
}).sort_values('importance', ascending=False)

# Select top features
selected_gb = gb_results.head(50)['feature'].tolist()  # Top 50 features

print(f"Gradient Boosting selected features: {len(selected_gb)}")
print(f"Top 10 GB features:")
for i, row in gb_results.head(10).iterrows():
    print(f"   {row['feature'][:50]:<50} | Importance: {row['importance']:.4f}")

# 5. XGBOOST FEATURE IMPORTANCE
print("\n=== 5. XGBOOST FEATURE IMPORTANCE ===")

try:
    # XGBoost
    xgb_model = xgb.XGBClassifier(n_estimators=100, random_state=42, eval_metric='logloss')
    xgb_model.fit(X_train, y_train)
    
    # Get feature importances
    xgb_importances = xgb_model.feature_importances_
    xgb_results = pd.DataFrame({
        'feature': X_train.columns,
        'importance': xgb_importances
    }).sort_values('importance', ascending=False)
    
    # Select top features
    selected_xgb = xgb_results.head(50)['feature'].tolist()
    
    print(f"XGBoost selected features: {len(selected_xgb)}")
    print(f"Top 10 XGBoost features:")
    for i, row in xgb_results.head(10).iterrows():
        print(f"   {row['feature'][:50]:<50} | Importance: {row['importance']:.4f}")
        
except ImportError:
    print("XGBoost not available, skipping XGBoost feature selection")
    xgb_results = pd.DataFrame()
    selected_xgb = []

# 6. RECURSIVE FEATURE ELIMINATION (RFE)
print("\n=== 6. RECURSIVE FEATURE ELIMINATION ===")

# Use logistic regression for RFE
rfe_model = LogisticRegression(random_state=42, max_iter=1000)
rfe_selector = RFE(estimator=rfe_model, n_features_to_select=40, step=1)
rfe_selector.fit(X_train, y_train)

selected_rfe = X_train.columns[rfe_selector.support_].tolist()

print(f"RFE selected features: {len(selected_rfe)}")
print(f"RFE ranking (1=selected): {rfe_selector.ranking_.min()} to {rfe_selector.ranking_.max()}")

# Get feature rankings
rfe_rankings = pd.DataFrame({
    'feature': X_train.columns,
    'ranking': rfe_selector.ranking_,
    'selected': rfe_selector.support_
}).sort_values('ranking')

print(f"Top 10 RFE features:")
for i, row in rfe_rankings.head(10).iterrows():
    print(f"   {row['feature'][:50]:<50} | Rank: {row['ranking']} | Selected: {row['selected']}")

# 7. CREATE CONSENSUS FEATURE SELECTION
print("\n=== 7. CONSENSUS FEATURE SELECTION ===")

# Combine all selection methods
all_selections = {
    'univariate_f': set(selected_f),
    'lasso': set(selected_lasso),
    'random_forest': set(selected_rf),
    'gradient_boosting': set(selected_gb),
    'xgboost': set(selected_xgb) if selected_xgb else set(),
    'rfe': set(selected_rfe)
}

# Count how many methods selected each feature
feature_counts = {}
for method, features in all_selections.items():
    for feature in features:
        feature_counts[feature] = feature_counts.get(feature, 0) + 1

# Create consensus selection
consensus_threshold = 3  # Feature must be selected by at least 3 methods
consensus_features = [feature for feature, count in feature_counts.items() if count >= consensus_threshold]

print(f"Consensus threshold: {consensus_threshold} methods")
print(f"Consensus features selected: {len(consensus_features)}")

# Create comprehensive feature selection summary
selection_summary = pd.DataFrame({
    'feature': X_train.columns,
    'univariate_f': X_train.columns.isin(selected_f),
    'lasso': X_train.columns.isin(selected_lasso),
    'random_forest': X_train.columns.isin(selected_rf),
    'gradient_boosting': X_train.columns.isin(selected_gb),
    'xgboost': X_train.columns.isin(selected_xgb),
    'rfe': X_train.columns.isin(selected_rfe),
    'consensus': X_train.columns.isin(consensus_features),
    'selection_count': [feature_counts.get(f, 0) for f in X_train.columns]
})

# Sort by selection count and importance
selection_summary = selection_summary.sort_values(['selection_count', 'consensus'], ascending=[False, False])

# Save selection summary
selection_summary.to_csv('pipeline_v4/plots/advanced_feature_selection_summary.csv', index=False)
print(f"✅ Feature selection summary saved to: pipeline_v4/plots/advanced_feature_selection_summary.csv")

# 8. VALIDATE CONSENSUS SELECTION
print("\n=== 8. VALIDATING CONSENSUS SELECTION ===")

# Use consensus features for final selection
X_train_consensus = X_train[consensus_features]
X_val_consensus = X_val[consensus_features]
X_test_consensus = X_test[consensus_features]

# Test performance with consensus features
models_to_test = {
    'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000),
    'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=42)
}

print("Model performance with consensus features:")
print(f"{'Model':<20} | {'Train Accuracy':<12} | {'Val Accuracy':<12} | {'CV Score':<10}")
print("-" * 60)

for name, model in models_to_test.items():
    # Train on consensus features
    model.fit(X_train_consensus, y_train)
    
    # Get accuracies
    train_acc = model.score(X_train_consensus, y_train)
    val_acc = model.score(X_val_consensus, y_val)
    
    # Cross-validation score
    cv_scores = cross_val_score(model, X_train_consensus, y_train, cv=5, scoring='accuracy')
    cv_mean = cv_scores.mean()
    
    print(f"{name:<20} | {train_acc:<12.4f} | {val_acc:<12.4f} | {cv_mean:<10.4f}")

# 9. CREATE VISUALIZATIONS
print("\n=== 9. CREATING VISUALIZATIONS ===")

# Feature selection comparison plot
fig, axes = plt.subplots(2, 3, figsize=(18, 12))

# Method comparison
method_counts = selection_summary[['univariate_f', 'lasso', 'random_forest', 'gradient_boosting', 'xgboost', 'rfe']].sum()
axes[0,0].bar(range(len(method_counts)), method_counts.values, 
              color=['skyblue', 'orange', 'green', 'red', 'purple', 'brown'], alpha=0.7)
axes[0,0].set_title('Features Selected by Each Method')
axes[0,0].set_ylabel('Number of Features')
axes[0,0].set_xticks(range(len(method_counts)))
axes[0,0].set_xticklabels(['F-test', 'LASSO', 'RF', 'GB', 'XGB', 'RFE'], rotation=45)
axes[0,0].grid(True, alpha=0.3)

# Selection count distribution
selection_counts = selection_summary['selection_count'].value_counts().sort_index()
axes[0,1].bar(selection_counts.index, selection_counts.values, color='teal', alpha=0.7)
axes[0,1].set_title('Feature Selection Count Distribution')
axes[0,1].set_xlabel('Number of Methods')
axes[0,1].set_ylabel('Number of Features')
axes[0,1].grid(True, alpha=0.3)

# Consensus features
consensus_data = selection_summary[selection_summary['consensus'] == True]
y_pos = np.arange(len(consensus_data))
axes[0,2].barh(y_pos, consensus_data['selection_count'], color='darkgreen', alpha=0.7)
axes[0,2].set_yticks(y_pos)
axes[0,2].set_yticklabels([f[:30] for f in consensus_data['feature']], fontsize=8)
axes[0,2].set_title(f'Consensus Features (≥{consensus_threshold} methods)')
axes[0,2].set_xlabel('Number of Methods')
axes[0,2].grid(True, alpha=0.3)

# Feature importance comparison (top 15)
top_features_comparison = pd.DataFrame({
    'feature': consensus_data['feature'][:15],
    'selection_count': consensus_data['selection_count'][:15]
})

axes[1,0].barh(range(len(top_features_comparison)), top_features_comparison['selection_count'], 
               color='coral', alpha=0.7)
axes[1,0].set_yticks(range(len(top_features_comparison)))
axes[1,0].set_yticklabels([f[:25] for f in top_features_comparison['feature']], fontsize=8)
axes[1,0].set_title('Top 15 Consensus Features')
axes[1,0].set_xlabel('Selection Count')
axes[1,0].grid(True, alpha=0.3)

# Method agreement heatmap
agreement_matrix = selection_summary[['univariate_f', 'lasso', 'random_forest', 'gradient_boosting', 'rfe']].astype(int)
agreement_matrix.columns = ['F-test', 'LASSO', 'RF', 'GB', 'RFE']

# Sample top 20 features for heatmap
top_20_features = selection_summary.head(20)
heatmap_data = top_20_features[['univariate_f', 'lasso', 'random_forest', 'gradient_boosting', 'rfe']].astype(int)
heatmap_data.columns = ['F-test', 'LASSO', 'RF', 'GB', 'RFE']

sns.heatmap(heatmap_data, annot=True, cmap='RdYlBu_r', cbar_kws={'shrink': 0.8}, 
            xticklabels=True, yticklabels=False, ax=axes[1,1])
axes[1,1].set_title('Feature Selection Agreement (Top 20)')
axes[1,1].set_xlabel('Selection Methods')

# Feature reduction summary
original_count = len(X_train.columns)
consensus_count = len(consensus_features)
reduction_pct = (1 - consensus_count/original_count) * 100

axes[1,2].pie([consensus_count, original_count - consensus_count], 
              labels=[f'Consensus\n({consensus_count})', f'Removed\n({original_count - consensus_count})'],
              colors=['lightgreen', 'lightcoral'], autopct='%1.1f%%', startangle=90)
axes[1,2].set_title(f'Feature Reduction\n({reduction_pct:.1f}% reduction)')

plt.tight_layout()
plt.savefig('pipeline_v4/plots/advanced_feature_selection_analysis.png', dpi=300, bbox_inches='tight')
plt.close()
print("✅ Advanced feature selection analysis plot saved!")

# 10. SAVE FINAL SELECTED FEATURES
print("\n=== 10. SAVING FINAL SELECTED FEATURES ===")

# Save consensus features
final_features = {
    'consensus_features': consensus_features,
    'feature_count': len(consensus_features),
    'reduction_percentage': reduction_pct,
    'selection_threshold': consensus_threshold,
    'original_feature_count': original_count
}

import json
with open('pipeline_v4/data/final_selected_features.json', 'w') as f:
    json.dump(final_features, f, indent=2)

print(f"✅ Final selected features saved to: pipeline_v4/data/final_selected_features.json")

# Apply final selection to datasets
X_train_final = X_train[consensus_features]
X_val_final = X_val[consensus_features]
X_test_final = X_test[consensus_features]

# Save final datasets
train_final = pd.concat([X_train_final, y_train], axis=1)
val_final = pd.concat([X_val_final, y_val], axis=1)
test_final = pd.concat([X_test_final, y_test], axis=1)

train_final.to_csv('pipeline_v4/data/X_train_final.csv', index=False)
val_final.to_csv('pipeline_v4/data/X_val_final.csv', index=False)
test_final.to_csv('pipeline_v4/data/X_test_final.csv', index=False)

print(f"✅ Final datasets saved:")
print(f"   Training: {X_train_final.shape}")
print(f"   Validation: {X_val_final.shape}")
print(f"   Test: {X_test_final.shape}")

print(f"\n=== ADVANCED FEATURE SELECTION COMPLETE ===")
print(f"Original features: {original_count}")
print(f"Final consensus features: {len(consensus_features)}")
print(f"Feature reduction: {reduction_pct:.1f}%")
print(f"Consensus threshold: {consensus_threshold} methods")
print("✅ Phase 2 feature selection complete!")