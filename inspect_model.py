import pickle
import os
import sys
import numpy as np

base_dir = r"c:\Users\FerrariKazu\Documents\AI Folder\P3\AM-DS-01\agent\ml"
model_b_path = os.path.join(base_dir, "model.pkl")

with open(model_b_path, 'rb') as f:
    model_b = pickle.load(f)

import json

with open(os.path.join(base_dir, "config.json"), 'r') as f:
    config = json.load(f)

features = config['features_used']
# Model B has one extra feature: AI Score
features_b = features + ["AI Score"]

params = model_b['preproc']
weights = model_b['weights']

bool_flags = params['bool_flags']

# Create list of tuples
feature_data = []
for i, feature in enumerate(features_b):
    # params might not have entry for AI Score if it wasn't in the original feature list?
    # Actually, evaluator.py says:
    # X_b = self._impute_and_scale(df_features, params_b)
    # X_b_combined = np.column_stack([X_b, np.array([[ai_score_std]])])
    # So params_b only covers the base features.
    
    if i < len(features):
        mean = params['mean'][i]
        std = params['std'][i]
        flag = bool_flags[i]
    else:
        # AI Score
        mean = 0.0 # Placeholder
        std = 1.0 # Placeholder
        flag = False
        
    weight = weights[i]
    feature_data.append((feature, mean, std, weight, flag))

# Sort by absolute weight
feature_data.sort(key=lambda x: abs(x[3]), reverse=True)

with open("weights_b.txt", "w") as f:
    f.write(f"{'Feature':<40} | {'Mean':<10} | {'Std':<10} | {'Weight':<10} | {'Bool':<5}\n")
    f.write("-" * 90 + "\n")

    for item in feature_data:
        f.write(f"{item[0]:<40} | {item[1]:<10.2f} | {item[2]:<10.2f} | {item[3]:<10.2f} | {str(item[4]):<5}\n")

    f.write("-" * 90 + "\n")
    f.write(f"Intercept: {weights[-1]}\n")

print("-" * 80)
print(f"Intercept: {weights[-1]}")
