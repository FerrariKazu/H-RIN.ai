#!/usr/bin/env python3
"""
Phase 2: Advanced Feature Engineering and Preparation
Load and analyze current feature set from Phase 1
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
from sklearn.feature_selection import SelectKBest, f_classif, RFE, SelectFromModel
from sklearn.linear_model import LogisticRegression, LassoCV
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
import warnings
warnings.filterwarnings('ignore')

print("=== PHASE 2: ADVANCED FEATURE ENGINEERING AND PREPARATION ===")

# Load the prepared datasets from Phase 1
try:
    train_data = pd.read_csv('pipeline_v4/data/X_train_prepared.csv')
    val_data = pd.read_csv('pipeline_v4/data/X_val_prepared.csv')
    test_data = pd.read_csv('pipeline_v4/data/X_test_prepared.csv')
    
    print("✅ Successfully loaded prepared datasets from Phase 1")
    print(f"Training set: {train_data.shape}")
    print(f"Validation set: {val_data.shape}")
    print(f"Test set: {test_data.shape}")
    
    # Separate features and target
    X_train = train_data.drop('target_binary', axis=1)
    y_train = train_data['target_binary']
    X_val = val_data.drop('target_binary', axis=1)
    y_val = val_data['target_binary']
    X_test = test_data.drop('target_binary', axis=1)
    y_test = test_data['target_binary']
    
    print(f"\nFeature breakdown:")
    print(f"Total features: {X_train.shape[1]}")
    print(f"Training samples: {X_train.shape[0]}")
    print(f"Target distribution - Train: {y_train.value_counts().to_dict()}")
    print(f"Target distribution - Val: {y_val.value_counts().to_dict()}")
    print(f"Target distribution - Test: {y_test.value_counts().to_dict()}")
    
except FileNotFoundError:
    print("❌ Phase 1 prepared datasets not found. Loading original balanced dataset...")
    
    # Load the original balanced dataset
    df = pd.read_csv('pipeline_v4/data/normalized_dataset_v4_balanced.csv')
    df['target_binary'] = (df['Recruiter_Decision'] == 'Hire').astype(int)
    
    print(f"Loaded balanced dataset: {df.shape}")
    
    # Separate features and target
    X = df.drop(['Recruiter_Decision', 'target_binary'], axis=1)
    y = df['target_binary']
    
    # Split the data
    X_temp, X_test, y_temp, y_test = train_test_split(X, y, test_size=0.15, random_state=42, stratify=y)
    X_train, X_val, y_train, y_val = train_test_split(X_temp, y_temp, test_size=0.176, random_state=42, stratify=y_temp)
    
    print(f"Created new splits:")
    print(f"Training: {X_train.shape[0]} samples")
    print(f"Validation: {X_val.shape[0]} samples") 
    print(f"Test: {X_test.shape[0]} samples")

# Analyze current feature set
print(f"\n=== CURRENT FEATURE ANALYSIS ===")

# Identify feature types
current_features = X_train.columns.tolist()
numeric_features = []
binary_features = []
interaction_features = []
poly_features = []
ratio_features = []

for feature in current_features:
    if 'interaction' in feature:
        interaction_features.append(feature)
    elif any(term in feature for term in ['_squared', '_cubed', '_sqrt']):
        poly_features.append(feature)
    elif 'ratio' in feature:
        ratio_features.append(feature)
    elif X_train[feature].nunique() <= 2 and set(X_train[feature].unique()).issubset({0, 1, 0.0, 1.0}):
        binary_features.append(feature)
    else:
        numeric_features.append(feature)

print(f"Feature type breakdown:")
print(f"   Numeric features: {len(numeric_features)}")
print(f"   Binary features: {len(binary_features)}")
print(f"   Interaction features: {len(interaction_features)}")
print(f"   Polynomial features: {len(poly_features)}")
print(f"   Ratio features: {len(ratio_features)}")
print(f"   Total: {len(current_features)}")

# Show top 10 features by name
print(f"\nTop 10 current features:")
for i, feature in enumerate(current_features[:10], 1):
    print(f"   {i:2d}. {feature}")

# Basic statistics
print(f"\n=== BASIC STATISTICS ===")
print(f"Training set statistics:")
print(f"   Mean of means: {X_train.mean().mean():.3f}")
print(f"   Mean of std: {X_train.std().mean():.3f}")
print(f"   Min value: {X_train.min().min():.3f}")
print(f"   Max value: {X_train.max().max():.3f}")

# Check for any remaining issues
print(f"\n=== DATA QUALITY CHECK ===")
print(f"Missing values in training: {X_train.isnull().sum().sum()}")
print(f"Infinite values in training: {np.isinf(X_train.select_dtypes(include=[np.number])).sum().sum()}")
print(f"Duplicate rows in training: {X_train.duplicated().sum()}")

print(f"\n✅ Current feature set analysis complete!")
print(f"Ready to proceed with advanced feature engineering...")