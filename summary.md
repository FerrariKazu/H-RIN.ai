# Project Reorganization Summary

Run ID: `20251112_0255`
Generated: `2025-11-12 02:55 UTC`

This document summarizes all file organization, pointers, and documentation updates performed to make the repository clean, navigable, and reproducible.

## Structure Overview

- `configs/`
  - `latest.json` — stable pointers to current best artifacts (models, metrics, plots, summaries)
  - `columns.json`, `columns_clean.json` — column configuration files
- `data/`
  - `enriched_dataset.csv` — enriched features dataset
  - `data_CLEANED_FIXED.csv` — cleaned and fixed base dataset
- `metrics/`
  - `cv/` — cross-validation metrics and out-of-fold predictions
  - `holdout/` — holdout evaluation metrics and thresholding report
  - `benchmark/` — winsorization and imbalance benchmarking
  - `coefficients/` — model coefficient exports
  - `archive/` — archived baseline metrics
- `models/`
  - `model_a/` — AI Score model (`ai_score_model.pkl`)
  - `model_b/` — Recruiter Decision model (`recruiter_model.pkl`, `recruiter_model_best.pkl`)
  - `archive/` — older checkpoints (`model.pkl`, `model_clean.pkl`)
- `plots/`
  - `model_a/` — regression diagnostic plots
  - `model_b/` — classification PR/confusion/reliability plots
  - `benchmark/` — strategy comparison plots
  - `archive/` — baseline PR/confusion matrix and reliability plots
- `reports/`
  - `project_summary.md` — stable pointer to latest full summary
  - `project_summary_20251112_0255.md` — timestamped full summary
  - `model_card.txt` — concise model card (purpose, metrics, guardrails)
  - `feature_engineering_report.txt` — details of feature engineering steps
  - `audits/` — guardrail and audit reports (`leakage_audit.txt`, `imbalance_report.txt`, `step3_4_audit.txt`, `label_prep_report.txt`, `cats_encoding_report.txt`, `numeric_scaling_report.json`)
- `scripts/`
  - `analyze_ai_high_performer.py`, `engineer_resume_features.py`, `train_baseline.py` — utility and baseline scripts
- Root files
  - `manifest.json` — computed manifest of files with sizes and hashes
  - `relocation_map.json` — mapping of moved files

## Key Actions Completed

- Computed `manifest.json` to track file paths, sizes, and SHA256 hashes.
- Compiled `reports/project_summary_20251112_0255.md` and updated `reports/project_summary.md` as a stable pointer.
- Wrote `reports/model_card.txt` capturing model purpose, configuration, metrics, calibration, and guardrails.
- Created `configs/latest.json` pointing to best models, key metrics, reports, and plots.
- Organized plots and metrics:
  - Moved baseline plots to `plots/archive/` and baseline metrics to `metrics/archive/`.
  - Grouped model-specific plots under `plots/model_a/` and `plots/model_b/`.
  - Grouped benchmarking artifacts under `plots/benchmark/` and `metrics/benchmark/`.
- Organized reports and audits into `reports/` and `reports/audits/`.
- Moved configuration files to `configs/` and data files under `data/`.
- Relocated utility scripts to `scripts/` for clarity.

## Best Artifacts and Pointers

- Models
  - `models/model_a/ai_score_model.pkl`
  - `models/model_b/recruiter_model.pkl` (current best)
- Metrics
  - CV: `metrics/cv/ai_score_cv_metrics.json`, `metrics/cv/recruiter_cv_metrics.json`
  - Holdout: `metrics/holdout/holdout_metrics.json`, `metrics/holdout/threshold_report.txt`
- Reports
  - Summary: `reports/project_summary.md`
  - Model card: `reports/model_card.txt`
  - Audits: `reports/audits/`
- Plots
  - Model A: `plots/model_a/`
  - Model B: `plots/model_b/`
  - Benchmark: `plots/benchmark/`
  - Baseline archive: `plots/archive/`

## Notes and Next Steps

- Use `configs/latest.json` as the single source of truth for current best artifacts.
- Reference `manifest.json` for checksums and file verification.
- Consider adding a small utility under `scripts/` to regenerate `manifest.json` on demand.
- If desired, create a README with quick-start commands and a diagram of the pipeline.

---

For any future changes, update `relocation_map.json` and re-run manifest generation to keep the repository consistent.