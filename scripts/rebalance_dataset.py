import argparse # Imports the argparse module for parsing command-line arguments.
import os
from pathlib import Path # Imports the Path class for object-oriented filesystem paths.
from typing import Dict, List, Tuple # Imports specific types for type hinting.

import numpy as np # Imports numpy for numerical operations.
import pandas as pd # Imports pandas for data manipulation and analysis.


# Defines a set of strings considered as positive labels for recruiter decisions.
POSITIVE_LABELS = {"1", "yes", "hire", "accept", "advance", "move forward", "positive"}
# Defines a set of strings considered as negative labels for recruiter decisions.
NEGATIVE_LABELS = {"0", "no", "reject", "decline", "hold", "do not move", "negative"}


def map_recruiter_label(val) -> int:
    # Checks if the input value is NaN (Not a Number).
    if pd.isna(val):
        return np.nan # Returns NaN if the value is NaN.
    # Converts the value to a string, strips whitespace, and converts to lowercase.
    s = str(val).strip().lower()
    # If the processed string is in the set of positive labels, return 1.
    if s in POSITIVE_LABELS:
        return 1
    # If the processed string is in the set of negative labels, return 0.
    if s in NEGATIVE_LABELS:
        return 0
    # Fallback for common labels that might not be in the exact sets.
    # If the string starts with "hir", return 1 (e.g., "hired").
    if s.startswith("hir"):
        return 1
    # If the string starts with "rej" or "decl", return 0 (e.g., "rejected", "declined").
    if s.startswith("rej") or s.startswith("decl"):
        return 0
    return np.nan # Returns NaN if no known label is matched.


def oversample_minority_to_majority(df: pd.DataFrame, label_col: str) -> pd.DataFrame:
    # Separates the DataFrame into positive and negative label groups.
    pos = df[df[label_col] == 1]
    neg = df[df[label_col] == 0]
    # If either group is empty, no rebalancing can be done, so return the original DataFrame.
    if len(pos) == 0 or len(neg) == 0:
        # nothing we can do; return as-is
        return df
    # Determines which group is the minority and which is the majority.
    if len(pos) > len(neg):
        minority = neg
        majority = pos
    else:
        minority = pos
        majority = neg
    # Calculates the number of samples needed to oversample the minority to match the majority size.
    up_count = len(majority) - len(minority)
    # Randomly samples from the minority group with replacement to reach the `up_count`.
    minority_up = minority.sample(n=up_count, replace=True, random_state=42)
    # Concatenates the original DataFrame with the oversampled minority samples.
    return pd.concat([df, minority_up], axis=0)


def equalize_bins_by_downsampling(df: pd.DataFrame, bin_col: str) -> pd.DataFrame:
    # Counts the occurrences of each bin and filters out bins with zero or negative counts.
    sizes = df[bin_col].value_counts()
    sizes = sizes[sizes > 0]
    # If no bins have actual rows, return an empty DataFrame.
    if sizes.empty:
        return df.iloc[0:0]
    # Determines the target size for each bin, which is the count of the smallest bin.
    target = int(sizes.min())
    parts = [] # Initializes a list to store sampled parts of the DataFrame.
    # Iterates through each bin and its count.
    for b, count in sizes.items():
        # Skips bins with zero or negative counts.
        if count <= 0:
            continue
        # Filters the DataFrame for the current bin.
        d = df[df[bin_col] == b]
        # Samples `target` number of rows from the current bin without replacement.
        parts.append(d.sample(n=target, replace=False, random_state=42))
    # Concatenates all sampled parts to form the rebalanced DataFrame.
    return pd.concat(parts, axis=0)


def enforce_label_balance_per_bin(df: pd.DataFrame, bin_col: str, label_col: str) -> pd.DataFrame:
    parts = [] # Initializes a list to store rebalanced parts of the DataFrame.
    # Determine uniform target size per bin (use current bin sizes)
    # Counts the occurrences of each bin.
    sizes = df[bin_col].value_counts()
    # Iterates through each bin and its size.
    for b, size in sizes.items():
        # Filters the DataFrame for the current bin.
        bin_df = df[df[bin_col] == b]
        # Skips bins with zero or negative sizes.
        if size <= 0:
            continue
        # Separates the bin DataFrame into positive and negative label groups.
        pos = bin_df[bin_df[label_col] == 1]
        neg = bin_df[bin_df[label_col] == 0]
        # Desired split: aims for an even split within each bin.
        pos_target = size // 2
        neg_target = size - pos_target
        # Sample (downsample or oversample as needed)
        # Samples from the positive group, oversampling if `pos_target` is greater than available positive samples.
        pos_samp = pos.sample(n=pos_target, replace=(len(pos) < pos_target), random_state=42)
        # Samples from the negative group, oversampling if `neg_target` is greater than available negative samples.
        neg_samp = neg.sample(n=neg_target, replace=(len(neg) < neg_target), random_state=42)
        # Concatenates the sampled positive and negative groups for the current bin.
        parts.append(pd.concat([pos_samp, neg_samp], axis=0))
    # Concatenates all rebalanced bin parts to form the final DataFrame.
    return pd.concat(parts, axis=0)


def main():
    # Creates an argument parser with a description.
    ap = argparse.ArgumentParser(description="Rebalance dataset for Recruiter_Decision and AI Score")
    # Adds an argument for the input CSV file path.
    ap.add_argument("--input", default=os.path.join("data", "normalized_dataset_v2.csv"), help="Input CSV path")
    # Adds an argument for the output balanced CSV file path.
    ap.add_argument("--output", default=os.path.join("data", "C_dataset.csv"), help="Output balanced CSV path")
    # Adds an argument for the AI Score column name.
    ap.add_argument("--ai_score_col", default="AI Score (0-100)", help="AI Score column name")
    # Adds an argument for the label column name (Recruiter_Decision).
    ap.add_argument("--label_col", default="Recruiter_Decision", help="Label column name")
    # Adds an argument for the number of quantile bins for AI Score.
    ap.add_argument("--bins", type=int, default=10, help="Number of quantile bins for AI Score")
    # Parses the command-line arguments.
    args = ap.parse_args()

    # Creates Path objects for the input and output file paths.
    src = Path(args.input)
    dst = Path(args.output)
    # Asserts that the input file exists, raising an error if not.
    assert src.exists(), f"Input file not found: {src}"
    # Reads the input CSV file into a pandas DataFrame.
    df = pd.read_csv(src)

    # Map labels to binary for balancing
    # Maps the recruiter decision labels to binary (0 or 1) using the `map_recruiter_label` function.
    df["_label_bin"] = df[args.label_col].map(map_recruiter_label)
    # Stores the counts of binary labels before rebalancing.
    before_counts = df["_label_bin"].value_counts().to_dict()

    # Drop rows with unknown labels
    # Filters out rows where the binary label is not 0 or 1.
    df = df[df["_label_bin"].isin([0, 1])].copy()

    # Prepare AI Score numeric
    # Converts the AI Score column to numeric, coercing errors to NaN.
    ai = pd.to_numeric(df[args.ai_score_col], errors="coerce")
    # Filters out rows where the AI Score is NaN.
    df = df[~ai.isna()].copy()
    # Creates a new column for numeric AI Score.
    df["_ai_score"] = pd.to_numeric(df[args.ai_score_col], errors="coerce")

    # Create quantile bins for AI Score
    try:
        # Creates quantile bins for the AI Score using the specified number of bins.
        df["_ai_bin"] = pd.qcut(df["_ai_score"], q=args.bins, duplicates="drop")
    except ValueError:
        # In case of too few unique values, fallback to 5 bins
        # If a ValueError occurs (e.g., not enough unique values for the requested bins), falls back to 5 bins.
        df["_ai_bin"] = pd.qcut(df["_ai_score"], q=5, duplicates="drop")

    # Step 1: Globally balance labels by oversampling minority to majority size (keep row count similar)
    # Rebalances the dataset by oversampling the minority class of the binary label.
    df_bal = oversample_minority_to_majority(df, "_label_bin")

    # Recompute AI bins after oversampling
    try:
        # Recomputes AI bins after oversampling, handling potential ValueErrors.
        df_bal["_ai_bin"] = pd.qcut(pd.to_numeric(df_bal[args.ai_score_col], errors="coerce"), q=args.bins, duplicates="drop")
    except ValueError:
        df_bal["_ai_bin"] = pd.qcut(pd.to_numeric(df_bal[args.ai_score_col], errors="coerce"), q=5, duplicates="drop")

    # Step 2: Equalize AI Score bin sizes by downsampling to the smallest bin count
    # Equalizes the size of AI Score bins by downsampling to the smallest bin.
    df_bal = equalize_bins_by_downsampling(df_bal, "_ai_bin")

    # Step 3: Globally re-balance labels after bin equalization (oversample minority)
    # Re-balances labels again after bin equalization.
    df_bal = oversample_minority_to_majority(df_bal, "_label_bin")

    # Shuffle final dataset for randomness
    # Shuffles the rebalanced DataFrame randomly.
    df_bal = df_bal.sample(frac=1.0, random_state=42).reset_index(drop=True)

    # Build a small audit report
    # Stores the counts of binary labels after rebalancing.
    after_counts = df_bal["_label_bin"].value_counts().to_dict()
    # Stores the AI Score bin counts before rebalancing.
    bin_counts_before = df["_ai_bin"].value_counts().to_dict()
    # Stores the AI Score bin counts after rebalancing, filtering out empty bins.
    bin_counts_after = df_bal["_ai_bin"].value_counts()
    bin_counts_after = bin_counts_after[bin_counts_after > 0].to_dict()

    # Add a uniformized AI Score column (0-100) via rank-based transform
    # Calculates a uniform AI Score (0-100) based on rank-based transformation.
    uniform = df_bal[args.ai_score_col].rank(method="average", pct=True) * 100.0
    # Adds the uniform AI Score as a new column.
    df_bal["AI Score (Uniform 0-100)"] = uniform

    # Clean helper columns and write
    # Drops temporary helper columns from the DataFrame.
    df_out = df_bal.drop(columns=["_label_bin", "_ai_score"])  # keep _ai_bin for transparency if desired
    # Creates parent directories for the output file if they don't exist.
    dst.parent.mkdir(parents=True, exist_ok=True)
    # Saves the rebalanced DataFrame to a CSV file.
    df_out.to_csv(dst, index=False)

    # Emit concise summary
    print("=== Rebalance Summary ===") # Prints a header for the summary.
    print(f"Input: {src}") # Prints the input file path.
    print(f"Output: {dst}") # Prints the output file path.
    print(f"Rows before: {len(df)} | Rows after: {len(df_out)}") # Prints row counts before and after rebalancing.
    print(f"Label counts before: {before_counts}") # Prints label counts before rebalancing.
    print(f"Label counts after:  {after_counts}") # Prints label counts after rebalancing.
    print("AI Score bin counts before:") # Prints a header for AI Score bin counts before.
    for k, v in bin_counts_before.items(): # Iterates and prints each AI Score bin count before.
        print(f"  {k}: {v}")
    print("AI Score bin counts after:") # Prints a header for AI Score bin counts after.
    for k, v in bin_counts_after.items(): # Iterates and prints each AI Score bin count after.
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main() # Calls the main function when the script is executed.