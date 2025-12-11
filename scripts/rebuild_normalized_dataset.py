"""  # Module docstring: explains purpose, inputs, outputs, and validations
Rebuild normalized training dataset using the Skill Normalization Layer.

Inputs
- `data/enriched_dataset.csv` (or a raw text source if available).
- `agent/skill_normalization.py` (uses `build_feature_vector`).
- `agent/skill_registry.json` and `agent/mapping_rules.json` (loaded by the agent).

Output
- `data/normalized_dataset_v2.csv`: dataframe containing
  - `Resume_ID`
  - `AI Score (0-100)`
  - `Recruiter_Decision` (renamed from `Recruiter Decision` if needed)
  - ALL features required by pipeline (model_a and model_b)
  - No missing values; numeric dtypes for all features.

Validation
- Every feature present in `pipeline_config.json` -> `features_used` MUST appear.
- No unexpected columns beyond features + labels.
- All feature columns must be numeric (int/float).

This script does NOT train any model and does NOT modify label values.
"""

from __future__ import annotations  # Future annotations for forward references

import argparse  # CLI argument parsing
import json  # JSON config reading/writing
import os # OS module for path manipulation
from pathlib import Path  # Filesystem path utilities
from typing import Dict, List  # Type hints for clarity

import pandas as pd  # DataFrame manipulation
import numpy as np  # Numeric checks and arrays

# Import the feature builder from the agent
from pathlib import Path as _PathForSys  # Alias for local sys.path injection
import sys as _sys  # Access to Python runtime path
# Ensure repository root is on sys.path for `agent` package import
_repo_root = _PathForSys(__file__).resolve().parent.parent  # Repo root folder
if str(_repo_root) not in _sys.path:  # Inject once to avoid duplicates
    _sys.path.insert(0, str(_repo_root))  # Prepend to module search path

from agent import build_feature_vector  # Feature vector builder from normalization layer
# For diagnostics (unmapped skills), leverage internal helpers
from agent.skill_normalization import extract_skills, normalize_skill  # Raw detection & canonicalization


def load_required_features(config_paths: List[Path]) -> List[str]:  # Determine required feature schema
    """Load the canonical feature list from `features_used` in pipeline configs.

    We prefer `pipeline_config.json` at repo root, but also accept a fallback copy
    under `data/pipeline_config.json` if present.
    """
    for p in config_paths:  # Iterate possible config locations
        if p.exists():  # If the config file exists
            cfg = json.loads(p.read_text(encoding="utf-8"))  # Read JSON contents
            feats = cfg.get("features_used", [])  # Extract feature list
            if feats:  # If non-empty
                return list(feats)  # Return as list
    raise FileNotFoundError("Could not load features_used from pipeline_config.json")  # Fail if missing


def detect_text_column(df: pd.DataFrame) -> str:  # Choose which column contains raw resume text
    """Detect the raw text column to feed into the normalization agent.

    Prefers `text_all`, then falls back to common textual fields if needed.
    """
    candidates = [  # Ordered preference for text sources
        "text_all",
        "Resume_Text",
        "Resume Summary",
        "Summary",
        "Description",
        "Skills",  # last resort: skills list
    ]
    norm = {str(c).strip().lower(): c for c in df.columns}  # Map normalized names to originals
    for alias in candidates:  # Scan aliases by priority
        key = alias.strip().lower()  # Normalize alias
        if key in norm:  # If present in DataFrame
            return norm[key]  # Return actual column name
    # If nothing matches, raise for explicit handling
    raise KeyError("No suitable resume text column found (looked for text_all, Resume_Text, etc.)")


def ensure_numeric(df: pd.DataFrame, feature_cols: List[str]) -> pd.DataFrame:  # Enforce numeric types
    """Coerce feature columns to numeric types and fill NaNs with 0.

    Cast to int when all values are whole numbers (e.g., flags/counts).
    """
    out = df.copy()  # Work on a copy to avoid mutating input
    for c in feature_cols:  # Iterate through features
        out[c] = pd.to_numeric(out[c], errors="coerce").fillna(0)  # Coerce and fill
        vals = out[c].to_numpy()  # Extract NumPy array for checks
        # If all values are effectively integers, cast to int
        if np.all(np.isfinite(vals)) and np.allclose(vals % 1, 0):  # Whole numbers check
            out[c] = out[c].astype(int)  # Cast to int for flags/counts
    return out  # Return type-safe DataFrame


def main():  # Entrypoint: orchestrates reading, normalization, validation, and reporting
    parser = argparse.ArgumentParser(description="Rebuild normalized dataset with skill normalization layer")  # CLI parser
    parser.add_argument("--input", default=os.path.join("data", "enriched_dataset.csv"), help="Path to input CSV")  # Input path arg
    parser.add_argument("--output", default=os.path.join("data", "normalized_dataset_v2.csv"), help="Path to output CSV")  # Output path arg
    args = parser.parse_args()  # Parse args from command line

    in_path = Path(args.input)  # Resolve input path
    out_path = Path(args.output)  # Resolve output path

    if not in_path.exists():  # Guard against missing input
        raise FileNotFoundError(f"Input CSV not found: {in_path}")  # Fail early if missing

    df = pd.read_csv(in_path)  # Load original dataset

    # Load required features from pipeline configs
    req_features = load_required_features([  # Determine schema
        Path(os.path.join("pipeline_config.json")),
        Path(os.path.join("data", "pipeline_config.json")),
    ])

    # Identify label/ID columns
    label_ai = "AI Score (0-100)"  # AI Score label name
    label_recruiter_out = "Recruiter_Decision"  # Required output name for recruiter label
    label_recruiter_in_candidates = ["Recruiter_Decision", "Recruiter Decision"]  # Acceptable input names
    label_id = "Resume_ID"  # Unique key column

    # Map recruiter label column to desired name without modifying values
    recruiter_in = None  # Initialize recruiter column name
    for cand in label_recruiter_in_candidates:  # Search candidate names
        if cand in df.columns:  # If found in DataFrame
            recruiter_in = cand  # Use this column
            break  # Stop at first match
    if recruiter_in is None:  # If none matched
        raise KeyError("Recruiter decision label not found (expected 'Recruiter_Decision' or 'Recruiter Decision')")  # Fail

    text_col = detect_text_column(df)  # Detect raw text column for normalization

    rows: List[Dict[str, float]] = []  # Output rows accumulator
    unmapped_skills_counter: Dict[str, int] = {}  # Track unmapped skill phrases

    baseline_skill_col = "feat_num_skills_matched"  # Coverage metric column
    baseline_present = baseline_skill_col in df.columns  # Check presence in original
    baseline_total = float(df[baseline_skill_col].sum()) if baseline_present else 0.0  # Sum baseline coverage

    for _, row in df.iterrows():  # Iterate resumes
        text = str(row.get(text_col, ""))  # Extract raw text
        vec = build_feature_vector(text)  # Build normalized feature vector

        # Gather diagnostics: unmapped skills
        try:
            raw_skills = extract_skills(text)  # Detect raw phrases
            for s in raw_skills:  # For each phrase
                canonical = normalize_skill(s)  # Attempt canonical mapping
                if not canonical:  # If mapping failed
                    key = s.strip().lower()  # Normalize phrase key
                    unmapped_skills_counter[key] = unmapped_skills_counter.get(key, 0) + 1  # Increment count
        except Exception:  # Robust to optional helper failures
            pass  # Skip diagnostics if helpers unavailable

        out_row: Dict[str, float] = {}  # Initialize output row
        for f in req_features:  # For each required feature
            if f in vec:  # Prefer agent-derived value
                out_row[f] = vec[f]  # Assign normalized feature
            else:
                val = row.get(f, 0)  # Fallback to original dataset value
                out_row[f] = val  # Store fallback value

        # Attach labels/ID (do not modify values)
        out_row[label_id] = row.get(label_id)  # Preserve Resume_ID
        out_row[label_ai] = row.get(label_ai)  # Preserve AI Score
        out_row[label_recruiter_out] = row.get(recruiter_in)  # Preserve recruiter decision

        rows.append(out_row)  # Append processed row to list

    out_df = pd.DataFrame(rows)  # Create output DataFrame

    missing = [f for f in req_features if f not in out_df.columns]  # Check for missing features
    if missing:  # If any missing
        raise AssertionError(f"Missing required feature columns: {missing}")  # Fail validation

    allowed = set(req_features + [label_id, label_ai, label_recruiter_out])  # Allowed schema
    extras = [c for c in out_df.columns if c not in allowed]  # Detect unexpected columns
    if extras:  # If extras present
        out_df = out_df.drop(columns=extras)  # Drop them to satisfy strict schema

    out_df = ensure_numeric(out_df, req_features)  # Enforce numeric types

    out_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure output directory exists
    out_df.to_csv(out_path, index=False)  # Save normalized dataset

    processed = len(out_df)  # Number of resumes processed
    new_skill_total = float(out_df[baseline_skill_col].sum()) if baseline_skill_col in out_df.columns else 0.0  # New coverage sum
    coverage_delta = new_skill_total - baseline_total  # Difference in coverage
    coverage_pct_change = (  # Percent change vs baseline
        (coverage_delta / baseline_total * 100.0) if baseline_total > 0 else 0.0
    )

    domain_cols = [c for c in req_features if c.startswith("feat_job_")]  # Domain feature columns
    domain_counts = {d: int(out_df[d].sum()) for d in domain_cols if d in out_df.columns}  # After counts

    print("=== Normalization Summary ===")  # Header for summary
    print(f"Resumes processed: {processed}")  # Count of processed resumes
    print(f"Skill coverage (feat_num_skills_matched) total before: {baseline_total:.0f}")  # Baseline coverage
    print(f"Skill coverage (feat_num_skills_matched) total after:  {new_skill_total:.0f}")  # Post-normalization coverage
    print(f"Coverage improvement: {coverage_delta:.0f} ({coverage_pct_change:.2f}% change)")  # Improvement metric
    print("Job domain flags activated (post-normalization):")  # Domain counts header
    for d, cnt in domain_counts.items():  # Iterate domains
        print(f"  - {d}: {cnt}")  # Print each domain count

    mapped_domains = [d for d, cnt in domain_counts.items() if cnt > 0]  # Domains with activity
    if mapped_domains:  # If any active domains
        print("Domains inferred from skills/text:")  # Header
        for d in mapped_domains:  # List domains
            print(f"  - {d}")  # Print domain name

    if unmapped_skills_counter:  # If any unmapped phrases recorded
        print("Unmapped skill phrases (top 20 by frequency):")  # Header
        top = sorted(unmapped_skills_counter.items(), key=lambda x: (-x[1], x[0]))[:20]  # Top 20
        for phrase, count in top:  # Print each
            print(f"  - '{phrase}': {count}")  # Phrase and count
    else:
        print("All detected skill phrases were mapped to canonical features.")  # No unmapped phrases

    # Write small audit report with before/after counts per skill flag and domains
    audits_dir = Path(os.path.join("reports", "audits"))  # Audits directory path
    audits_dir.mkdir(parents=True, exist_ok=True)  # Ensure it exists
    audit_path = audits_dir / "skill_normalization_audit.txt"  # Audit file path

    skill_cols = [c for c in req_features if c.startswith("feat_skill_")]  # Skill feature columns
    before_skill_counts = {c: (int(df[c].sum()) if c in df.columns else 0) for c in skill_cols}  # Before sums
    after_skill_counts = {c: int(out_df[c].sum()) for c in skill_cols if c in out_df.columns}  # After sums

    before_domain_counts = {c: (int(df[c].sum()) if c in df.columns else 0) for c in domain_cols}  # Before domain sums
    after_domain_counts = {c: int(out_df[c].sum()) for c in domain_cols if c in out_df.columns}  # After domain sums

    lines = []  # Collect lines to write
    lines.append("Normalization Audit Report")  # Title
    lines.append("==========================")  # Underline
    lines.append(f"Input: {in_path}")  # Input file path
    lines.append(f"Output: {out_path}")  # Output file path
    lines.append(f"Resumes processed: {processed}")  # Count
    lines.append("")  # Spacer
    lines.append("Skill Flag Counts (before -> after)")  # Section header
    for c in sorted(skill_cols):  # Deterministic order
        b = before_skill_counts.get(c, 0)  # Before count
        a = after_skill_counts.get(c, 0)  # After count
        lines.append(f"- {c}: {b} -> {a}")  # Line entry
    lines.append("")  # Spacer
    lines.append("Job Domain Flag Counts (before -> after)")  # Section header
    for c in sorted(domain_cols):  # Deterministic order
        b = before_domain_counts.get(c, 0)  # Before count
        a = after_domain_counts.get(c, 0)  # After count
        lines.append(f"- {c}: {b} -> {a}")  # Line entry
    lines.append("")  # Spacer
    lines.append(f"Skill coverage (feat_num_skills_matched): {baseline_total:.0f} -> {new_skill_total:.0f}")  # Coverage summary
    lines.append(f"Coverage improvement: {coverage_delta:.0f} ({coverage_pct_change:.2f}% change)")  # Improvement metric

    audit_path.write_text("\n".join(lines), encoding="utf-8")  # Write report to disk

    print(f"Saved normalized dataset to: {out_path}")  # Confirm save location
    print(f"Wrote audit report to: {audit_path}")  # Confirm audit path


if __name__ == "__main__":  # Script entry point
    main()  # Invoke main