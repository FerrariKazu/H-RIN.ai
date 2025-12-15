print("DEBUG: Script started...")
import sys
import os
# Fix for Sklearn/MKL hang
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"

print("DEBUG: Importing pandas...")
import pandas as pd
print("DEBUG: Importing numpy...")
import numpy as np
print("DEBUG: Importing matplotlib...")
import matplotlib.pyplot as plt
print("DEBUG: Importing sklearn...")
from sklearn.metrics import confusion_matrix, accuracy_score, classification_report
print("DEBUG: Importing joblib...")
import joblib
print("DEBUG: Imports complete.")

# Set paths
DATA_PATH = r"pipeline_v4/data/normalized_dataset_v4_balanced.csv"
MODEL_PATH = r"models/latest/ai_score_model.pkl"
OUTPUT_DIR = r"pipeline_v4/plots"


def main():
    base_dir = r"pipeline_v4/data"
    files = ["X_train_final.csv", "X_val_final.csv", "X_test_final.csv"]
    
    dfs = []
    for f in files:
        path = os.path.join(base_dir, f)
        if os.path.exists(path):
            print(f"Loading {path}...")
            dfs.append(pd.read_csv(path))
        else:
            print(f"Warning: {path} not found.")
            
    if not dfs:
        print("No data loaded.")
        return
        
    df = pd.concat(dfs, ignore_index=True)
    print(f"Total rows: {len(df)}")

    # Detect target
    target_col = None
    possible_targets = ["AI_High_Performer", "target", "target_binary", "High_Performer"]
    for t in possible_targets:
        if t in df.columns:
            target_col = t
            break
            
    if not target_col:
        # Check last column
        print(f"Target not found in {possible_targets}. Columns: {df.columns.tolist()[:5]} ... {df.columns.tolist()[-5:]}")
        # Try finding column with binary values 0/1 and distinct name
        # Assuming last column is target as seen in "...,1"
        target_col = df.columns[-1]
        print(f"Using last column as target: {target_col}")

    print(f"Target: {target_col}")
    
    y = df[target_col]
    X = df.drop(columns=[target_col])
    
    # Load Model
    model_path = MODEL_PATH
    if not os.path.exists(model_path):
        print(f"Error: Model not found at {model_path}")
        return
    
    print(f"Loading model from {model_path}...")
    try:
        model = joblib.load(model_path)
    except Exception as e:
        print(f"Failed to load model: {e}")
        return
        
    # Align features
    # Model might expect specific columns. 
    # If model is sklearn pipeline, it might handle it. If simple estimator, cols must match.
    # We check if model has feature_names_in_
    if hasattr(model, "feature_names_in_"):
        model_feats = model.feature_names_in_
        # Drop extra columns, add missing?
        # For now, select assumption
        missing = [c for c in model_feats if c not in X.columns]
        if missing:
            print(f"Warning: Missing features in data: {missing}")
        X = X[model_feats]
        
    print("Predicting on ALL rows...")
    y_pred = model.predict(X)
    
    # Confusion Matrix
    cm = confusion_matrix(y, y_pred)
    print("Confusion Matrix:")
    print(cm)
    
    # Plot
    # Plot using Matplotlib only (Seaborn hanging)
    plt.figure(figsize=(8, 6))
    plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    plt.title('Confusion Matrix (Full Dataset: Train+Val+Test)')
    plt.colorbar()
    
    classes = ['Low/Avg', 'High Performer']
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=0)
    plt.yticks(tick_marks, classes)
    
    # Text annotations
    import itertools
    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, format(cm[i, j], 'd'),
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")
                 
    plt.tight_layout()
    plt.ylabel('Actual')
    plt.xlabel('Predicted')
    
    out_path = os.path.join(OUTPUT_DIR, "confusion_matrix_full_dataset_v4.png")
    plt.savefig(out_path)
    print(f"Saved plot to {out_path}")


if __name__ == "__main__":
    main()
