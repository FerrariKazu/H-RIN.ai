"""  # Module docstring: describes the two-model pipeline’s purpose, inputs, outputs, and artifacts
Two-model training pipeline: regress `AI Score (0-100)` (Model A) and
classify `Recruiter_Decision` (Model B) using engineered features.

Overview
- Model A (regression): learns to predict `AI Score (0-100)` from standardized numeric
  and encoded categorical features. Reports CV metrics (MAE, RMSE, R², Pearson r, Spearman ρ)
  and saves OOF predictions and plots.
- Model B (classification): predicts recruiter readiness. Uses the same features plus the
  standardized Model A prediction as an additional feature. Evaluates PR/ROC, F1, precision,
  recall, calibration (Brier), and computes best-F1 and cost-optimal thresholds.
- Includes label discovery for `Recruiter_Decision` (case-insensitive aliases) and
  group-aware splitting via `Resume_ID`.
- Provides optional scikit-learn path if available; otherwise uses pure NumPy implementations.

Artifacts
- Metrics: `ai_score_cv_metrics.json`, `recruiter_cv_metrics.json`, `holdout_metrics.json`.
- Models: `ai_score_model.pkl`, `recruiter_model.pkl`, `recruiter_model_best.pkl`.
- Plots: scatter, error hist, PR curve, confusion matrix, reliability plots.
- Reports: `threshold_report.txt`, `step3_4_audit.txt`, `label_prep_report.txt`,
  `winsorization_compare.txt`, `imbalance_benchmark_report.json`.

Usage
    python train_two_model_pipeline.py --path enriched_dataset.csv --out_dir models/pipeline
    python train_two_model_pipeline.py --path enriched_dataset.csv --out_dir models/pipeline --use_sklearn

Inputs
- `enriched_dataset.csv` with engineered `feat_*` columns, `AI Score (0-100)`, and `Resume_ID`.
- Optional labels CSV (`--labels_path`) to merge `Recruiter_Decision` by key if missing;
  can specify `--recruiter_col` to override the decision column name.

Outputs
- Saved models, metrics, plots, and updated `pipeline_config.json` under `--out_dir`.

Notes
- The pipeline standardizes numeric features and encodes categoricals consistently.
- Winsorization and resampling strategies for Model B can be benchmarked and configured.
"""
import argparse  # Parses command-line arguments for configurable runs
import json  # Handles JSON serialization/deserialization for configs and metrics
from typing import Tuple, Dict  # Type hints for clarity and tooling
from sklearn.linear_model import LogisticRegression  # Import sklearn’s logistic regression
from sklearn.metrics import (
    precision_recall_curve,  # Standard PR curve utility
    average_precision_score,  # Area under PR curve (AP)
    roc_auc_score,  # ROC AUC computation
    f1_score,  # F1 metric
    precision_score,  # Precision metric
    recall_score,  # Recall metric
    brier_score_loss,  # Calibration (Brier) metric
    confusion_matrix,  # Confusion matrix utility
)
SKLEARN_AVAILABLE = True  # Flag indicating scikit-learn is usable
try:
    from imblearn.over_sampling import SMOTE  # type: ignore  # Attempt to import SMOTE for resampling
    IMB_AVAILABLE = True  # Flag for imbalanced-learn availability
except Exception:
    IMB_AVAILABLE = False  # If unavailable, skip SMOTE-based strategies
from pathlib import Path  # Filesystem path utility for robust IO
from typing import Dict, List, Tuple  # Additional type hints used across functions

import numpy as np  # NumPy for numeric operations and arrays
import pandas as pd  # Pandas for DataFrame manipulation
import matplotlib.pyplot as plt  # Matplotlib for plotting metrics and diagnostics
import pickle  # Pickle for model artifact serialization

def _normalize_name(name: str) -> str:  # Normalize column names (strip, lower, underscore)
    return (
        str(name)  # Ensure the input is a string
        .strip()  # Remove leading/trailing whitespace
        .lower()  # Lowercase for consistent matching
        .replace(" ", "_")  # Replace spaces with underscores
        .replace("-", "_")  # Replace dashes with underscores
    )

DECISION_ALIASES = {  # Known aliases for the recruiter decision column
    "recruiter_decision",
    "recruiterdecision",
    "recruiter_label",
    "decision",
    "advanceflag",
    "status",
    "finaldecision",
    "review_outcome",
}

KEY_ALIASES = ["resume_id", "id", "candidate_id"]  # Candidate/resume identifier aliases used when merging

POSITIVE_STRINGS = {"advance", "accept", "yes", "hire", "move forward"}  # Positive decision keywords
NEGATIVE_STRINGS = {"reject", "no", "decline"}  # Negative decision keywords

def _map_decision_series(s: pd.Series) -> pd.Series:  # Normalize a decision series to {0,1} with NaNs for unknowns
    # Try booleans
    if s.dtype == bool:  # If already boolean, convert True/False to 1/0
        return s.astype(int)
    # Try numeric
    s_num = pd.to_numeric(s, errors="coerce")  # Coerce to numeric; non-numeric becomes NaN
    if s_num.notna().any():  # If any numeric values exist
        # Map numerics {1,0} as-is; anything else becomes NaN
        mapped = s_num.where(s_num.isin([0, 1]))  # Keep only 0/1; set other numerics to NaN
        return mapped
    # Fallback to strings
    s_str = s.astype(str).str.strip().str.lower()  # Normalize string values for keyword matching
    mapped = pd.Series(index=s.index, dtype=float)  # Prepare a float series for {0.0,1.0}
    mapped[:] = np.nan  # Initialize as NaN
    mapped[s_str.isin(POSITIVE_STRINGS)] = 1.0  # Mark positive keywords as 1
    mapped[s_str.isin(NEGATIVE_STRINGS)] = 0.0  # Mark negative keywords as 0
    return mapped  # Return normalized binary/NaN series

def _detect_decision_col(df: pd.DataFrame) -> str | None:  # Identify recruiter decision column by alias
    norm_map = {_normalize_name(c): c for c in df.columns}  # Map normalized names to original
    for alias in DECISION_ALIASES:  # Iterate through known aliases
        if alias in norm_map:  # If alias exists, return the original column name
            return norm_map[alias]
    return None  # Return None if not found

def _detect_key_col(df: pd.DataFrame) -> str | None:  # Identify key (ID) column by alias
    norm_map = {_normalize_name(c): c for c in df.columns}  # Map normalized names to original
    for alias in KEY_ALIASES:  # Iterate through key aliases
        if alias in norm_map:  # If alias exists, return the original column name
            return norm_map[alias]
    return None  # Return None if not found

def load_feature_columns(df: pd.DataFrame, clean_cols_path: Path) -> List[str]:  # Determine feature columns for modeling
    if clean_cols_path.exists():  # If a clean columns config exists, load it
        cfg = json.loads(clean_cols_path.read_text(encoding="utf-8"))  # Read JSON config text
        cols = [c for c in cfg.get("feature_columns", [])]  # Use specified feature columns
    else:
        feat_cols = [c for c in df.columns if c.startswith("feat_")]  # Collect engineered feature columns
        numeric_cols = [
            c for c in df.select_dtypes(include=[np.number]).columns  # Numeric columns
            if c not in feat_cols  # Avoid duplicating engineered feats
        ]
        cols = feat_cols + numeric_cols  # Combine engineered + numeric
    # Explicit excludes
    excludes = {
        "AI Score (0-100)",  # Target for Model A; exclude from features
        "AI Score (0-100)_reflect_log",  # Leakage-prone variant; exclude
        "AI Score (Uniform 0-100)",  # Uniform AI Score; exclude from features
        "AI_High_Performer",  # Label shorthand; exclude from features
        "text_all",  # Raw text; not used directly here
        "Resume_ID",  # Group identifier; not a predictive feature
        "Recruiter_Decision",  # Target for Recruiter Model; exclude from features
    }
    return [c for c in cols if c not in excludes]  # Final filtered feature list


def infer_feature_types(df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, List[str]]:  # Split features into numeric/boolean/categorical
    numeric = []  # Numeric columns (non-binary)
    boolean = []  # Binary columns (0/1 or bool)
    categoricals = []  # Non-numeric, non-boolean columns
    for c in feature_cols:  # Inspect each feature
        s = df[c]  # Column series
        if pd.api.types.is_numeric_dtype(s):  # Numeric dtype
            # check if binary 0/1
            vals = pd.to_numeric(s, errors="coerce")  # Coerce to numeric
            uniq = np.unique(vals.dropna().values)  # Unique non-NaN values
            if set(np.round(uniq).tolist()).issubset({0, 1}):  # If only 0/1 after rounding
                boolean.append(c)  # Treat as boolean
            else:
                numeric.append(c)  # Otherwise treat as numeric
        elif pd.api.types.is_bool_dtype(s):  # Explicit boolean dtype
            boolean.append(c)
        else:
            categoricals.append(c)  # Catch-all for categorical
    return {"numeric": numeric, "boolean": boolean, "categorical": categoricals}  # Return grouped types


def one_hot_encode_categoricals(df: pd.DataFrame, cat_cols: List[str], min_prevalence: float = 0.01) -> Tuple[pd.DataFrame, Dict]:  # One-hot encode with rare-level bucketing
    if not cat_cols:  # If no categorical columns, return as-is with empty report
        return df.copy(), {"encoded": [], "rare_buckets": {}}
    out = df.copy()  # Work on a copy to avoid mutating input
    report = {"encoded": [], "rare_buckets": {}}  # Track what was encoded and rare categories
    for c in cat_cols:  # Process each categorical feature
        s = out[c].astype(str).str.strip()  # Normalize to trimmed strings
        # prevalence
        counts = s.value_counts(normalize=True)  # Relative frequency of each level
        rare_levels = counts[counts < min_prevalence].index.tolist()  # Levels below threshold are rare
        s2 = s.where(~s.isin(rare_levels), other="Other")  # Replace rare levels with 'Other'
        dummies = pd.get_dummies(s2, prefix=c)  # One-hot encode the normalized series
        out = pd.concat([out.drop(columns=[c]), dummies], axis=1)  # Replace original col with dummies
        report["encoded"].append(c)  # Record encoded column
        report["rare_buckets"][c] = rare_levels  # Record which levels were considered rare
    return out, report  # Return transformed DataFrame and encoding report


def winsorize_numeric(df: pd.DataFrame, numeric_cols: List[str], low_q: float = 0.01, high_q: float = 0.99) -> pd.DataFrame:  # Clip extremes to reduce outlier impact
    out = df.copy()  # Work on a copy
    for c in numeric_cols:  # For each numeric column
        s = pd.to_numeric(out[c], errors="coerce")  # Ensure numeric values
        lo = s.quantile(low_q)  # Lower quantile threshold
        hi = s.quantile(high_q)  # Upper quantile threshold
        out[c] = s.clip(lower=lo, upper=hi)  # Clip values to [lo, hi]
    return out  # Return winsorized DataFrame


def make_class_weights(y: np.ndarray) -> np.ndarray:  # Compute inverse-frequency class weights
    # inverse frequency
    classes, counts = np.unique(y, return_counts=True)  # Get counts per class
    freq = {cls: cnt / len(y) for cls, cnt in zip(classes, counts)}  # Frequency per class
    weights = np.array([1.0 / freq[v] for v in y])  # Assign inverse frequency to each sample
    # normalize to mean 1
    return weights / np.mean(weights)  # Normalize weights to have mean 1


def resample_training(X: np.ndarray, y: np.ndarray, strategy: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Dict[str, str]]:  # Apply selected class imbalance strategy
    info = {"strategy": strategy}  # Report which strategy was applied
    if strategy == "class_weights":  # Use inverse-frequency weighting without changing data
        return X, y, make_class_weights(y), info
    elif strategy == "undersample":  # Randomly drop majority samples to approximate 1:1
        # random undersample majority to ~1:1
        pos_idx = np.where(y == 1)[0]  # Indices of positive class
        neg_idx = np.where(y == 0)[0]  # Indices of negative class
        if len(pos_idx) == 0 or len(neg_idx) == 0:  # If single-class, skip resampling
            return X, y, np.ones_like(y, dtype=float), {"note": "no resampling due to single-class"}
        target = min(len(pos_idx), len(neg_idx))  # Target count for each class
        rng = np.random.default_rng(42)  # Reproducible RNG
        if len(pos_idx) > len(neg_idx):  # If positives are majority
            pos_keep = rng.choice(pos_idx, size=target, replace=False)  # Sample positives to target
            keep = np.concatenate([pos_keep, neg_idx])  # Combine with all negatives
        else:  # If negatives are majority
            neg_keep = rng.choice(neg_idx, size=target, replace=False)  # Sample negatives to target
            keep = np.concatenate([pos_idx, neg_keep])  # Combine with all positives
        return X[keep], y[keep], np.ones(len(keep)), info  # Return resampled data, unit weights
    elif strategy == "oversample":  # Randomly duplicate minority samples to approximate 1:1
        # random oversample minority to ~1:1
        pos_idx = np.where(y == 1)[0]  # Indices of positive class
        neg_idx = np.where(y == 0)[0]  # Indices of negative class
        if len(pos_idx) == 0 or len(neg_idx) == 0:  # If single-class, skip resampling
            return X, y, np.ones_like(y, dtype=float), {"note": "no resampling due to single-class"}
        rng = np.random.default_rng(42)  # Reproducible RNG
        if len(pos_idx) < len(neg_idx):  # If positives are minority
            add = rng.choice(pos_idx, size=(len(neg_idx) - len(pos_idx)), replace=True)  # Sample positives with replacement
            keep = np.concatenate([np.arange(len(y)), add])  # Append duplicates to original indices
        else:  # If negatives are minority
            add = rng.choice(neg_idx, size=(len(pos_idx) - len(neg_idx)), replace=True)  # Sample negatives with replacement
            keep = np.concatenate([np.arange(len(y)), add])  # Append duplicates
        return X[keep], y[keep], np.ones(len(keep)), info  # Return oversampled data, unit weights
    elif strategy == "smote":  # Synthetic minority over-sampling technique
        if not IMB_AVAILABLE:  # If imbalanced-learn is unavailable
            return X, y, np.ones_like(y, dtype=float), {"note": "SMOTE unavailable; skipping"}
        sm = SMOTE(random_state=42)  # SMOTE with fixed seed
        Xr, yr = sm.fit_resample(X, y)  # Generate synthetic samples for minority class
        return Xr, yr, np.ones(len(yr)), info  # Return resampled data, unit weights
    else:  # Unknown strategy; leave data unchanged
        return X, y, np.ones_like(y, dtype=float), {"note": "unknown strategy; using original"}


def platt_scale_fit(probs: np.ndarray, y_true: np.ndarray) -> Tuple[LogisticRegression, float, float]:
    # Fit logistic on probs as a single feature  # Calibrate raw probabilities via logistic regression
    lr = LogisticRegression(solver="lbfgs")  # Use LBFGS solver for stable convergence
    lr.fit(probs.reshape(-1, 1), y_true)  # Train logistic on single-feature input (probs)
    a = lr.coef_[0][0]  # Slope parameter from fitted model
    b = lr.intercept_[0]  # Intercept parameter from fitted model
    return lr, a, b  # Return fitted estimator and parameters


def detect_boolean_columns(X_df: pd.DataFrame) -> List[bool]:  # Identify which columns are binary (0/1)
    flags = []  # Collect boolean flags per column
    for c in X_df.columns:  # Iterate columns
        vals = pd.to_numeric(X_df[c], errors="coerce")  # Convert values to numeric (NaN on failure)
        uniq = np.unique(vals.dropna().values)  # Unique non-NaN values
        flags.append(set(np.round(uniq).tolist()).issubset({0, 1}))  # True if all values are 0/1 after rounding
    return flags  # Return list of boolean indicators


def impute_and_scale_train(X_df: pd.DataFrame, bool_flags: List[bool]) -> Tuple[np.ndarray, Dict]:  # Fit imputation/scaling params and transform training data
    X_vals = X_df.values.astype(float)  # Work with float array for NaN handling and scaling
    medians = []  # Track per-column medians (for numeric)
    modes = []  # Track per-column modes (for boolean)
    for j in range(X_vals.shape[1]):  # Iterate columns
        col = X_vals[:, j]  # Column view
        if bool_flags[j]:  # Boolean column handling
            cnt0 = np.sum(col == 0)  # Count zeros
            cnt1 = np.sum(col == 1)  # Count ones
            mode_val = 1.0 if cnt1 > cnt0 else 0.0  # Mode based on majority
            modes.append(mode_val)  # Store mode
            medians.append(float(np.nanmedian(col)))  # Still store median for completeness
            col[np.isnan(col)] = mode_val  # Impute NaNs with mode for boolean
            X_vals[:, j] = col  # Write back imputed column
        else:  # Numeric column handling
            m = float(np.nanmedian(col))  # Compute median for imputation
            medians.append(m)  # Store median
            modes.append(float("nan"))  # No mode for numeric; store NaN
            col[np.isnan(col)] = m  # Impute NaNs with median
            X_vals[:, j] = col  # Write back
    # standardize numeric only
    mean = X_vals.mean(axis=0)  # Per-column mean
    std = X_vals.std(axis=0) + 1e-8  # Per-column std with epsilon to avoid divide-by-zero
    X_std = X_vals.copy()  # Copy for standardized output
    for j in range(X_vals.shape[1]):  # Iterate columns
        if not bool_flags[j]:  # Standardize only non-boolean columns
            X_std[:, j] = (X_vals[:, j] - mean[j]) / std[j]  # Z-score normalization
    params = {
        "medians": medians,  # Store medians for apply phase
        "modes": modes,  # Store boolean modes for apply phase
        "mean": mean.tolist(),  # Store means for apply phase
        "std": std.tolist(),  # Store stds for apply phase
        "bool_flags": bool_flags,  # Persist boolean column flags
    }
    return X_std, params  # Return standardized data and parameters


def impute_and_scale_apply(X_df: pd.DataFrame, params: Dict) -> np.ndarray:  # Apply stored imputation/scaling params to new data
    X_vals = X_df.values.astype(float)  # Convert to float array
    medians = params["medians"]  # Retrieve stored medians
    modes = params["modes"]  # Retrieve stored modes
    mean = np.array(params["mean"], dtype=float)  # Retrieve means
    std = np.array(params["std"], dtype=float)  # Retrieve stds
    bool_flags = params["bool_flags"]  # Retrieve boolean flags
    for j in range(X_vals.shape[1]):  # Iterate columns
        col = X_vals[:, j]  # Column view
        if bool_flags[j]:  # Boolean column
            mode_val = modes[j]  # Mode for this column
            col[np.isnan(col)] = mode_val  # Impute NaNs with mode
        else:  # Numeric column
            m = medians[j]  # Median for this column
            col[np.isnan(col)] = m  # Impute NaNs with median
        X_vals[:, j] = col  # Write back
    X_std = X_vals.copy()  # Copy for standardized output
    for j in range(X_vals.shape[1]):  # Iterate columns
        if not bool_flags[j]:  # Only standardize non-boolean columns
            X_std[:, j] = (X_vals[:, j] - mean[j]) / std[j]  # Z-score normalization
    return X_std  # Return transformed array


def add_intercept(X: np.ndarray) -> np.ndarray:  # Append a constant 1 column for intercept term
    return np.hstack([X, np.ones((X.shape[0], 1))])  # Concatenate features with a column of ones


def fit_linear_regression(X: np.ndarray, y: np.ndarray, alpha: float = 0.0) -> np.ndarray:  # Closed-form ridge regression
    # ridge: (X^T X + alpha I)^{-1} X^T y
    Xt = X.T  # Transpose X
    A = Xt @ X  # Gram matrix
    if alpha > 0:  # Add L2 regularization if requested
        A = A + alpha * np.eye(A.shape[0])  # Diagonal regularization term
    b = Xt @ y  # X^T y
    w = np.linalg.solve(A, b)  # Solve linear system for weights
    return w  # Return regression weights


def predict_linear(X: np.ndarray, w: np.ndarray) -> np.ndarray:  # Linear regression prediction
    return X @ w  # Matrix-vector multiply to get predictions


def fit_logistic_regression(X: np.ndarray, y: np.ndarray, sample_weights: np.ndarray, lr: float = 0.05, epochs: int = 3000, seed: int = 42) -> np.ndarray:  # Simple weighted gradient descent logistic fit
    rng = np.random.default_rng(seed)  # Reproducible random generator
    w = rng.normal(0, 0.01, size=X.shape[1])  # Initialize weights with small Gaussian noise
    for _ in range(epochs):  # Iterate gradient steps
        z = X @ w  # Linear scores
        p = 1 / (1 + np.exp(-z))  # Sigmoid to probabilities
        grad = (X * sample_weights[:, None]).T @ (p - y) / X.shape[0]  # Weighted gradient
        w -= lr * grad  # Gradient descent update
    return w  # Return learned logistic weights


def predict_logistic_prob(X: np.ndarray, w: np.ndarray) -> np.ndarray:  # Logistic probability prediction
    z = X @ w  # Linear scores
    return 1 / (1 + np.exp(-z))  # Sigmoid to probabilities


def compute_sample_weights(y: np.ndarray) -> np.ndarray:  # Balanced class weights for logistic training
    classes, counts = np.unique(y, return_counts=True)  # Class counts
    total = y.shape[0]  # Total samples
    w_map = {cls: total / (2.0 * cnt) for cls, cnt in zip(classes, counts)}  # Inverse proportional weights
    return np.array([w_map[int(v)] for v in y], dtype=float)  # Map each sample to its class weight


def group_kfold(groups: np.ndarray, n_splits: int = 5, seed: int = 42) -> List[Tuple[np.ndarray, np.ndarray]]:  # Group-aware CV splitter
    uniq = np.array(sorted(set(groups)))  # Unique group IDs
    rng = np.random.default_rng(seed)  # RNG for reproducibility
    rng.shuffle(uniq)  # Shuffle groups
    folds = np.array_split(uniq, n_splits)  # Partition into folds
    splits = []  # Unused, but kept for clarity
    for i in range(n_splits):  # For each fold as validation
        val_groups = set(folds[i].tolist())  # Groups assigned to validation
        train_groups = set(np.concatenate([folds[j] for j in range(n_splits) if j != i]).tolist())  # Remaining groups for train
        yield val_groups, train_groups  # Yield the group sets


def spearman_rho(y_true: np.ndarray, y_pred: np.ndarray) -> float:  # Spearman rank correlation
    # rank via argsort twice
    def rankdata(a: np.ndarray) -> np.ndarray:  # Convert raw values to rank positions
        order = np.argsort(a)  # Sort indices by value
        ranks = np.empty_like(order)  # Allocate ranks array
        ranks[order] = np.arange(1, len(a) + 1)  # Assign ranks (1..N) by sorted order
        return ranks.astype(float)  # Return float ranks
    rt = rankdata(y_true)  # Ranks of true values
    rp = rankdata(y_pred)  # Ranks of predictions
    # Pearson on ranks
    rt = (rt - rt.mean()) / (rt.std() + 1e-8)  # Standardize ranks
    rp = (rp - rp.mean()) / (rp.std() + 1e-8)  # Standardize ranks
    return float(np.clip(np.mean(rt * rp), -1.0, 1.0))  # Correlation bounded to [-1,1]


def pearson_r(y_true: np.ndarray, y_pred: np.ndarray) -> float:  # Pearson correlation coefficient
    yt = (y_true - y_true.mean()) / (y_true.std() + 1e-8)  # Standardize true values
    yp = (y_pred - y_pred.mean()) / (y_pred.std() + 1e-8)  # Standardize predictions
    return float(np.clip(np.mean(yt * yp), -1.0, 1.0))  # Mean product equals correlation; bound to [-1,1]


def pr_curve(y_true: np.ndarray, y_prob: np.ndarray):  # Construct precision-recall curve arrays
    order = np.argsort(-y_prob)  # Sort by descending probability
    y_true_sorted = y_true[order]  # True labels in score order
    y_prob_sorted = y_prob[order]  # Sorted probabilities
    tp = np.cumsum(y_true_sorted == 1)  # True positives cumulative
    fp = np.cumsum(y_true_sorted == 0)  # False positives cumulative
    pos_total = (y_true == 1).sum()  # Total positives
    precision = tp / np.maximum(tp + fp, 1)  # Precision at each threshold
    recall = tp / np.maximum(pos_total, 1)  # Recall at each threshold
    thresholds = y_prob_sorted  # Thresholds corresponding to sorted scores
    precision = np.r_[1.0, precision]  # Prepend perfect precision at start
    recall = np.r_[0.0, recall]  # Prepend zero recall at start
    thresholds = np.r_[thresholds[0], thresholds]  # Align thresholds length
    return precision, recall, thresholds  # Return PR arrays


def average_precision(precision: np.ndarray, recall: np.ndarray) -> float:  # Compute area under PR curve (AP)
    ap = 0.0  # Accumulator
    for i in range(1, len(recall)):  # Trapezoidal integration over recall
        ap += (recall[i] - recall[i - 1]) * precision[i]  # Area of slice
    return float(ap)  # Return AP


def confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:  # Custom confusion matrix
    tn = int(((y_true == 0) & (y_pred == 0)).sum())  # True negatives count
    fp = int(((y_true == 0) & (y_pred == 1)).sum())  # False positives count
    fn = int(((y_true == 1) & (y_pred == 0)).sum())  # False negatives count
    tp = int(((y_true == 1) & (y_pred == 1)).sum())  # True positives count
    return np.array([[tn, fp], [fn, tp]], dtype=int)  # 2x2 matrix


def plot_reliability(y_true: np.ndarray, y_prob: np.ndarray, title: str, out_path: Path):  # Reliability diagram (calibration plot)
    bins = np.linspace(0.0, 1.0, 11)  # 10 bins over [0,1]
    inds = np.digitize(y_prob, bins) - 1  # Bin assignment for each probability
    xs = []  # Average predicted probability per bin
    ys = []  # Observed positive fraction per bin
    for b in range(10):  # For each bin
        mask = inds == b  # Samples in bin
        if mask.sum() == 0:  # Skip empty bins
            continue
        xs.append(y_prob[mask].mean())  # Mean predicted prob in bin
        ys.append((y_true[mask] == 1).mean())  # Fraction of positives in bin
    plt.figure(figsize=(5, 5))  # Create figure
    plt.plot([0, 1], [0, 1], '--', color='gray', label='Perfect calibration')  # Reference line
    plt.scatter(xs, ys, color='blue', label='Observed')  # Observed calibration points
    plt.xlabel('Predicted probability')  # X-axis label
    plt.ylabel('Fraction positive')  # Y-axis label
    plt.title(title)  # Plot title
    plt.legend()  # Legend
    plt.grid(True, alpha=0.3)  # Gridlines
    plt.tight_layout()  # Tight layout
    plt.savefig(out_path)  # Save figure
    plt.close()  # Close figure to free memory


def brier_score(y_true: np.ndarray, y_prob: np.ndarray) -> float:  # Brier score (calibration error)
    return float(np.mean((y_prob - y_true) ** 2))  # Mean squared error of probabilities vs outcomes


def platt_scaling_fit(scores: np.ndarray, y_true: np.ndarray, lr: float = 0.05, epochs: int = 2000) -> Tuple[float, float]:  # Platt scaling parameters via logistic fit
    # Fit logistic on single feature 'scores' with intercept
    X = np.column_stack([scores, np.ones_like(scores)])  # Feature column + intercept
    w = fit_logistic_regression(X, y_true, sample_weights=np.ones_like(y_true, dtype=float), lr=lr, epochs=epochs)  # Fit parameters
    return float(w[0]), float(w[1])  # Return slope (a) and intercept (b)


def platt_scaling_predict(scores: np.ndarray, a: float, b: float) -> np.ndarray:  # Apply Platt scaling to scores
    z = a * scores + b  # Linear transform
    return 1 / (1 + np.exp(-z))  # Sigmoid to calibrated probabilities


def agg_auc_rank(y_true: np.ndarray, y_prob: np.ndarray) -> float:  # Rank-based AUC approximation
    order = np.argsort(y_prob)  # Sort ascending by score
    ranks = np.empty_like(order)  # Allocate ranks
    ranks[order] = np.arange(1, len(y_prob) + 1)  # Assign ranks
    n_pos = int((y_true == 1).sum())  # Number of positives
    n_neg = int((y_true == 0).sum())  # Number of negatives
    if n_pos == 0 or n_neg == 0:  # Degenerate case
        return 0.5  # Neutral AUC
    return float(((ranks[y_true == 1].sum()) - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg + 1e-8))  # Mann-Whitney U normalization


def _conf_counts(y_true: np.ndarray, y_prob: np.ndarray, thr: float) -> Tuple[int, int, int, int]:  # Confusion counts at threshold
    pred = (y_prob >= thr).astype(int)  # Binary predictions
    tn = int(((pred == 0) & (y_true == 0)).sum())  # True negatives
    fp = int(((pred == 1) & (y_true == 0)).sum())  # False positives
    fn = int(((pred == 0) & (y_true == 1)).sum())  # False negatives
    tp = int(((pred == 1) & (y_true == 1)).sum())  # True positives
    return tn, fp, fn, tp  # Return counts


def compute_precision(y_true: np.ndarray, y_prob: np.ndarray, thr: float) -> float:  # Precision at threshold
    tn, fp, fn, tp = _conf_counts(y_true, y_prob, thr)  # Confusion counts
    return float(tp / max(tp + fp, 1))  # TP / (TP + FP), guard against zero denom


def compute_recall(y_true: np.ndarray, y_prob: np.ndarray, thr: float) -> float:  # Recall at threshold
    tn, fp, fn, tp = _conf_counts(y_true, y_prob, thr)  # Confusion counts
    return float(tp / max(tp + fn, 1))  # TP / (TP + FN), guard against zero denom


def compute_f1(y_true: np.ndarray, y_prob: np.ndarray, thr: float) -> float:  # F1 at threshold
    p = compute_precision(y_true, y_prob, thr)  # Precision
    r = compute_recall(y_true, y_prob, thr)  # Recall
    return float((2 * p * r) / max(p + r, 1e-8))  # Harmonic mean; guard against zero denom


def main():  # Orchestrate the end-to-end two-model pipeline
    parser = argparse.ArgumentParser(description="Two-model pipeline: AI Score (regression) + Recruiter Decision (classification)")  # CLI parser
    parser.add_argument("--path", default="c:\\Users\\FerrariKazu\\Documents\\AI Folder\\P3\\AM-DS-01\\models\\pipeline_v3\\normalized_dataset_v3.csv")  # Path to base dataset CSV
    parser.add_argument("--out_dir", default=".")  # Output directory for artifacts
    parser.add_argument("--use_sklearn", action="store_true", help="Attempt scikit-learn models if available")  # Toggle sklearn usage
    parser.add_argument("--labels_path", default=None, help="Optional CSV containing recruiter decisions to merge by key")  # Optional labels CSV
    parser.add_argument("--recruiter_col", default=None, help="Override recruiter decision column name in base CSV")  # Override decision column name
    args = parser.parse_args()  # Parse CLI args

    out_dir = Path(args.out_dir)  # Normalize output dir path
    out_dir.mkdir(parents=True, exist_ok=True)  # Ensure output dir exists
    data_path = Path(args.path)  # Normalize data path
    df = pd.read_csv(data_path)  # Load dataset into DataFrame
    # Targets
    ai_score_col = "AI Score (0-100)"  # Regression target for Model A
    recruiter_col = "Recruiter_Decision"  # Classification target for Model B
    group_col = "Resume_ID"  # Grouping key for CV splits

    # Validate base-required columns
    missing_base = []  # Track missing columns
    if ai_score_col not in df.columns:  # Require AI Score
        missing_base.append(ai_score_col)
    if group_col not in df.columns:  # Require Resume_ID for grouping
        missing_base.append(group_col)
    if missing_base:  # If any missing, raise early
        raise KeyError(f"Missing required columns: {missing_base}")

    # Label discovery in base CSV (case-insensitive, underscore-normalized)
    label_prep_lines = []  # Collect informational lines for label prep report
    detected_col = None  # Placeholder for detected decision column
    if args.recruiter_col and args.recruiter_col in df.columns:  # If override provided and exists
        detected_col = args.recruiter_col  # Use override
        label_prep_lines.append(f"Recruiter label override provided: {detected_col}")  # Log override
    else:
        base_detected = _detect_decision_col(df)  # Attempt auto-detection in base CSV
        if base_detected:
            detected_col = base_detected  # Use detected column
            label_prep_lines.append(f"Detected recruiter decision in base CSV: {base_detected}")  # Log detection

    # If not found in base, try optional labels file
    if not detected_col and args.labels_path:  # Use external labels if needed
        lp = Path(args.labels_path)  # Normalize labels path
        if lp.exists():  # If labels CSV exists
            labels_df = pd.read_csv(lp)  # Load labels
            # Normalize column names
            labels_df.columns = [_normalize_name(c) for c in labels_df.columns]  # Standardize names for detection
            key_col = _detect_key_col(labels_df)  # Detect key column in labels
            dec_col = _detect_decision_col(labels_df)  # Detect decision column in labels
            label_prep_lines.append(f"Labels file loaded: {lp}")  # Log
            label_prep_lines.append(f"Detected key col: {key_col}")  # Log key detection
            label_prep_lines.append(f"Detected decision col: {dec_col}")  # Log decision detection
            if key_col and dec_col:  # If both needed columns found
                labels_df[dec_col] = _map_decision_series(labels_df[dec_col])  # Normalize decision values
                # Prepare keys as strings for safe join
                left_key = df[group_col].astype(str)  # Convert base keys to string
                right_key = labels_df[key_col].astype(str)  # Convert labels keys to string
                merged = df.copy()  # Work on a copy
                merged["__key__"] = left_key.values  # Temp join key in base
                lk = labels_df[[key_col, dec_col]].copy()  # Keep only relevant columns
                lk["__key__"] = right_key.values  # Temp join key in labels
                merged = merged.merge(lk[["__key__", dec_col]], on="__key__", how="left")  # Left join
                merged.drop(columns=["__key__"], inplace=True)  # Drop temp key
                df = merged  # Update base DataFrame
                df[recruiter_col] = df[dec_col]  # Copy decision into canonical column
                matched = int(df[recruiter_col].notna().sum())  # Count matches
                missing = int(df[recruiter_col].isna().sum())  # Count missing
                label_prep_lines.append(f"Labels merge: matched={matched}, missing={missing}")  # Log merge stats
            else:
                label_prep_lines.append("Labels file does not contain detectable key/decision columns.")  # Report detection failure
        else:
            label_prep_lines.append(f"Labels file path not found: {lp}")  # Report missing file

    # If base detection succeeded (and we didn't rely on labels), map and standardize
    if detected_col:  # If we found recruiter decision in base CSV
        mapped = _map_decision_series(df[detected_col])  # Normalize to binary
        df[recruiter_col] = mapped  # Store under canonical column name
        n_pos = int((df[recruiter_col] == 1).sum())  # Positives count
        n_neg = int((df[recruiter_col] == 0).sum())  # Negatives count
        n_nan = int(df[recruiter_col].isna().sum())  # Missing count
        label_prep_lines.append(f"Base label mapping counts: pos={n_pos}, neg={n_neg}, missing={n_nan}")  # Log stats

    # Determine if recruiter label is present
    recruiter_missing = recruiter_col not in df.columns  # Boolean flag
    # If still missing, save labels_missing_report.txt with scanned info
    if recruiter_missing:  # Write diagnostic report if missing
        report_lines = []  # Collect report lines
        report_lines.append("Labels Missing Report")  # Title
        report_lines.append("---------------------")  # Underline
        report_lines.append("Scanned aliases: " + ", ".join(sorted(DECISION_ALIASES)))  # List of checked aliases
        report_lines.append("Columns in base CSV (normalized -> original):")  # Column mapping
        for c in df.columns:  # Map normalized to original names
            report_lines.append(f"- {_normalize_name(c)} -> {c}")
        # Try to show sample values of any columns that look related
        related_cols = [c for c in df.columns if any(a in _normalize_name(c) for a in DECISION_ALIASES)]  # Potentially relevant columns
        if related_cols:
            for c in related_cols:  # Show sample values
                sample_vals = df[c].dropna().astype(str).head(5).tolist()
                report_lines.append(f"Samples for {c}: {sample_vals}")
        (out_dir / "labels_missing_report.txt").write_text("\n".join(report_lines) + "\n", encoding="utf-8")  # Save report
    else:
        # Save label prep report
        (out_dir / "label_prep_report.txt").write_text("\n".join(label_prep_lines) + "\n", encoding="utf-8")  # Save prep details

    # Feature columns
    feature_cols = load_feature_columns(df, Path("columns_clean.json"))  # Select feature columns
    # Infer dtypes on selected features
    type_info = infer_feature_types(df, feature_cols)  # Group into numeric/boolean/categorical
    cat_report = {}  # Placeholder for encoding report
    if type_info["categorical"]:  # If there are non-binary categorical columns
        # One-hot encode with 'Other' bucket for rare levels
        df_encoded, cat_report = one_hot_encode_categoricals(df[feature_cols], type_info["categorical"], min_prevalence=0.01)  # Encode
        # Rebuild feature columns list after encoding
        feature_cols = list(df_encoded.columns)  # Encoded column names
        X_base = df_encoded.copy()  # Base features become the encoded frame
        cats_encoding_path = Path(args.out_dir) / "cats_encoding_report.txt"  # Report path
        cats_encoding_path.write_text(
            "Categorical Encoding Report\n" +  # Title
            "---------------------------\n" +  # Underline
            f"Encoded columns: {type_info['categorical']}\n" +  # List encoded cols
            f"Rare level buckets: {json.dumps(cat_report['rare_buckets'], ensure_ascii=False)}\n",  # Rare levels per column
            encoding="utf-8",
        )
    else:  # No non-binary categoricals present
        X_base = df[feature_cols].copy()  # Use original features as-is
        cats_encoding_path = Path(args.out_dir) / "cats_encoding_report.txt"  # Report path
        cats_encoding_path.write_text(
            "Categorical Encoding Report\n" +  # Title
            "---------------------------\n" +  # Underline
            "No non-binary categorical columns found.\n",  # Message
            encoding="utf-8",
        )

    # Base data
    groups = df[group_col].values  # Group identifiers for CV splitting
    # Optional winsorization comparison will use X_base_wins if it improves Model B
    X_base_wins = winsorize_numeric(X_base, [c for c in feature_cols if c in type_info["numeric"]])  # Clip numeric extremes

    # MODEL A: 5-fold Group CV for AI Score
    bool_flags = detect_boolean_columns(X_base)  # Identify binary columns
    X_std_full, preproc_params = impute_and_scale_train(X_base, bool_flags)  # Standardize and store params
    # add intercept
    XA_full = add_intercept(X_std_full)  # Add intercept column
    yA = pd.to_numeric(df[ai_score_col], errors="coerce").fillna(0).values.astype(float)  # Target vector

    # Folds
    fold_splits = list(group_kfold(groups, n_splits=5, seed=42))  # Group-aware CV folds
    oof_pred = np.zeros_like(yA)  # Out-of-fold predictions placeholder
    cv_metrics = []  # Per-fold metrics
    scaling_audit = {"per_fold": []}  # Track mean/std per fold for audit
    for fold_idx, (val_groups, train_groups) in enumerate(fold_splits):  # Iterate folds
        is_val = df[group_col].isin(val_groups).values  # Validation mask
        is_train = df[group_col].isin(train_groups).values  # Training mask
        X_tr = X_std_full[is_train]  # Train features
        y_tr = yA[is_train]  # Train target
        X_va = X_std_full[is_val]  # Validation features
        y_va = yA[is_val]  # Validation target
        # Fit ridge with mild regularization for stability
        w = fit_linear_regression(add_intercept(X_tr), y_tr, alpha=1.0)  # Train linear ridge
        pred_va = predict_linear(add_intercept(X_va), w)  # Predict validation
        pred_va = np.clip(pred_va, 0.0, 100.0)  # Clip to valid score range
        oof_pred[is_val] = pred_va  # Store OOF predictions
        mae = float(np.mean(np.abs(pred_va - y_va)))  # Mean absolute error
        rmse = float(np.sqrt(np.mean((pred_va - y_va) ** 2)))  # Root mean squared error
        # R2 manually
        ss_res = float(np.sum((y_va - pred_va) ** 2))  # Residual sum of squares
        ss_tot = float(np.sum((y_va - y_va.mean()) ** 2)) + 1e-8  # Total sum of squares
        r2 = 1.0 - ss_res / ss_tot  # R^2
        pr = pearson_r(y_va, pred_va)  # Pearson correlation
        sr = spearman_rho(y_va, pred_va)  # Spearman correlation
        cv_metrics.append({"fold": fold_idx + 1, "mae": mae, "rmse": rmse, "r2": r2, "pearson_r": pr, "spearman_rho": sr})  # Record metrics
        # Numeric scaling audit: train mean≈0, std≈1 for non-boolean
        non_bool_idx = [i for i, b in enumerate(bool_flags) if not b]  # Indices for numeric features
        train_means = np.mean(X_tr[:, non_bool_idx], axis=0).tolist()  # Train means
        train_stds = np.std(X_tr[:, non_bool_idx], axis=0).tolist()  # Train stds
        val_means = np.mean(X_va[:, non_bool_idx], axis=0).tolist()  # Validation means
        val_stds = np.std(X_va[:, non_bool_idx], axis=0).tolist()  # Validation stds
        scaling_audit["per_fold"].append({  # Append audit info for fold
            "fold": fold_idx + 1,
            "train_means": train_means,
            "train_stds": train_stds,
            "val_means": val_means,
            "val_stds": val_stds,
        })

    # Save OOF and CV metrics
    oof_path = out_dir / "ai_score_oof.csv"  # Path for OOF predictions CSV
    pd.DataFrame({  # Construct OOF DataFrame
        "Resume_ID": df[group_col],  # Group key
        "index": np.arange(len(df)),  # Row index
        "y_true": yA,  # True AI score
        "y_pred_oof": oof_pred,  # OOF predicted score
    }).to_csv(oof_path, index=False)  # Write CSV

    # Aggregate metrics
    def agg(lst, key):  # Helper to compute mean/std aggregates
        vals = [d[key] for d in lst]  # Extract values
        return {"mean": float(np.mean(vals)), "std": float(np.std(vals, ddof=1))}  # Mean and sample std
    cv_summary = {  # Bundle per-fold and summary metrics
        "per_fold": cv_metrics,
        "summary": {
            "mae": agg(cv_metrics, "mae"),
            "rmse": agg(cv_metrics, "rmse"),
            "r2": agg(cv_metrics, "r2"),
            "pearson_r": agg(cv_metrics, "pearson_r"),
            "spearman_rho": agg(cv_metrics, "spearman_rho"),
        },
    }
    (out_dir / "ai_score_cv_metrics.json").write_text(json.dumps(cv_summary, indent=2), encoding="utf-8")  # Save CV metrics
    # Save numeric scaling audit
    (out_dir / "numeric_scaling_report.json").write_text(json.dumps(scaling_audit, indent=2), encoding="utf-8")  # Save scaling audit

    # Fit final Model A on full data
    wA = fit_linear_regression(XA_full, yA, alpha=1.0)  # Train ridge on full data
    with open(out_dir / "ai_score_model.pkl", "wb"):  # Open model artifact path
        pickle.dump({"type": "linear_ridge_numpy", "weights": wA.tolist(), "preproc": preproc_params, "feature_columns": feature_cols}, open(out_dir / "ai_score_model.pkl", "wb"))  # Save model bundle

    # Plots for Model A (OOF)
    plt.figure(figsize=(6, 5))  # Create scatter plot figure
    plt.scatter(yA, oof_pred, s=10, alpha=0.6)  # Scatter: true vs OOF pred
    plt.xlabel("True AI Score")  # X-label
    plt.ylabel("OOF Predicted AI Score")  # Y-label
    plt.title("Model A: True vs OOF Predicted")  # Title
    plt.grid(True, alpha=0.3)  # Gridlines
    plt.tight_layout()  # Optimize layout
    plt.savefig(out_dir / "y_true_vs_pred_scatter.png")  # Save plot
    plt.close()  # Close figure

    plt.figure(figsize=(6, 5))  # Create histogram figure
    errors = oof_pred - yA  # Compute OOF errors
    plt.hist(errors, bins=30, color="steelblue", alpha=0.8)  # Plot histogram
    plt.xlabel("Prediction Error")  # X-label
    plt.ylabel("Count")  # Y-label
    plt.title("Model A: OOF Error Histogram")  # Title
    plt.grid(True, alpha=0.3)  # Gridlines
    plt.tight_layout()  # Optimize layout
    plt.savefig(out_dir / "error_hist.png")  # Save plot
    plt.close()  # Close figure

    # MODEL B: Recruiter Decision classification with 5-fold Group CV (skip if missing)
    if not recruiter_missing:  # Proceed only if recruiter labels are available
        yB = pd.to_numeric(df[recruiter_col], errors="coerce").fillna(0).astype(int).values  # Binary target vector
        # Prepare base features for B: same preprocessing, then append ai_score_oof (scaled like numeric)
        Xb_train_std = X_std_full.copy()  # Start from standardized base features
        # standardize oof to comparable scale
        oof_mean = oof_pred.mean()  # Mean of OOF scores
        oof_std = oof_pred.std() + 1e-8  # Std of OOF scores
        oof_std_feat = (oof_pred - oof_mean) / oof_std  # Standardized OOF feature
        Xb_with_oof = np.column_stack([Xb_train_std, oof_std_feat])  # Append OOF feature
        feat_cols_b = feature_cols  # Feature names for Model B
        # add intercept
        Xb_with_oof_i = add_intercept(Xb_with_oof)  # Add intercept

        # CV for Model B
        recruiter_cv = []  # Per-fold metrics for Model B
        brier_before = []  # Calibration error before Platt scaling
        brier_after = []  # Calibration error after Platt scaling
        for fold_idx, (val_groups, train_groups) in enumerate(fold_splits):  # Iterate folds
            is_val = df[group_col].isin(val_groups).values  # Validation mask
            is_train = df[group_col].isin(train_groups).values  # Training mask
            X_tr = Xb_with_oof_i[is_train]  # Train features
            y_tr = yB[is_train]  # Train labels
            X_va = Xb_with_oof_i[is_val]  # Validation features
            y_va = yB[is_val]  # Validation labels
            sw_tr = compute_sample_weights(y_tr)  # Balanced weights
            wB = fit_logistic_regression(X_tr, y_tr, sw_tr, lr=0.05, epochs=3000, seed=42)  # Train logistic
            prob_va = predict_logistic_prob(X_va, wB)  # Predict probabilities
            # metrics
            prec, rec, thr = pr_curve(y_va, prob_va)  # PR arrays
            pr_auc = average_precision(prec, rec)  # PR AUC (AP)
            # ROC AUC via Mann-Whitney
            order = np.argsort(prob_va)  # Sort ascending
            ranks = np.empty_like(order)  # Allocate ranks
            ranks[order] = np.arange(1, len(prob_va) + 1)  # Assign ranks
            n_pos = int((y_va == 1).sum())  # Positives count
            n_neg = int((y_va == 0).sum())  # Negatives count
            auc = float(((ranks[y_va == 1].sum()) - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg + 1e-8))  # AUC via U statistic
            # thresholds
            ths = np.linspace(0.01, 0.99, 99)  # Candidate thresholds
            best_f1 = -1.0  # Best F1 tracker
            best_th = 0.5  # Default threshold
            best_cm = None  # Best confusion matrix holder
            for t in ths:  # Scan thresholds
                pred = (prob_va >= t).astype(int)  # Binary predictions
                cm = confusion_matrix(y_va, pred)  # Confusion matrix
                tn, fp, fn, tp = cm[0,0], cm[0,1], cm[1,0], cm[1,1]  # Counts
                p = tp / max(tp + fp, 1)  # Precision
                r = tp / max(tp + fn, 1)  # Recall
                f1 = (2 * p * r) / max(p + r, 1e-8)  # F1
                if f1 > best_f1:  # Update best if improved
                    best_f1, best_th, best_cm = f1, t, cm
            # cost-optimal thresholds  # Placeholder for cost analysis to pick operational threshold
            def cost_opt(cost_fn: float, cost_fp: float):  # Minimize linear cost of FN/FP at threshold
                best_c = 1e18  # Initialize best cost
                best_t = 0.5  # Initialize best threshold
                for t in ths:  # Iterate candidate thresholds
                    pred = (prob_va >= t).astype(int)  # Binary predictions at t
                    cm = confusion_matrix(y_va, pred)  # Confusion matrix
                    tn, fp, fn, tp = cm[0,0], cm[0,1], cm[1,0], cm[1,1]  # Counts
                    c = cost_fn * fn + cost_fp * fp  # Linear cost: FN weighted + FP weighted
                    if c < best_c:  # If lower cost found
                        best_c, best_t = c, t  # Update
                return best_t  # Return threshold minimizing cost
            th_1_1 = cost_opt(1.0, 1.0)  # Equal cost FN vs FP
            th_3_1 = cost_opt(3.0, 1.0)  # FN=3x FP
            th_5_1 = cost_opt(5.0, 1.0)  # FN=5x FP
            # calibration (Platt)
            a, b = platt_scaling_fit(prob_va, y_va)  # Fit Platt scaling params on val fold
            prob_cal = platt_scaling_predict(prob_va, a, b)  # Apply calibration to val probs
            brier_b = brier_score(y_va, prob_va)  # Uncalibrated Brier score
            brier_a = brier_score(y_va, prob_cal)  # Calibrated Brier score
            brier_before.append(brier_b)  # Track before calibration
            brier_after.append(brier_a)  # Track after calibration
            # reliability plot per fold
            plot_reliability(y_va, prob_va, f"Fold {fold_idx+1} before calibration", out_dir / f"reliability_plot_fold{fold_idx+1}_before.png")  # Save pre-cal plot
            plot_reliability(y_va, prob_cal, f"Fold {fold_idx+1} after calibration", out_dir / f"reliability_plot_fold{fold_idx+1}_after.png")  # Save post-cal plot
            # record
            tn, fp, fn, tp = best_cm[0,0], best_cm[0,1], best_cm[1,0], best_cm[1,1]  # Best confusion matrix counts
            p = tp / max(tp + fp, 1)  # Precision at best threshold
            r = tp / max(tp + fn, 1)  # Recall at best threshold
            recruiter_cv.append({  # Append fold summary
                "fold": fold_idx + 1,
                "roc_auc": auc,
                "pr_auc": pr_auc,
                "f1": best_f1,
                "precision": p,
                "recall": r,
                "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
                "best_threshold": best_th,
                "cost_thresholds": {"1:1": th_1_1, "3:1": th_3_1, "5:1": th_5_1},
                "brier_before": brier_b,
                "brier_after": brier_a,
            })

        cv_b_summary = {  # Summarize Model B CV metrics
            "per_fold": recruiter_cv,
            "summary": {
                "roc_auc": agg(recruiter_cv, "roc_auc"),  # Mean/std ROC AUC
                "pr_auc": agg(recruiter_cv, "pr_auc"),  # Mean/std PR AUC
                "f1": agg(recruiter_cv, "f1"),  # Mean/std F1
                "precision": agg(recruiter_cv, "precision"),  # Mean/std precision
                "recall": agg(recruiter_cv, "recall"),  # Mean/std recall
                "brier_before": {"mean": float(np.mean(brier_before)), "std": float(np.std(brier_before, ddof=1))},  # Brier pre-cal
                "brier_after": {"mean": float(np.mean(brier_after)), "std": float(np.std(brier_after, ddof=1))},  # Brier post-cal
            }
        }
        (out_dir / "recruiter_cv_metrics.json").write_text(json.dumps(cv_b_summary, indent=2), encoding="utf-8")  # Save CV metrics JSON

        # Imbalance benchmarking (strategies a-d) with optional winsorization
        # Prepare winsorized standardized features for Model B
        bool_flags_w_b = detect_boolean_columns(X_base_wins)  # Detect booleans in winsorized frame
        X_std_wins_b, _pre_wins = impute_and_scale_train(X_base_wins, bool_flags_w_b)  # Standardize winsorized
        oof_mean_b = oof_pred.mean(); oof_std_b = oof_pred.std() + 1e-8  # Stats for OOF normalization
        oof_std_feat_b = (oof_pred - oof_mean_b) / oof_std_b  # Standardized OOF feature
        Xb_base_i = add_intercept(np.column_stack([X_std_full, oof_std_feat_b]))  # Base features + OOF + intercept
        Xb_wins_i = add_intercept(np.column_stack([X_std_wins_b, oof_std_feat_b]))  # Winsorized features + OOF + intercept

        def cv_eval_matrix(Xmat: np.ndarray) -> Tuple[float, float]:  # Evaluate PR AUC and Brier across CV using sklearn baseline
            pr_aucs, briers = [], []  # Per-fold metrics
            for val_groups, train_groups in fold_splits:  # Iterate folds
                is_val = df[group_col].isin(val_groups).values  # Validation mask
                is_train = df[group_col].isin(train_groups).values  # Training mask
                X_tr, y_tr = Xmat[is_train], yB[is_train]  # Train split
                X_va, y_va = Xmat[is_val], yB[is_val]  # Validation split
                Xr, yr, sw, _ = resample_training(X_tr, y_tr, "class_weights")  # Balanced class weights
                clf = LogisticRegression(max_iter=1000, fit_intercept=False)  # Logistic baseline
                clf.fit(Xr, yr, sample_weight=sw)  # Fit
                prob_va = clf.predict_proba(X_va)[:, 1]  # Validation probs
                pr_aucs.append(average_precision_score(y_va, prob_va))  # PR AUC
                briers.append(brier_score_loss(y_va, prob_va))  # Brier
            return float(np.mean(pr_aucs)), float(np.mean(briers))  # Mean metrics

        pr_base, br_base = cv_eval_matrix(Xb_base_i)  # CV metrics for base
        pr_wins, br_wins = cv_eval_matrix(Xb_wins_i)  # CV metrics for winsorized
        use_wins = (pr_wins > pr_base + 1e-9) or (br_wins < br_base - 1e-9)  # Decide based on improvement
        (out_dir / "winsorization_compare.txt").write_text(  # Save comparison
            f"PR AUC base={pr_base:.4f}, wins={pr_wins:.4f}\n"+
            f"Brier base={br_base:.4f}, wins={br_wins:.4f}\n"+
            f"Decision: {'Use winsorized numeric' if use_wins else 'Keep base numeric'}\n",
            encoding="utf-8",
        )
        Xb_bench = Xb_wins_i if use_wins else Xb_base_i  # Choose matrix for benchmarking

        strategies = ["class_weights", "undersample", "oversample"] + (["smote"] if IMB_AVAILABLE else [])  # Candidate imbalance strategies
        bench_report = {"per_strategy": {}, "summary": {}}  # Aggregate report
        pr_overlay = {}  # PR curve overlay data
        calib_overlay = {}  # Reliability overlay data
        for strat in strategies:  # Iterate strategies
            per_fold = []  # Per-fold metrics list
            all_prob = []  # Collect probs for overlay
            all_true = []  # Collect labels for overlay
            for val_groups, train_groups in fold_splits:  # Iterate CV folds
                is_val = df[group_col].isin(val_groups).values  # Validation mask
                is_train = df[group_col].isin(train_groups).values  # Training mask
                X_tr, y_tr = Xb_bench[is_train], yB[is_train]  # Train data
                X_va, y_va = Xb_bench[is_val], yB[is_val]  # Validation data
                Xr, yr, sw, _ = resample_training(X_tr, y_tr, strat)  # Resample per strategy
                clf = LogisticRegression(max_iter=1000, fit_intercept=False)  # Logistic classifier
                clf.fit(Xr, yr, sample_weight=sw)  # Fit with sample weights
                prob_va = clf.predict_proba(X_va)[:, 1]  # Validation probs
                # Platt scaling on training probs
                prob_tr = clf.predict_proba(X_tr)[:, 1]  # Training probs
                cal_lr, a, b = platt_scale_fit(prob_tr, y_tr)  # Fit calibration
                prob_va_cal = cal_lr.predict_proba(prob_va.reshape(-1, 1))[:, 1]  # Apply to val probs
                per_fold.append({  # Store fold metrics
                    "pr_auc": float(average_precision_score(y_va, prob_va)),
                    "roc_auc": float(roc_auc_score(y_va, prob_va)),
                    "f1": float(f1_score(y_va, (prob_va >= 0.5).astype(int))),
                    "precision": float(precision_score(y_va, (prob_va >= 0.5).astype(int), zero_division=0)),
                    "recall": float(recall_score(y_va, (prob_va >= 0.5).astype(int))),
                    "brier_before": float(brier_score_loss(y_va, prob_va)),
                    "brier_after": float(brier_score_loss(y_va, prob_va_cal)),
                    "calib_slope": float(a),
                    "calib_intercept": float(b),
                })
                all_prob.append(prob_va)  # Collect for overlay
                all_true.append(y_va)  # Collect labels
            pr_mean = float(np.mean([d["pr_auc"] for d in per_fold]))  # Mean PR AUC
            br_mean = float(np.mean([d["brier_before"] for d in per_fold]))  # Mean Brier
            bench_report["per_strategy"][strat] = {"folds": per_fold, "mean_pr_auc": pr_mean, "mean_brier": br_mean}  # Store
            probs_concat = np.concatenate(all_prob); true_concat = np.concatenate(all_true)  # Concatenate folds
            pr_p, pr_r, _ = precision_recall_curve(true_concat, probs_concat)  # Overlay PR curve
            pr_overlay[strat] = {"precision": pr_p.tolist(), "recall": pr_r.tolist()}  # Store overlay data
            bins = np.linspace(0, 1, 11)  # 10 bins for reliability
            inds = np.digitize(probs_concat, bins) - 1  # Bin indices
            frac_pos = [float(np.mean(true_concat[inds == i])) if np.any(inds == i) else None for i in range(len(bins))]  # Fraction positives
            calib_overlay[strat] = {"bins": bins.tolist(), "fraction_positives": frac_pos}  # Store reliability overlay

        base_auc = bench_report["per_strategy"]["class_weights"]["mean_pr_auc"]  # Baseline AUC
        base_br = bench_report["per_strategy"]["class_weights"]["mean_brier"]  # Baseline Brier
        best_strat = "class_weights"; best_auc = base_auc; best_br = base_br  # Initialize best
        for strat in strategies:  # Compare strategies
            auc = bench_report["per_strategy"][strat]["mean_pr_auc"]  # Strategy AUC
            br = bench_report["per_strategy"][strat]["mean_brier"]  # Strategy Brier
            if auc > best_auc + 1e-12 or (abs(auc - best_auc) < 1e-12 and br < best_br):  # Better by AUC or tie-breaker by Brier
                best_strat, best_auc, best_br = strat, auc, br  # Update best
        if (best_auc - base_auc) < 0.01:  # Require meaningful improvement
            best_strat = "class_weights"  # Default to simplicity
        bench_report["summary"] = {"best_strategy": best_strat, "baseline_auc": base_auc, "best_auc": best_auc, "baseline_brier": base_br, "best_brier": best_br, "winsorization_used": bool(use_wins)}  # Summary
        (out_dir / "imbalance_benchmark_report.json").write_text(json.dumps(bench_report, indent=2), encoding="utf-8")  # Save report

        # Overlay plots (CV)
        try:
            plt.figure(figsize=(6,5))  # PR overlay
            for strat in strategies:  # Plot each strategy's PR curve
                d = pr_overlay[strat]
                plt.plot(d["recall"], d["precision"], label=strat)
            plt.xlabel("Recall"); plt.ylabel("Precision"); plt.title("PR overlay (CV)"); plt.legend(); plt.tight_layout()  # Labels and layout
            plt.savefig(out_dir / "pr_curve_recruiter_benchmark.png", dpi=160); plt.close()  # Save PR overlay
            plt.figure(figsize=(6,5))  # Reliability overlay
            for strat in strategies:  # Plot reliability per strategy
                d = calib_overlay[strat]
                ys = [y if y is not None else np.nan for y in d["fraction_positives"]]
                plt.plot(d["bins"], ys, marker="o", label=strat)
            plt.plot([0,1],[0,1],"--",color="gray",label="perfect")  # Perfect calibration line
            plt.xlabel("Pred prob bin"); plt.ylabel("Frac positives"); plt.title("Reliability overlay (CV)"); plt.legend(); plt.tight_layout()  # Labels and layout
            plt.savefig(out_dir / "reliability_plots_benchmark.png", dpi=160); plt.close()  # Save reliability overlay
        except Exception:
            pass  # Ignore plotting errors in headless environments

        # Step 3/4 audit summary
        (out_dir / "step3_4_audit.txt").write_text(  # Save decisions audit
            "Audit summary and decisions\n"+
            "---------------------------\n"+
            f"Numeric features: {len(type_info['numeric'])}\n"+
            f"Boolean/binary features: {len(type_info['boolean'])}\n"+
            (f"Categorical encoded: {type_info['categorical']}\n" if type_info['categorical'] else "No non-binary categorical columns found.\n")+
            f"Winsorization: {'used' if use_wins else 'not used'}\n"+
            f"Imbalance best strategy (CV): {best_strat}\n",
            encoding="utf-8",
        )

    # HOLDOUT 80/20 group-aware
    uniq_groups = np.array(sorted(set(groups)))  # Unique group IDs
    rng = np.random.default_rng(42)  # Random generator
    rng.shuffle(uniq_groups)  # Shuffle groups for split
    n_test = int(len(uniq_groups) * 0.2)  # 20% for holdout
    val_groups = set(uniq_groups[:n_test].tolist())  # Validation group set
    train_groups = set(uniq_groups[n_test:].tolist())  # Training group set
    is_val = df[group_col].isin(val_groups).values  # Validation mask
    is_train = df[group_col].isin(train_groups).values  # Training mask
    # Fit A on train and predict on val
    X_trA = X_std_full[is_train]  # Train features for A
    y_trA = yA[is_train]  # Train target for A
    wA_hold = fit_linear_regression(add_intercept(X_trA), y_trA, alpha=1.0)  # Fit A on train
    X_vaA = X_std_full[is_val]  # Validation features for A
    ai_pred_val = predict_linear(add_intercept(X_vaA), wA_hold)  # Predict holdout A
    ai_pred_val = np.clip(ai_pred_val, 0.0, 100.0)  # Clip to valid range
    # Prepare B features for holdout
    # For train, we use in-sample predictions from A fitted on train
    ai_pred_train = predict_linear(add_intercept(X_trA), wA_hold)  # In-sample A predictions
    ai_pred_train = np.clip(ai_pred_train, 0.0, 100.0)  # Clip
    # Prepare B holdout data only if recruiter target exists
    if not recruiter_missing:
        # standardize these two sets using train stats
        m_ai = ai_pred_train.mean()  # Mean of A preds (train)
        s_ai = ai_pred_train.std() + 1e-8  # Std of A preds (train)
        ai_tr_feat = (ai_pred_train - m_ai) / s_ai  # Standardized train A feature
        ai_va_feat = (ai_pred_val - m_ai) / s_ai  # Standardized val A feature
        X_trB = add_intercept(np.column_stack([X_std_full[is_train], ai_tr_feat]))  # B train features with A feature
        X_vaB = add_intercept(np.column_stack([X_std_full[is_val], ai_va_feat]))  # B val features with A feature
        yB = pd.to_numeric(df[recruiter_col], errors="coerce").fillna(0).astype(int).values  # Binary labels
        y_trB = yB[is_train]  # Train labels
        y_vaB = yB[is_val]  # Val labels
    # Train B (skip if recruiter missing)
    if not recruiter_missing:
        wB_hold = fit_logistic_regression(X_trB, y_trB, compute_sample_weights(y_trB), lr=0.05, epochs=3000, seed=42)  # Fit B on train
        prob_vaB = predict_logistic_prob(X_vaB, wB_hold)  # Predict holdout probabilities
    # Metrics
    if not recruiter_missing:
        prec, rec, thr = pr_curve(y_vaB, prob_vaB)  # PR curve arrays
        pr_auc_hold = average_precision(prec, rec)  # PR AUC
    # ROC AUC via ranks
    if not recruiter_missing:
        order = np.argsort(prob_vaB)  # Ascending order of probs
        ranks = np.empty_like(order)  # Allocate ranks
        ranks[order] = np.arange(1, len(prob_vaB) + 1)  # Assign ranks
        n_pos = int((y_vaB == 1).sum())  # Positive count
        n_neg = int((y_vaB == 0).sum())  # Negative count
        auc_hold = float(((ranks[y_vaB == 1].sum()) - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg + 1e-8))  # Mann-Whitney AUC
    ths = np.linspace(0.01, 0.99, 99)  # Candidate thresholds
    best_f1 = -1.0  # Initialize best F1
    best_th = 0.5  # Initialize best threshold
    best_cm = None  # Initialize best confusion matrix
    if not recruiter_missing:
        for t in ths:  # Scan thresholds
            pred = (prob_vaB >= t).astype(int)  # Binary predictions
            cm = confusion_matrix(y_vaB, pred)  # Confusion matrix
            tn, fp, fn, tp = cm[0,0], cm[0,1], cm[1,0], cm[1,1]  # Counts
            p = tp / max(tp + fp, 1)  # Precision
            r = tp / max(tp + fn, 1)  # Recall
            f1 = (2 * p * r) / max(p + r, 1e-8)  # F1 score
            if f1 > best_f1:  # Update best
                best_f1, best_th, best_cm = f1, t, cm
    # cost thresholds
    def cost_opt_hold(cost_fn: float, cost_fp: float):  # Cost-optimal threshold on holdout
        best_c = 1e18  # Initialize best cost
        best_t = 0.5  # Initialize best threshold
        for t in ths:  # Iterate thresholds
            pred = (prob_vaB >= t).astype(int)  # Predictions
            cm = confusion_matrix(y_vaB, pred)  # Confusion matrix
            tn, fp, fn, tp = cm[0,0], cm[0,1], cm[1,0], cm[1,1]  # Counts
            c = cost_fn * fn + cost_fp * fp  # Linear cost of errors
            if c < best_c:  # Better cost
                best_c, best_t = c, t  # Update best
        return best_t  # Return best threshold
    if not recruiter_missing:
        th_1_1_h = cost_opt_hold(1.0, 1.0)  # Equal cost
        th_3_1_h = cost_opt_hold(3.0, 1.0)  # FN heavier
        th_5_1_h = cost_opt_hold(5.0, 1.0)  # FN much heavier

    # Save holdout plots
    if not recruiter_missing:
        plt.figure(figsize=(6,5))  # Holdout PR curve
        plt.plot(rec, prec, label="PR")  # Plot PR
        plt.scatter([], [])  # No-op for consistent legend spacing
        plt.xlabel("Recall")
        plt.ylabel("Precision")
        plt.title("Holdout PR curve")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(out_dir / "pr_curve_recruiter.png")  # Save PR curve
        plt.close()
        cm = best_cm  # Best confusion matrix at F1 threshold
        plt.figure(figsize=(4,4))  # Confusion matrix plot
        plt.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)  # Heatmap
        plt.title("Holdout Confusion Matrix")
        plt.colorbar()
        tick_marks = np.arange(2)
        plt.xticks(tick_marks, ["Reject (0)", "Advance (1)"])  # X ticks
        plt.yticks(tick_marks, ["Reject (0)", "Advance (1)"])  # Y ticks
        thresh = cm.max() / 2.0  # Threshold for text color
        for i in range(cm.shape[0]):  # Iterate cells
            for j in range(cm.shape[1]):
                plt.text(j, i, format(int(cm[i, j])), horizontalalignment="center", color="white" if cm[i, j] > thresh else "black")  # Annotate
        plt.tight_layout()
        plt.savefig(out_dir / "confusion_matrix_recruiter.png")  # Save CM plot
        plt.close()
        # Reliability plot on holdout probabilities
        plot_reliability(y_vaB, prob_vaB, "Holdout Reliability (uncalibrated)", out_dir / "reliability_plot_recruiter.png")  # Save reliability

    # Threshold report
    if not recruiter_missing:
        thresh_report = []  # Build threshold report lines
        thresh_report.append("Threshold Report")  # Title
        thresh_report.append("-----------------")  # Underline
        thresh_report.append(f"Max-F1 threshold: {best_th:.2f}")  # F1-optimal threshold
        thresh_report.append(f"Cost-optimal thresholds (FN:FP): 1:1={th_1_1_h:.2f}, 3:1={th_3_1_h:.2f}, 5:1={th_5_1_h:.2f}")  # Cost thresholds
        (out_dir / "threshold_report.txt").write_text("\n".join(thresh_report) + "\n", encoding="utf-8")  # Save report

    # Holdout evaluation with chosen imbalance strategy (and winsorization decision) and save best model
    if not recruiter_missing:  # Finalize best strategy on holdout
        # Use winsorization decision from benchmarking
        try:
            wins_used = json.loads((out_dir / "imbalance_benchmark_report.json").read_text(encoding="utf-8"))["summary"]["winsorization_used"]  # Read flag
            best_strategy = json.loads((out_dir / "imbalance_benchmark_report.json").read_text(encoding="utf-8"))["summary"]["best_strategy"]  # Read strategy
        except Exception:
            wins_used = False  # Default to no winsorization
            best_strategy = "class_weights"  # Default strategy
        # Prepare feature matrices for holdout train/val
        if wins_used:  # Use winsorized standardized features
            bool_flags_w_b = detect_boolean_columns(X_base_wins)  # Detect booleans
            X_std_wins_b, _ = impute_and_scale_train(X_base_wins, bool_flags_w_b)  # Standardize winsorized
            X_trB_bench = X_std_wins_b[is_train]  # Train features
            X_vaB_bench = X_std_wins_b[is_val]  # Val features
        else:
            X_trB_bench = X_std_full[is_train]  # Train features (base)
            X_vaB_bench = X_std_full[is_val]  # Val features (base)
        # Append AI score features standardized with train stats
        m_ai = ai_pred_train.mean(); s_ai = ai_pred_train.std() + 1e-8  # Train stats
        ai_tr_feat = (ai_pred_train - m_ai) / s_ai  # Standardized train A feature
        ai_va_feat = (ai_pred_val - m_ai) / s_ai  # Standardized val A feature
        X_tr_best = add_intercept(np.column_stack([X_trB_bench, ai_tr_feat]))  # Build B train matrix
        X_va_best = add_intercept(np.column_stack([X_vaB_bench, ai_va_feat]))  # Build B val matrix
        # Train with selected strategy
        Xr, yr, sw, _ = resample_training(X_tr_best, y_trB, best_strategy)  # Resample per chosen strategy
        w_best = fit_logistic_regression(Xr, yr, sw, lr=0.05, epochs=3000, seed=42)  # Fit logistic
        prob_va_best = predict_logistic_prob(X_va_best, w_best)  # Predict holdout probs
        # Threshold sweep overwrite
        thresholds = np.linspace(0, 1, 101)  # Dense threshold grid
        thr_report = []  # Collect metrics per threshold
        for t in thresholds:  # Sweep thresholds
            pred_t = (prob_va_best >= t).astype(int)  # Predictions at t
            f1 = f1_score(y_vaB, pred_t)  # F1
            prec = precision_score(y_vaB, pred_t, zero_division=0)  # Precision
            rec = recall_score(y_vaB, pred_t)  # Recall
            thr_report.append({"threshold": float(t), "f1": float(f1), "precision": float(prec), "recall": float(rec)})  # Append
        (out_dir / "threshold_report.txt").write_text(  # Write sweep report
            "Threshold sweep (holdout, best strategy)\n" + json.dumps(thr_report, indent=2), encoding="utf-8"
        )
        # Save best model
        with open(out_dir / "recruiter_model_best.pkl", "wb") as fh:  # Best model artifact
            pickle.dump({"type": "logistic_numpy", "weights": w_best.tolist(), "winsorization_used": bool(wins_used), "best_strategy": best_strategy}, fh)  # Serialize bundle
        # Update pipeline_config.json
        try:
            pipeline_cfg = json.loads((out_dir / "pipeline_config.json").read_text(encoding="utf-8"))  # Read existing config
        except Exception:
            pipeline_cfg = {}  # Initialize empty config
        pipeline_cfg["model_b_best_strategy"] = best_strategy  # Set best strategy
        pipeline_cfg["winsorization_used"] = bool(wins_used)  # Set winsorization flag
        (out_dir / "pipeline_config.json").write_text(json.dumps(pipeline_cfg, indent=2), encoding="utf-8")  # Save config
        # Coefficients snapshot
        try:
            coefs = w_best.tolist()  # Coefficients list
            (out_dir / "coefficients_recruiter.csv").write_text(  # Quick CSV with positional features
                "feature,coef\n" + "\n".join([f"f{i},{coefs[i]}" for i in range(len(coefs))]),
                encoding="utf-8",
            )
        except Exception:
            pass  # Ignore if writing fails

    # Fit final recruiter model on full data using Model A predictions
    ai_pred_full = predict_linear(XA_full, wA)  # Model A predictions on full data
    ai_pred_full = np.clip(ai_pred_full, 0.0, 100.0)  # Clip to valid range
    m_ai_full = ai_pred_full.mean()  # Mean of full A preds
    s_ai_full = ai_pred_full.std() + 1e-8  # Std of full A preds
    ai_feat_full = (ai_pred_full - m_ai_full) / s_ai_full  # Standardized A feature
    X_fullB = add_intercept(np.column_stack([X_std_full, ai_feat_full]))  # Full B design matrix
    if not recruiter_missing:
        wB_final = fit_logistic_regression(X_fullB, yB, compute_sample_weights(yB), lr=0.05, epochs=3000, seed=42)  # Fit final B
        with open(out_dir / "recruiter_model.pkl", "wb"):  # Open artifact path
            pickle.dump({
                "type": "logistic_numpy",
                "weights": wB_final.tolist(),
                "feature_columns": feat_cols_b,
                "preproc": preproc_params,
                "ai_feature_standardization": {"mean": float(m_ai_full), "std": float(s_ai_full)},
            }, open(out_dir / "recruiter_model.pkl", "wb"))  # Serialize model bundle

        # Coefficients for interpretability
        coef_map = {feat_cols_b[i]: float(wB_final[i]) for i in range(len(feat_cols_b))}  # Map feature names to weights
        import csv  # CSV writer for human-readable coefficients
        with open(out_dir / "coefficients_recruiter.csv", "w", newline="", encoding="utf-8") as f:  # Open CSV
            writer = csv.writer(f)
            writer.writerow(["feature", "coefficient", "abs_coefficient"])  # Header
            for name, val in sorted(coef_map.items(), key=lambda kv: abs(kv[1]), reverse=True):  # Sort by magnitude
                writer.writerow([name, f"{val:.6f}", f"{abs(val):.6f}"])  # Write row

        # Holdout metrics json
        holdout_metrics = {  # Bundle holdout metrics
            "roc_auc": auc_hold,
            "pr_auc": pr_auc_hold,
            "f1": best_f1,
            "best_threshold": best_th,
            "cost_thresholds": {"1:1": th_1_1_h, "3:1": th_3_1_h, "5:1": th_5_1_h},
            "confusion_matrix": [[int(best_cm[0,0]), int(best_cm[0,1])], [int(best_cm[1,0]), int(best_cm[1,1])]],
        }
        (out_dir / "holdout_metrics.json").write_text(json.dumps(holdout_metrics, indent=2), encoding="utf-8")  # Save JSON

    # Pipeline config
    pipeline_cfg = {  # Final pipeline configuration snapshot
        "seed": 42,
        "features_used": feature_cols,
        "group_kfold": 5,
        "group_col": group_col,
        "targets": {"ai_score": ai_score_col, "recruiter": recruiter_col if not recruiter_missing else None},
        "thresholds": {
            "max_f1": best_th if not recruiter_missing else None,
            "cost_opt": {"1:1": th_1_1_h if not recruiter_missing else None, "3:1": th_3_1_h if not recruiter_missing else None, "5:1": th_5_1_h if not recruiter_missing else None},
        },
        "artifacts": [
            "ai_score_model.pkl", "ai_score_cv_metrics.json", "ai_score_oof.csv",
            "y_true_vs_pred_scatter.png", "error_hist.png",
            *( ["recruiter_model.pkl", "recruiter_cv_metrics.json", "holdout_metrics.json", "threshold_report.txt", "pr_curve_recruiter.png", "confusion_matrix_recruiter.png", "reliability_plot_recruiter.png", "coefficients_recruiter.csv", "label_prep_report.txt"] if not recruiter_missing else ["labels_missing_report.txt"] ),
        ],
    }
    (out_dir / "pipeline_config.json").write_text(json.dumps(pipeline_cfg, indent=2), encoding="utf-8")  # Save config JSON

    # Print paths
    print(f"Saved ai_score_model.pkl: {(out_dir / 'ai_score_model.pkl').resolve()}")  # Confirm path
    print(f"Saved ai_score_cv_metrics.json: {(out_dir / 'ai_score_cv_metrics.json').resolve()}")  # Confirm path
    print(f"Saved numeric_scaling_report.json: {(out_dir / 'numeric_scaling_report.json').resolve()}")  # Confirm path
    print(f"Saved cats_encoding_report.txt: {(out_dir / 'cats_encoding_report.txt').resolve()}")  # Confirm path
    print(f"Saved step3_4_audit.txt: {(out_dir / 'step3_4_audit.txt').resolve()}")  # Confirm path
    if not recruiter_missing:
        print(f"Saved recruiter_model.pkl: {(out_dir / 'recruiter_model.pkl').resolve()}")  # Confirm path
        print(f"Saved recruiter_cv_metrics.json: {(out_dir / 'recruiter_cv_metrics.json').resolve()}")  # Confirm path
        print(f"Saved holdout_metrics.json: {(out_dir / 'holdout_metrics.json').resolve()}")  # Confirm path
        print(f"Saved threshold_report.txt: {(out_dir / 'threshold_report.txt').resolve()}")  # Confirm path
        print(f"Saved plots: {(out_dir / 'y_true_vs_pred_scatter.png').resolve()}, {(out_dir / 'error_hist.png').resolve()}, {(out_dir / 'pr_curve_recruiter.png').resolve()}, {(out_dir / 'confusion_matrix_recruiter.png').resolve()}, {(out_dir / 'reliability_plot_recruiter.png').resolve()}")  # Confirm plot paths
        print(f"Saved label_prep_report.txt: {(out_dir / 'label_prep_report.txt').resolve()}")  # Confirm path
        print(f"Saved winsorization_compare.txt: {(out_dir / 'winsorization_compare.txt').resolve()}")  # Confirm path
        print(f"Saved imbalance_benchmark_report.json: {(out_dir / 'imbalance_benchmark_report.json').resolve()}")  # Confirm path
        print(f"Saved pr_curve_recruiter_benchmark.png: {(out_dir / 'pr_curve_recruiter_benchmark.png').resolve()}")  # Confirm path
        print(f"Saved reliability_plots_benchmark.png: {(out_dir / 'reliability_plots_benchmark.png').resolve()}")  # Confirm path
        print(f"Saved recruiter_model_best.pkl: {(out_dir / 'recruiter_model_best.pkl').resolve()}")  # Confirm path
    else:
        print("Recruiter_Decision column not found; saved labels_missing_report.txt and skipped Model B training and holdout evaluation.")  # Inform skip
    # Calibration improvement summary
    if not recruiter_missing:
        mean_b_before = float(np.mean(brier_before))  # Mean Brier score before calibration
        mean_b_after = float(np.mean(brier_after))  # Mean Brier score after calibration
        improved = mean_b_after < mean_b_before  # Improvement flag
        print(f"Calibration Brier score improved: {improved} (before={mean_b_before:.4f}, after={mean_b_after:.4f})")  # Print summary
        # Explicit statement when no categoricals and class weights best
        try:
            bench = json.loads((out_dir / 'imbalance_benchmark_report.json').read_text(encoding='utf-8'))  # Load benchmark
            if not type_info['categorical'] and bench['summary'].get('best_strategy') == 'class_weights':  # No cats, class weights best
                print("No categorical columns were found and class weights remain the best strategy.")  # Inform
        except Exception:
            pass  # Ignore errors
    else:
        print("Calibration Brier score improved: N/A (Recruiter_Decision missing)")  # Not applicable


def agg(items, key):  # Utility to compute mean and sample std for a list of dicts
    vals = [d[key] for d in items]  # Extract values
    return {"mean": float(np.mean(vals)), "std": float(np.std(vals, ddof=1))}  # Mean and sample std


if __name__ == "__main__":  # Script entry point
    main()  # Run main pipeline