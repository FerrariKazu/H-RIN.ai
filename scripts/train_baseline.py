"""
Train and evaluate baseline classifiers for `AI_High_Performer` using engineered features.

Overview
- Selects features from `feat_*` and numeric columns while excluding leakage-prone fields.
- Optionally performs clean training with explicit leakage exclusions.
- Supports group-aware stratified splitting on `Resume_ID`, with instance-level fallback.
- Trains a baseline classifier and evaluates metrics (ROC AUC, PR AUC, F1, precision, recall).
- Sweeps thresholds to find best F1 and produces diagnostic plots (PR, confusion matrix).
- Saves artifacts to the specified output directory.

Usage
    python scripts/train_baseline.py --path data/enriched_dataset.csv --out_dir models/baseline

Inputs
- `enriched_dataset.csv` with `feat_*` columns and a target `AI_High_Performer`.

Outputs
- Plots and metrics files in `--out_dir`, including PR curve and confusion matrix images.

Notes
- Group-aware splitting helps prevent leakage; adjust `--group_col` to your ID column.
- Use `--fallback` to force pure-NumPy flow if scikit-learn is unavailable.
"""
# Import standard libraries for CLI parsing, JSON I/O, and filesystem paths.
import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

# Import numerical and tabular computing libraries.
import numpy as np
import pandas as pd

# Import plotting library for PR curves and confusion matrices.
import matplotlib.pyplot as plt
# Import pickle for model serialization when using scikit-learn.
import pickle


def select_features(df: pd.DataFrame, target_col: str) -> List[str]:
    # Include all feat_* columns
    feat_cols = [c for c in df.columns if c.startswith("feat_")]
    # Include numeric original columns (excluding target and text_all and tfidf_*)
    numeric_cols = [
        c
        for c in df.select_dtypes(include=[np.number]).columns
        if c != target_col and not c.startswith("tfidf_") and c not in feat_cols
    ]
    # Exclude text_all explicitly
    final_cols = [c for c in feat_cols + numeric_cols if c != "text_all"]
    return final_cols


def compute_sample_weights(y: np.ndarray) -> np.ndarray:
    # Minority class (0 = not high) should receive higher weight
    classes, counts = np.unique(y, return_counts=True)
    total = y.shape[0]
    class_weights = {cls: total / (2.0 * cnt) for cls, cnt in zip(classes, counts)}
    weights = np.array([class_weights[int(val)] for val in y], dtype=float)
    return weights


def _roc_auc_custom(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    # Mann-Whitney U based AUC
    pos_scores = y_prob[y_true == 1]
    neg_scores = y_prob[y_true == 0]
    n_pos = pos_scores.shape[0]
    n_neg = neg_scores.shape[0]
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    # ranks
    order = np.argsort(y_prob)
    ranks = np.empty_like(order)
    ranks[order] = np.arange(1, len(y_prob) + 1)
    rank_sum_pos = ranks[y_true == 1].sum()
    auc = (rank_sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    return float(auc)


def _precision_recall_curve_custom(y_true: np.ndarray, y_prob: np.ndarray):
    # Sort by score descending
    order = np.argsort(-y_prob)
    y_true_sorted = y_true[order]
    y_prob_sorted = y_prob[order]
    tp = np.cumsum(y_true_sorted == 1)
    fp = np.cumsum(y_true_sorted == 0)
    pos_total = (y_true == 1).sum()
    precision = tp / np.maximum(tp + fp, 1)
    recall = tp / np.maximum(pos_total, 1)
    thresholds = y_prob_sorted
    # Add (0,1) start point behavior typical for PR curves
    precision = np.r_[1.0, precision]
    recall = np.r_[0.0, recall]
    thresholds = np.r_[thresholds[0], thresholds]
    return precision, recall, thresholds


def _average_precision_custom(precision: np.ndarray, recall: np.ndarray) -> float:
    # AP as area under PR curve using recall steps
    ap = 0.0
    for i in range(1, len(recall)):
        ap += (recall[i] - recall[i - 1]) * precision[i]
    return float(ap)


def _confusion_matrix_custom(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
    # Compute counts for TN, FP, FN, TP manually.
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    return np.array([[tn, fp], [fn, tp]], dtype=int)


def _prec(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    # Precision: TP / predicted positives.
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    pp = int((y_pred == 1).sum())
    return float(tp / pp) if pp else 0.0


def _rec(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    # Recall: TP / actual positives.
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    p = int((y_true == 1).sum())
    return float(tp / p) if p else 0.0


def _f1(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    # F1: harmonic mean of precision and recall.
    p = _prec(y_true, y_pred)
    r = _rec(y_true, y_pred)
    return float((2 * p * r) / (p + r)) if (p + r) else 0.0


def evaluate_at_threshold(y_true: np.ndarray, y_prob: np.ndarray, threshold: float, use_sklearn: bool) -> Dict[str, float]:
    # Create binary predictions based on threshold.
    y_pred = (y_prob >= threshold).astype(int)
    if use_sklearn:
        # Use sklearn metrics if available.
        from sklearn.metrics import (
            roc_auc_score,
            average_precision_score,
            f1_score,
            precision_score,
            recall_score,
            confusion_matrix,
        )
        return {
            "roc_auc": roc_auc_score(y_true, y_prob),
            "pr_auc": average_precision_score(y_true, y_prob),
            "f1": f1_score(y_true, y_pred, zero_division=0),
            "precision": precision_score(y_true, y_pred, zero_division=0),
            "recall": recall_score(y_true, y_pred, zero_division=0),
            "threshold": threshold,
            "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
        }
    else:
        # Fall back to custom metric implementations.
        prec_curve, rec_curve, _ = _precision_recall_curve_custom(y_true, y_prob)
        ap = _average_precision_custom(prec_curve, rec_curve)
        roc = _roc_auc_custom(y_true, y_prob)
        return {
            "roc_auc": roc,
            "pr_auc": ap,
            "f1": _f1(y_true, y_pred),
            "precision": _prec(y_true, y_pred),
            "recall": _rec(y_true, y_pred),
            "threshold": threshold,
            "confusion_matrix": _confusion_matrix_custom(y_true, y_pred).tolist(),
        }


def find_best_f1_threshold(y_true: np.ndarray, y_prob: np.ndarray, use_sklearn: bool) -> Tuple[float, Dict[str, float]]:
    # Evaluate F1 across 200 thresholds
    thresholds = np.linspace(0.05, 0.95, 200)
    best_metrics = None
    best_th = 0.5
    best_f1 = -1.0
    for th in thresholds:
        metrics = evaluate_at_threshold(y_true, y_prob, th, use_sklearn)
        if metrics["f1"] > best_f1:
            best_f1 = metrics["f1"]
            best_th = th
            best_metrics = metrics
    return best_th, best_metrics


def plot_pr_curve(y_true: np.ndarray, y_prob: np.ndarray, best_threshold: float, out_path: Path, use_sklearn: bool):
    if use_sklearn:
        from sklearn.metrics import precision_recall_curve
        precision, recall, thresholds = precision_recall_curve(y_true, y_prob)
    else:
        precision, recall, thresholds = _precision_recall_curve_custom(y_true, y_prob)
    # Create PR plot figure.
    plt.figure(figsize=(6, 5))
    plt.plot(recall, precision, label="PR curve")
    # Mark best threshold point by recomputing precision/recall at that threshold
    y_pred_best = (y_prob >= best_threshold).astype(int)
    if use_sklearn:
        from sklearn.metrics import precision_score, recall_score
        prec_best = precision_score(y_true, y_pred_best, zero_division=0)
        rec_best = recall_score(y_true, y_pred_best, zero_division=0)
    else:
        prec_best = _prec(y_true, y_pred_best)
        rec_best = _rec(y_true, y_pred_best)
    plt.scatter([rec_best], [prec_best], color="red", label=f"Best F1 @ {best_threshold:.2f}")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision–Recall Curve (Positive=1)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def plot_confusion_matrix(cm: np.ndarray, out_path: Path):
    # Create confusion matrix visualization.
    plt.figure(figsize=(4, 4))
    plt.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    plt.title("Confusion Matrix")
    plt.colorbar()
    tick_marks = np.arange(2)
    plt.xticks(tick_marks, ["Not High (0)", "High (1)"])
    plt.yticks(tick_marks, ["Not High (0)", "High (1)"])
    thresh = cm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(j, i, format(int(cm[i, j])), horizontalalignment="center", color="white" if cm[i, j] > thresh else "black")
    plt.ylabel("True label")
    plt.xlabel("Predicted label")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def main():
    # Configure CLI to control training options and outputs.
    parser = argparse.ArgumentParser(description="Train and evaluate baseline classifiers for AI_High_Performer.")
    # Path to enriched dataset containing engineered features.
    parser.add_argument("--path", default="enriched_dataset.csv", help="Path to enriched dataset CSV.")
    # Output directory for metrics, models, and plots.
    parser.add_argument("--out_dir", default=".", help="Output directory for artifacts.")
    # Force fallback mode without scikit-learn/SciPy.
    parser.add_argument("--fallback", action="store_true", help="Force pure-NumPy logistic training (avoid scikit-learn/SciPy).")
    # Clean mode disables leakage-prone columns and saves with _clean suffix.
    parser.add_argument("--clean", action="store_true", help="Enable leakage-clean training and save _clean artifacts.")
    parser.add_argument(
        "--drop_cols",
        nargs="*",
        default=["AI Score (0-100)", "AI Score (0-100)_reflect_log", "Resume_ID"],
        help="Columns to drop from training features to avoid leakage.",
    )
    # Argument for the column used for group-aware splitting, not used as a feature.
    parser.add_argument("--group_col", default="Resume_ID", help="Grouping column for group-aware split (not used as feature).")
    # Parse the command-line arguments provided by the user.
    args = parser.parse_args()

    # Prepare the output directory for saving artifacts.
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load the enriched dataset from the specified path.
    df = pd.read_csv(args.path)
    # Define the target column name.
    target_col = "AI_High_Performer"
    # Check if the target column exists in the DataFrame, handling case insensitivity.
    if target_col not in df.columns:
        lower_map = {c.lower(): c for c in df.columns}
        if target_col.lower() in lower_map:
            target_col = lower_map[target_col.lower()]
        else:
            # Raise an error if the target column is not found.
            raise KeyError("AI_High_Performer target column not found.")

    # Select features for the model.
    feature_cols = select_features(df, target_col)
    # Drop specified leakage-prone columns and the grouping column from the features.
    dropped_present = []
    for col in set(args.drop_cols + [args.group_col]):
        if col in feature_cols:
            feature_cols.remove(col)
            dropped_present.append(col)
    # Build the feature matrix (X) and the numeric target array (y).
    X = df[feature_cols].copy()
    y = df[target_col].copy()
    # Convert target to numeric, fill NaNs with 0, and cast to integer.
    y = pd.to_numeric(y, errors="coerce").fillna(0).astype(int).values

    # Define a function for stratified group splitting.
    def stratified_group_split(df_all: pd.DataFrame, X_df: pd.DataFrame, y_arr: np.ndarray, group_col: str, test_size=0.2, random_state=42):
        # If the group column is not present, fall back to instance-level stratification.
        if group_col not in df_all.columns:
            # Initialize a random number generator.
            rng = np.random.default_rng(random_state)
            # Get indices for positive and negative samples.
            idx_pos = np.where(y_arr == 1)[0]
            idx_neg = np.where(y_arr == 0)[0]
            # Shuffle the indices.
            rng.shuffle(idx_pos)
            rng.shuffle(idx_neg)
            # Determine the number of positive and negative samples for the test set.
            n_pos_test = int(len(idx_pos) * test_size)
            n_neg_test = int(len(idx_neg) * test_size)
            # Combine indices for the test set.
            test_idx = np.r_[idx_pos[:n_pos_test], idx_neg[:n_neg_test]]
            # Combine indices for the training set.
            train_idx = np.r_[idx_pos[n_pos_test:], idx_neg[n_neg_test:]]
            # Shuffle the test and train indices.
            rng.shuffle(test_idx)
            rng.shuffle(train_idx)
            # Return the split dataframes and arrays.
            return X_df.iloc[train_idx], X_df.iloc[test_idx], y_arr[train_idx], y_arr[test_idx]
        # Build group-wise labels using the mean of the target within each group.
        grp = df_all[[group_col, target_col]].copy()
        # Convert target to numeric, fill NaNs with 0, and cast to integer.
        grp[target_col] = pd.to_numeric(grp[target_col], errors="coerce").fillna(0).astype(int)
        # Aggregate target mean by group.
        agg = grp.groupby(group_col)[target_col].mean()
        # Group label is the rounded mean (majority label per group).
        grp_labels = (agg >= 0.5).astype(int)
        # Initialize a random number generator.
        rng = np.random.default_rng(random_state)
        # Get positive and negative groups.
        pos_groups = np.array(grp_labels[grp_labels == 1].index)
        neg_groups = np.array(grp_labels[grp_labels == 0].index)
        # Shuffle the groups.
        rng.shuffle(pos_groups)
        rng.shuffle(neg_groups)
        # Determine the number of positive and negative groups for the test set.
        n_pos_test = int(len(pos_groups) * test_size)
        n_neg_test = int(len(neg_groups) * test_size)
        # Combine groups for the test set.
        test_groups = set(np.r_[pos_groups[:n_pos_test], neg_groups[:n_neg_test]].tolist())
        # Combine groups for the training set.
        train_groups = set(np.r_[pos_groups[n_pos_test:], neg_groups[n_neg_test:]].tolist())
        # Map rows to train/validation by group membership.
        is_test = df_all[group_col].isin(test_groups).values
        is_train = df_all[group_col].isin(train_groups).values
        # Split the dataframes and arrays.
        X_train_df = X_df[is_train]
        X_val_df = X_df[is_test]
        y_train_arr = y_arr[is_train]
        y_val_arr = y_arr[is_test]
        # Return the split data.
        return X_train_df, X_val_df, y_train_arr, y_val_arr

    # Perform group-aware stratified split to build training and validation sets.
    X_train, X_val, y_train, y_val = stratified_group_split(df, X, y, args.group_col, test_size=0.2, random_state=42)

    # Decide whether to use scikit-learn or fallback to pure NumPy implementation.
    use_fallback = args.fallback
    try:
        # Attempt to use scikit-learn if not in fallback mode.
        if not use_fallback:
            # Import scikit-learn components for pipelines and models.
            from sklearn.pipeline import Pipeline
            from sklearn.compose import ColumnTransformer
            from sklearn.impute import SimpleImputer
            from sklearn.linear_model import LogisticRegression
            from sklearn.ensemble import GradientBoostingClassifier

            # Define numeric features.
            numeric_features = feature_cols
            # Create a preprocessor for numeric features by imputing medians.
            preprocessor = ColumnTransformer(
                transformers=[("num", SimpleImputer(strategy="median"), numeric_features)],
                remainder="drop",
            )

            # Create a logistic regression pipeline with class balancing.
            lr_pipeline = Pipeline(
                steps=[
                    ("pre", preprocessor),
                    ("clf", LogisticRegression(max_iter=2000, class_weight="balanced", solver="lbfgs")),
                ]
            )

            # Create a gradient boosting pipeline as an alternative baseline.
            gb_pipeline = Pipeline(
                steps=[
                    ("pre", preprocessor),
                    ("clf", GradientBoostingClassifier(random_state=42)),
                ]
            )

            # Fit the logistic regression model and evaluate on the validation set.
            lr_pipeline.fit(X_train, y_train)
            lr_val_prob = lr_pipeline.predict_proba(X_val)[:, 1]
            # Find the best F1-optimal threshold and metrics for logistic regression.
            lr_best_th, lr_metrics = find_best_f1_threshold(y_val, lr_val_prob, use_sklearn=True)
            # Extract the confusion matrix for logistic regression.
            lr_cm = np.array(lr_metrics["confusion_matrix"])  # type: ignore

            # Fit the gradient boosting model, using sample weights to handle imbalance.
            sw_train = compute_sample_weights(y_train)
            gb_pipeline.fit(X_train, y_train, clf__sample_weight=sw_train)
            gb_val_prob = gb_pipeline.predict_proba(X_val)[:, 1]
            # Find the best F1-optimal threshold and metrics for gradient boosting.
            gb_best_th, gb_metrics = find_best_f1_threshold(y_val, gb_val_prob, use_sklearn=True)
            # Extract the confusion matrix for gradient boosting.
            gb_cm = np.array(gb_metrics["confusion_matrix"])  # type: ignore

            # Choose the better of the two models based on F1 score.
            best_name = "logistic_regression" if lr_metrics["f1"] >= gb_metrics["f1"] else "gradient_boosting"
            best_pipeline = lr_pipeline if best_name == "logistic_regression" else gb_pipeline
            best_metrics = lr_metrics if best_name == "logistic_regression" else gb_metrics
            best_prob = lr_val_prob if best_name == "logistic_regression" else gb_val_prob
            best_th = lr_best_th if best_name == "logistic_regression" else gb_best_th
            best_cm = lr_cm if best_name == "logistic_regression" else gb_cm

            # Set flag to indicate scikit-learn model saving.
            save_sklearn = True
            # Initialize coefficient map.
            coef_map = None
            # If the best model is logistic regression, extract coefficients.
            if best_name == "logistic_regression":
                # Get the classifier and imputer from the pipeline.
                clf = best_pipeline.named_steps["clf"]
                imputer = best_pipeline.named_steps["pre"]
                # Assume SimpleImputer does not change feature ordering; extract coefficients.
                coefs = clf.coef_[0]
                coef_map = {feature_cols[i]: float(coefs[i]) for i in range(len(feature_cols))}
        else:
            # Force fallback mode if scikit-learn/SciPy is not to be used.
            raise ImportError("Forced fallback mode")
    except Exception:
        # Fallback to pure NumPy logistic regression with class weights if scikit-learn fails or is forced.
        use_fallback = True
        # Convert training and validation data to float arrays.
        X_train_vals = X_train.values.astype(float)
        X_val_vals = X_val.values.astype(float)
        # Initialize lists for medians and modes for imputation.
        medians = []
        modes = []
        # Create copies for imputed data.
        X_train_imp = X_train_vals.copy()
        X_val_imp = X_val_vals.copy()
        # Iterate through each feature column for imputation.
        for j, col in enumerate(feature_cols):
            col_train = X_train_vals[:, j]
            # Determine if the column is binary (0/1) by checking unique values.
            uniq = np.unique(col_train[~np.isnan(col_train)])
            is_binary = set(np.round(uniq).tolist()).issubset({0, 1})
            if is_binary:
                # Calculate mode (most frequent value, ties go to 0).
                counts0 = np.sum(col_train == 0)
                counts1 = np.sum(col_train == 1)
                mode_val = 1.0 if counts1 > counts0 else 0.0
                modes.append(mode_val)
                # Fill NaNs with the calculated mode.
                X_train_imp[np.isnan(X_train_imp[:, j]), j] = mode_val
                X_val_imp[np.isnan(X_val_imp[:, j]), j] = mode_val
                # Append median for consistency, though not used for binary imputation.
                medians.append(float(np.nanmedian(col_train)))
            else:
                # Calculate median for non-binary columns.
                m = float(np.nanmedian(col_train))
                medians.append(m)
                modes.append(float("nan"))
                # Fill NaNs with the calculated median.
                X_train_imp[np.isnan(X_train_imp[:, j]), j] = m
                X_val_imp[np.isnan(X_val_imp[:, j]), j] = m
        # Standardize the imputed data.
        mean = X_train_imp.mean(axis=0)
        std = X_train_imp.std(axis=0) + 1e-8
        X_train_std = (X_train_imp - mean) / std
        X_val_std = (X_val_imp - mean) / std

        # Train logistic regression with weighted loss using pure NumPy.
        rng = np.random.default_rng(42)
        # Initialize weights and bias.
        w = rng.normal(0, 0.01, size=X_train_std.shape[1])
        b = 0.0
        # Compute sample weights for imbalanced classes.
        weights = compute_sample_weights(y_train)
        # Set learning rate and number of epochs.
        lr = 0.05
        epochs = 3000
        # Gradient descent loop.
        for _ in range(epochs):
            # Calculate linear combination.
            z = X_train_std @ w + b
            # Apply sigmoid function to get probabilities.
            p = 1 / (1 + np.exp(-z))
            # Calculate gradients of weighted binary cross-entropy loss.
            grad_w = (X_train_std * weights[:, None]).T @ (p - y_train) / X_train_std.shape[0]
            grad_b = np.mean((p - y_train) * weights)
            # Update weights and bias.
            w -= lr * grad_w
            b -= lr * grad_b

        # Calculate validation probabilities using the trained NumPy model.
        val_prob = 1 / (1 + np.exp(-(X_val_std @ w + b)))
        # Find the best F1-optimal threshold and metrics for the NumPy model.
        best_th, best_metrics = find_best_f1_threshold(y_val, val_prob, use_sklearn=False)
        # Extract the confusion matrix for the NumPy model.
        best_cm = np.array(best_metrics["confusion_matrix"])  # type: ignore
        best_prob = val_prob
        best_name = "pure_numpy_logistic"
        # Store model object details for NumPy implementation.
        model_obj = {
            "type": best_name,
            "weights": w.tolist(),
            "bias": b,
            "feature_columns": feature_cols,
            "imputer_medians": medians,
            "imputer_modes": modes,
            "scaler_mean": mean.tolist(),
            "scaler_std": std.tolist(),
        }
        # Set flag to indicate NumPy fallback implementation.
        save_sklearn = False  # Flag indicating we used the numpy fallback implementation, not sklearn
        # Map feature names to their learned weights for interpretability.
        coef_map = {feature_cols[i]: float(w[i]) for i in range(len(feature_cols))}  # Map feature names to their learned weights for interpretability

    # Save artifacts to the output directory.
    suffix = "_clean" if args.clean else ""  # Suffix for artifacts if clean mode is active.
    metrics_path = out_dir / f"metrics_baseline{suffix}.txt"  # Path for textual metrics summary.
    pr_path = out_dir / f"pr_curve{suffix}.png"  # Path for the precision–recall curve plot.
    cm_path = out_dir / f"confusion_matrix{suffix}.png"  # Path for the confusion matrix plot.
    model_path = out_dir / f"model{suffix}.pkl"  # Path for the trained model object (pickle).
    cols_path = out_dir / f"columns{suffix}.json"  # Path for selected columns and preprocessing info.
    coef_path = out_dir / ("coefficients.csv" if not args.clean else "coefficients_clean.csv")  # Path for coefficients CSV, depends on clean mode.
    leakage_path = out_dir / "leakage_audit.txt"  # Path for a leakage audit note when clean mode is used.

    # Build a human-readable metrics summary.
    lines = []  # List to collect lines for the metrics summary file.
    lines.append("Baseline Model Evaluation (Validation Set)")  # Title.
    lines.append("-----------------------------------------")  # Underline.
    lines.append(f"Features used: {len(feature_cols)} columns")  # Report the number of features used.
    lines.append(f"Model chosen: {best_name}")  # State which model implementation was chosen.
    lines.append(
        f"ROC AUC: {best_metrics['roc_auc']:.4f}\nPR AUC: {best_metrics['pr_auc']:.4f}\nF1: {best_metrics['f1']:.4f}\n"
        f"Precision: {best_metrics['precision']:.4f}\nRecall: {best_metrics['recall']:.4f}\n"
        f"Chosen threshold (F1-optimal): {best_metrics['threshold']:.2f}"
    )
    lines.append("Confusion Matrix:")  # Header for confusion matrix.
    cm_rows = [
        f"[TN={best_cm[0,0]} FP={best_cm[0,1]}]",
        f"[FN={best_cm[1,0]} TP={best_cm[1,1]}]",
    ]
    lines.extend(cm_rows)
    # Include top 20 coefficients by absolute value if available.
    if coef_map is not None:  # Check if coefficient map exists.
        sorted_items = sorted(coef_map.items(), key=lambda kv: abs(kv[1]), reverse=True)  # Sort by absolute coefficient magnitude.
        top20 = sorted_items[:20]  # Take top 20 for brevity
        lines.append("Top 20 features by |coefficient|:")  # Section header
        for name, val in top20:  # Append each feature and its coefficient
            lines.append(f"- {name}: {val:.6f} (|coef|={abs(val):.6f})")
    # Write the metrics summary to disk.
    Path(metrics_path).write_text("\n".join(lines) + "\n", encoding="utf-8")  # Write the metrics summary to disk

    # Generate and save the Precision-Recall curve plot for validation.
    plot_pr_curve(y_val, best_prob, best_th, pr_path, use_sklearn=not use_fallback)  # Generate and save PR curve plot for validation
    # Generate and save the confusion matrix plot.
    plot_confusion_matrix(best_cm, cm_path)  # Generate and save confusion matrix plot

    # Save the model object.
    with open(model_path, "wb"):  # Open model path for writing in binary mode
        pickle.dump(model_obj, open(model_path, "wb"))  # Serialize and save the model object using pickle

    # Save coefficients CSV for interpretability.
    if coef_map is not None:  # If we have coefficients to export
        import csv  # Import CSV writer (local import keeps top-level imports tidy)
        # Primary coefficients file (with clean suffix if requested).
        with open(coef_path, "w", newline="", encoding="utf-8") as f:  # Create the coefficients CSV file
            writer = csv.writer(f)  # CSV writer instance
            writer.writerow(["feature", "coefficient", "abs_coefficient"])  # Header row for readability
            for name, val in sorted(coef_map.items(), key=lambda kv: abs(kv[1]), reverse=True):  # Sort by magnitude
                writer.writerow([name, f"{val:.6f}", f"{abs(val):.6f}"])  # Write each feature and its coefficient value
        # Also write a non-suffixed coefficients.csv for convenience.
        plain_coef_path = out_dir / "coefficients.csv"  # Also write a non-suffixed version for convenience
        with open(plain_coef_path, "w", newline="", encoding="utf-8") as f:  # Open the plain coefficients file
            writer = csv.writer(f)  # CSV writer instance
            writer.writerow(["feature", "coefficient", "abs_coefficient"])  # Header row
            for name, val in sorted(coef_map.items(), key=lambda kv: abs(kv[1]), reverse=True):  # Same sort order
                writer.writerow([name, f"{val:.6f}", f"{abs(val):.6f}"])  # Write feature and coefficient values

    columns_info = {  # Describe features and preprocessing choices used by this run
        "target": target_col,
        "feature_columns": feature_cols,
        "preprocessing": {
            "numeric": {
                "imputer": "median",
            },
            "exclude": ["text_all"],
        },
        "threshold": best_th,
        "mode": best_name,
    }
    cols_path.write_text(json.dumps(columns_info, indent=2), encoding="utf-8")  # Save columns and preprocessing metadata as JSON

    # Write leakage audit when clean mode requested
    if args.clean:  # If clean mode was active, also write an audit explaining leakage-related drops
        audit_lines = []  # Collect lines for leakage audit
        audit_lines.append("Leakage Audit")  # Header
        audit_lines.append("--------------")  # Underline
        audit_lines.append(f"Grouping column: {args.group_col} (used only to enforce group-aware split)")  # Document group column usage
        audit_lines.append("Dropped features to reduce leakage:")  # Section heading
        for col in args.drop_cols:  # List each dropped column
            audit_lines.append(f"- {col}")
        audit_lines.append("")  # Blank line separator
        audit_lines.append("Rationale:")  # Rationale header
        audit_lines.append("- 'AI Score (0-100)' and its log variant are highly correlated with the target and can introduce target leakage.")  # Explain AI Score drop
        audit_lines.append("- 'Resume_ID' is an identifier, not predictive content; excluding it avoids group mixing in features.")  # Explain ID drop
        audit_lines.append("")  # Blank line
        audit_lines.append(f"Features used after dropping: {len(feature_cols)}")  # Count final features used
        leakage_path.write_text("\n".join(audit_lines) + "\n", encoding="utf-8")  # Write the audit file to disk

    print(f"Saved metrics: {metrics_path.resolve()}")  # Inform the user where metrics summary was saved
    print(f"Saved PR curve: {pr_path.resolve()}")  # Inform the user where PR curve image was saved
    print(f"Saved confusion matrix: {cm_path.resolve()}")  # Inform the user where confusion matrix image was saved
    print(f"Saved model: {model_path.resolve()}")  # Inform the user where the model pickle was saved
    print(f"Saved columns description: {cols_path.resolve()}")  # Inform the user where columns metadata was saved
    if coef_map is not None:  # If coefficients were exported
        print(f"Saved coefficients: {coef_path.resolve()}")  # Report path to main coefficients file
        print(f"Saved coefficients (plain): {(out_dir / 'coefficients.csv').resolve()}")  # Report path to plain coefficients file
    if args.clean:  # If leakage audit was generated
        print(f"Saved leakage audit: {leakage_path.resolve()}")  # Report path to leakage audit


if __name__ == "__main__":  # Standard Python entry point guard
    main()  # Invoke the main function when the script is executed directly