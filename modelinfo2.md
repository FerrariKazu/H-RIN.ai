# Project Model Summary

## Overview

- Purpose: Score candidate resumes and classify recruiter-readiness.
- Architecture: Two-model pipeline
  - Model A (Regression): predicts `AI Score (0-100)`.
  - Model B (Classification): predicts `Recruiter_Decision` with calibrated probabilities.
- Validation: 5-fold GroupKFold on `Resume_ID` to prevent leakage.
- Reproducibility: seed `42` and documented audits.

## Contents

- `data/` cleaned and enriched datasets; label presence confirmed.
- `configs/` column configs and `latest.json` pointers to best artifacts.
- `models/` current (`model_a`, `model_b`, `latest`) and archived checkpoints.
- `metrics/` CV, holdout, benchmark, coefficients, baseline archive.
- `plots/` model diagnostics, benchmarks, baseline archive.
- `reports/` project summary, model card, audits (leakage, imbalance, scaling, encoding).
- `scripts/` training, analysis, manifest regeneration, PNG repair.
- `manifest.json` integrity with sizes and SHA256; `relocation_map.json` moves.

## Capabilities

- Predicts continuous AI Score and binary recruiter decision.
- Produces calibrated probabilities and threshold sweeps; best threshold `0.12`.
- Exports CV/holdout metrics, coefficients, and diagnostic plots.
- Runs audits: winsorization applied; class imbalance handled via `class_weights`.
- Ensures file integrity via manifest; repairs PNG header corruption.

## Key Metrics

- Regression (CV): MAE `~6.02`, RMSE `~8.13`, R² `~0.8469`, Pearson `~0.9461`.
- Classification (CV): ROC AUC `~0.9976`, PR AUC `~0.99947`, F1 `~0.9902`.
- Holdout (Model B): ROC AUC `0.99718`, PR AUC `0.99936`, F1 `0.98788`, threshold `0.12`.

## Usage

- Train: `python train_two_model_pipeline.py`.
- Latest pointers: `configs/latest.json`.
- Regenerate manifest: `python scripts/regenerate_manifest.py`.

## Notes

- No non-binary categorical columns detected; many features are binary/boolean.
- Winsorization used for numeric tails; calibration improves Brier score.