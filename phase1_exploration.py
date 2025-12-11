#!/usr/bin/env python3
"""
Phase 1: Data Exploration and Feature Analysis
Comprehensive analysis of the balanced dataset for recruitment screening
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

# Set style for better plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# Load the balanced dataset
print("Loading balanced dataset...")
df = pd.read_csv('pipeline_v4/data/normalized_dataset_v4_balanced.csv')
print(f"Dataset shape: {df.shape}")
print(f"Missing values: {df.isnull().sum().sum()}")

# Initial exploration
print("\n=== INITIAL DATASET EXPLORATION ===")
print(f"Total records: {len(df)}")
print(f"Total features: {df.shape[1]}")
print(f"Target variable distribution:")
target_counts = df['Recruiter_Decision'].value_counts()
print(target_counts)
print(f"Hire percentage: {(target_counts['Hire'] / len(df) * 100):.1f}%")

# Identify feature types
numeric_features = []
categorical_features = []
binary_features = []
target_col = 'Recruiter_Decision'

for col in df.columns:
    if col == target_col:
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
print(f"Categorical features: {len(categorical_features)}")
print(f"Binary features: {len(binary_features)}")

# Convert target to binary
df['target_binary'] = (df['Recruiter_Decision'] == 'Hire').astype(int)

print("\nDataset loaded and ready for analysis!")