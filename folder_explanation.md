# Folder and File Overview

This document briefly explains each folder and the purpose of key files.

## Root
- `train_two_model_pipeline.py` — End-to-end training pipeline for AI Score (regression) and Recruiter Decision (classification).
- `manifest.json` — Project manifest describing assets and metadata (hashes, categories).
- `pipeline_config.json` — Snapshot of pipeline configuration and artifact references.
- `summary.md` — High-level project summary and notes.
- `modelinfo.md` — Model information and documentation.
- `modelinfo2.md` — Additional model notes and documentation.
- `relocation_map.json` — Mapping of relocated/renamed assets.
- `imbalance_report.txt` — Dataset class imbalance summary.

## agent/
- `README.md` — Overview and usage notes for the agent module.
- `__init__.py` — Marks `agent` as a Python package.
- `extractor_examples.json` — Example inputs/outputs for data extraction.
- `mapping_rules.json` — Rules to map raw fields to standardized feature keys.
- `skill_normalization.py` — Normalizes skills using embeddings, aliases, and fuzzy matching.
- `skill_registry.json` — Canonical list of skills and aliases.

## archive/
- Historical backups and older artifacts.

## configs/
- `columns.json` — Original feature column definitions.
- `columns_clean.json` — Cleaned feature list used for training.
- `latest.json` — Latest configuration snapshot for the pipeline.

## data/
- `data_CLEANED_FIXED.csv` — Cleaned and fixed dataset.
- `enriched_dataset.csv` — Dataset with engineered features used by pipelines.
- `labels/` — Supplemental label files (e.g., recruiter decisions) to merge by key.
- `pipeline_config.json` — Data-level pipeline configuration snapshot (if present).

## logs/
- Runtime logs, debug outputs, and execution traces.

## metrics/
- `archive/` — Earlier metrics snapshots for reference.
  - `metrics_baseline.txt` — Baseline metrics summary.
  - `metrics_baseline_clean.txt` — Metrics summary after cleaning.
- `benchmark/` — Benchmarking outputs for preprocessing and imbalance strategies.
  - `imbalance_benchmark_report.json` — Comparison of strategies (class weights, under/over-sampling, SMOTE).
  - `winsorization_compare.txt` — Numeric winsorization comparison and decision.
- `coefficients/` — Model coefficients exports.
  - `coefficients.csv` — Coefficients from an earlier model run.
  - `coefficients_clean.csv` — Cleaned coefficients export.
  - `coefficients_recruiter.csv` — Recruiter model coefficients with magnitudes.
- `cv/` — Cross-validation artifacts.
  - `ai_score_cv_metrics.json` — CV metrics for AI Score (Model A).
  - `ai_score_oof.csv` — Out-of-fold predictions for AI Score.
  - `recruiter_cv_metrics.json` — CV metrics for Recruiter Decision (Model B).
- `holdout/` — Holdout evaluation artifacts.
  - `holdout_metrics.json` — Holdout performance metrics summary.
  - `threshold_report.txt` — Threshold selection report on holdout.

## models/
- `archive/` — Archived model binaries.
  - `model.pkl` — Archived model artifact.
  - `model_clean.pkl` — Archived cleaned model artifact.
- `latest/` — Latest model artifacts.
  - `ai_score_model.pkl` — Latest AI Score model bundle.
  - `recruiter_model.pkl` — Latest Recruiter model bundle.
- `model_a/` — Model A artifacts.
  - `ai_score_model.pkl` — Trained AI Score model.
- `model_b/` — Model B artifacts.
  - `recruiter_model.pkl` — Trained Recruiter model.
  - `recruiter_model_best.pkl` — Best holdout-tuned Recruiter model.

## plots/
- `archive/` — Older plots from previous runs.
  - `confusion_matrix.png` — Baseline confusion matrix plot.
  - `confusion_matrix_clean.png` — Confusion matrix after data cleaning.
  - `pr_curve.png` — Baseline precision-recall curve.
  - `pr_curve_clean.png` — Precision-recall curve after data cleaning.
  - `reliability_plot_foldX_before/after.png` — Per-fold reliability plots (pre/post calibration).
- `benchmark/` — Benchmarking visualization outputs.
  - `pr_curve_recruiter_benchmark.png` — PR curves overlay across strategies.
  - `reliability_plots_benchmark.png` — Reliability overlays across strategies.
- `model_a/` — Plots for AI Score.
  - `error_hist.png` — OOF error histogram.
  - `y_true_vs_pred_scatter.png` — Scatter of true vs OOF predicted AI Score.
- `model_b/` — Plots for Recruiter Decision.
  - `confusion_matrix_recruiter.png` — Holdout confusion matrix.
  - `pr_curve_recruiter.png` — Holdout precision-recall curve.
  - `reliability_plot_recruiter.png` — Holdout reliability plot.

## reports/
- `audits/` — Audit reports and pipeline decisions.
  - `cats_encoding_report.txt` — Categorical encoding summary and rare level handling.
  - `imbalance_report.txt` — Class imbalance analysis report.
  - `label_prep_report.txt` — Label discovery and merge report.
  - `leakage_audit.txt` — Leakage checks and findings.
  - `numeric_scaling_report.json` — Numeric scaling audit across CV folds.
  - `step3_4_audit.txt` — Preprocessing and strategy decisions summary.
- `feature_engineering_report.txt` — Summary of engineered features and their stats.
- `model_card.txt` — Model card documenting training setup and performance.
- `project_summary_YYYYMMDD_HHMM.md` — Time-stamped project summary.

## scripts/
- `analyze_ai_high_performer.py` — Analyzes features predictive of high performer label.
- `engineer_resume_features.py` — Builds resume-derived features and text/TF-IDF features.
- `regenerate_manifest.py` — Regenerates `manifest.json` and categorizes project artifacts.
- `train_baseline.py` — Trains a baseline classifier/regressor and saves artifacts.