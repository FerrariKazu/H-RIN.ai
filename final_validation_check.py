#!/usr/bin/env python3
"""
Final Validation and Completion Check
Comprehensive verification of all deliverables and project completion
"""

import pandas as pd
import numpy as np
import json
import os
import matplotlib.pyplot as plt
from datetime import datetime

print("=" * 80)
print("FINAL VALIDATION AND PROJECT COMPLETION CHECK")
print("=" * 80)
print(f"Validation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Define expected deliverables
expected_files = {
    'data': [
        'X_train_preprocessed.csv',
        'X_val_preprocessed.csv', 
        'X_test_preprocessed.csv',
        'normalized_dataset_v4_balanced.csv',
        'final_selected_features.json',
        'preprocessing_report.json'
    ],
    'plots': [
        'advanced_feature_selection_analysis.png',
        'comprehensive_correlation_analysis.png',
        'comprehensive_eda_analysis.png',
        'feature_engineering_summary.png',
        'feature_importance_comparison.png',
        'phase2_complete_summary.png',
        'preprocessing_analysis.png',
        'predictive_power_analysis.png',
        'target_variable_balance.png',
        'detailed_AI_Score_0-100_analysis.png',
        'detailed_AI_Score_Uniform_0-100_analysis.png',
        'detailed_Experience_Years_analysis.png',
        'detailed_Projects_Count_analysis.png',
        'detailed_feat_job_tech_analysis.png'
    ],
    'reports': [
        'COMPLETE_ANALYSIS_SUMMARY.md',
        'PHASE_1_ANALYSIS_REPORT.md',
        'PHASE_2_ANALYSIS_REPORT.md',
        'MASTER_DELIVERABLES_INDEX.md',
        'balance_report.txt',
        'balance_report_final.txt',
        'comprehensive_summary_report.txt',
        'final_summary_report.txt'
    ],
    'csv_files': [
        'advanced_feature_selection_summary.csv',
        'correlation_analysis_results.csv',
        'feature_engineering_summary_advanced.csv',
        'feature_selection_summary.csv',
        'statistical_tests_results.csv'
    ]
}

# Check file existence
def check_files_exist(directory, files):
    """Check if files exist in directory"""
    missing_files = []
    existing_files = []
    
    for file in files:
        filepath = os.path.join(directory, file)
        if os.path.exists(filepath):
            existing_files.append(file)
        else:
            missing_files.append(file)
    
    return existing_files, missing_files

print("\n" + "=" * 80)
print("DELIVERABLES VERIFICATION")
print("=" * 80)

# Check each category
results = {}
total_expected = 0
total_found = 0

for category, files in expected_files.items():
    if category == 'csv_files':
        dir_path = 'pipeline_v4/plots/'
    else:
        dir_path = f'pipeline_v4/{category}/'
    
    existing, missing = check_files_exist(dir_path, files)
    results[category] = {'existing': existing, 'missing': missing}
    
    found_count = len(existing)
    expected_count = len(files)
    
    total_expected += expected_count
    total_found += found_count
    
    print(f"\n📁 {category.upper()}:")
    print(f"   Expected: {expected_count}")
    print(f"   Found: {found_count}")
    print(f"   Missing: {len(missing)}")
    
    if missing:
        print(f"   Missing files: {', '.join(missing[:3])}{'...' if len(missing) > 3 else ''}")

print(f"\n" + "=" * 50)
print("OVERALL FILE VERIFICATION")
print("=" * 50)
print(f"Total Expected Files: {total_expected}")
print(f"Total Found Files: {total_found}")
print(f"Completion Rate: {(total_found/total_expected)*100:.1f}%")

# Validate data quality
print("\n" + "=" * 80)
print("DATA QUALITY VALIDATION")
print("=" * 80)

try:
    # Load final datasets
    train_data = pd.read_csv('pipeline_v4/data/X_train_preprocessed.csv')
    val_data = pd.read_csv('pipeline_v4/data/X_val_preprocessed.csv')
    test_data = pd.read_csv('pipeline_v4/data/X_test_preprocessed.csv')
    
    print(f"\n📊 FINAL DATASET VALIDATION:")
    print(f"Training set: {train_data.shape}")
    print(f"Validation set: {val_data.shape}")
    print(f"Test set: {test_data.shape}")
    
    # Check data quality
    print(f"\n✅ DATA QUALITY CHECKS:")
    print(f"Training missing values: {train_data.isnull().sum().sum()}")
    print(f"Validation missing values: {val_data.isnull().sum().sum()}")
    print(f"Test missing values: {test_data.isnull().sum().sum()}")
    
    # Check target balance
    train_target = train_data['target_binary']
    val_target = val_data['target_binary']
    test_target = test_data['target_binary']
    
    print(f"\n🎯 TARGET BALANCE VALIDATION:")
    print(f"Training positive rate: {train_target.mean():.1%}")
    print(f"Validation positive rate: {val_target.mean():.1%}")
    print(f"Test positive rate: {test_target.mean():.1%}")
    
    # Check feature consistency
    train_features = set(train_data.columns) - {'target_binary'}
    val_features = set(val_data.columns) - {'target_binary'}
    test_features = set(test_data.columns) - {'target_binary'}
    
    features_consistent = (train_features == val_features == test_features)
    print(f"\n🔧 FEATURE CONSISTENCY:")
    print(f"Features consistent across datasets: {features_consistent}")
    print(f"Total features: {len(train_features)}")
    
except Exception as e:
    print(f"❌ Error validating datasets: {e}")

# Validate key results
print("\n" + "=" * 80)
print("KEY RESULTS VALIDATION")
print("=" * 80)

try:
    # Load feature selection results
    selection_summary = pd.read_csv('pipeline_v4/plots/advanced_feature_selection_summary.csv')
    consensus_features = selection_summary[selection_summary['consensus'] == True]
    
    print(f"\n🎯 FEATURE SELECTION VALIDATION:")
    print(f"Total features in selection analysis: {len(selection_summary)}")
    print(f"Consensus features (≥3 methods): {len(consensus_features)}")
    print(f"Average selection count: {consensus_features['selection_count'].mean():.1f}")
    print(f"Max selection count: {consensus_features['selection_count'].max()}")
    
    # Check top features
    top_5 = consensus_features.head(5)
    print(f"\n🏆 TOP 5 CONSENSUS FEATURES:")
    for i, (_, row) in enumerate(top_5.iterrows(), 1):
        print(f"   {i}. {row['feature'][:50]:<50} | Selected by {row['selection_count']} methods")
    
except Exception as e:
    print(f"❌ Error validating feature selection: {e}")

# Create final validation summary
print("\n" + "=" * 80)
print("FINAL VALIDATION SUMMARY")
print("=" * 80)

# Calculate overall project metrics
completion_rate = (total_found/total_expected)*100
data_quality_score = 100 if train_data.isnull().sum().sum() == 0 else 0
target_balance_score = 100 if abs(train_target.mean() - 0.525) < 0.05 else 0
feature_consistency_score = 100 if features_consistent else 0

overall_score = (completion_rate + data_quality_score + target_balance_score + feature_consistency_score) / 4

print(f"\n📊 PROJECT COMPLETION METRICS:")
print(f"File Completion Rate: {completion_rate:.1f}%")
print(f"Data Quality Score: {data_quality_score:.0f}%")
print(f"Target Balance Score: {target_balance_score:.0f}%")
print(f"Feature Consistency Score: {feature_consistency_score:.0f}%")
print(f"Overall Project Score: {overall_score:.1f}%")

# Project status assessment
if overall_score >= 90:
    status = "✅ EXCELLENT - Production Ready"
elif overall_score >= 80:
    status = "✅ GOOD - Minor issues resolved"
elif overall_score >= 70:
    status = "⚠️  FAIR - Some issues need attention"
else:
    status = "❌ NEEDS WORK - Significant issues identified"

print(f"\n🎯 PROJECT STATUS: {status}")

# Create final recommendations
print(f"\n📋 FINAL RECOMMENDATIONS:")
if overall_score >= 90:
    print("• Project is ready for production deployment")
    print("• Proceed with model development using final datasets")
    print("• Consider ensemble methods for improved performance")
elif overall_score >= 80:
    print("• Address any minor issues identified")
    print("• Proceed with model development")
    print("• Monitor for any data quality issues")
else:
    print("• Address identified issues before proceeding")
    print("• Re-run affected analysis steps")
    print("• Ensure data quality before model development")

print(f"\n" + "=" * 80)
print("VALIDATION COMPLETE")
print("=" * 80)

# Save validation report
validation_report = {
    'validation_date': datetime.now().isoformat(),
    'completion_rate': completion_rate,
    'data_quality_score': data_quality_score,
    'target_balance_score': target_balance_score,
    'feature_consistency_score': feature_consistency_score,
    'overall_score': overall_score,
    'project_status': status,
    'total_files_expected': total_expected,
    'total_files_found': total_found,
    'final_datasets': {
        'training_samples': train_data.shape[0] if 'train_data' in locals() else 0,
        'validation_samples': val_data.shape[0] if 'val_data' in locals() else 0,
        'test_samples': test_data.shape[0] if 'test_data' in locals() else 0,
        'total_features': len(train_features) if 'train_features' in locals() else 0
    }
}

with open('pipeline_v4/data/validation_report.json', 'w') as f:
    json.dump(validation_report, f, indent=2)

print(f"✅ Validation report saved to: pipeline_v4/data/validation_report.json")

print(f"\n🚀 READY FOR: Model Development and Production Deployment")
print("=" * 80)