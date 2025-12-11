# Model Info (Two-Model Pipeline)

## Overview

- Purpose: Rank candidates by predicted AI Score and classify recruiter decision readiness.
- Architecture: Two-model pipeline
  - Model A (Regression): predicts `AI Score (0-100)`.
  - Model B (Classification): predicts `Recruiter_Decision` with calibrated probabilities.
- CV: Group K-Fold (`k=5`) grouped by `Resume_ID` to avoid leakage.
- Seed: `42` for reproducibility.

## Data & Labels

- Source data: `data/enriched_dataset.csv`, `data/data_CLEANED_FIXED.csv`.
- Labels:
  - Regression target: `AI Score (0-100)`.
  - Classification target: `Recruiter_Decision` (confirmed present; see `reports/audits/label_prep_report.txt`).
- Group column: `Resume_ID` for CV.

## Features

- Skills, certifications, degrees, job categories, promotions, experience, text stats.
- Examples: `feat_skill_python`, `feat_skill_sql`, `feat_cert_aws`, `feat_degree_master`, `feat_job_product`, `feat_num_promotions`, `feat_years_experience_extracted`, `Experience (Years)`, `Projects Count`, text length features.
- Full list: see `pipeline_config.json` (`features_used`) or `configs/columns_clean.json`.

## Training Configuration

- Cross-validation: 5-fold GroupKFold on `Resume_ID`.
- Preprocessing audits:
  - Winsorization: used (numeric tails tamed).
  - Imbalance: `class_weights` chosen as best strategy for CV.
  - Categorical: no non-binary categoricals detected.
- Calibration (Model B): Brier score improved after calibration.
- Thresholding: tuned to maximize F1 on holdout.

## Metrics Summary

- Model A (AI Score regression, CV summary):
  - MAE: mean `6.02`, std `0.13`
  - RMSE: mean `8.13`, std `0.16`
  - R²: mean `0.8469`, std `0.0167`
  - Pearson r: mean `0.9461`, std `0.0082`
  - Spearman rho: mean `0.8837`, std `0.0398`
  - Source: `metrics/cv/ai_score_cv_metrics.json`

- Model B (Recruiter classification, CV summary):
  - ROC AUC: mean `0.9976`, std `0.0018`
  - PR AUC: mean `0.99947`, std `0.00037`
  - F1: mean `0.9902`, std `0.0033`
  - Precision: mean `0.9866`, std `0.0049`
  - Recall: mean `0.9938`, std `0.0043`
  - Brier: before `0.03135` → after `0.02711`
  - Source: `metrics/cv/recruiter_cv_metrics.json`

- Model B (Holdout):
  - ROC AUC: `0.99718`
  - PR AUC: `0.99936`
  - F1: `0.98788`
  - Best threshold: `0.12` (also optimal for cost 1:1, 3:1, 5:1)
  - Confusion matrix: `[[33, 4], [0, 163]]` (TN, FP; FN, TP)
  - Source: `metrics/holdout/holdout_metrics.json`, `metrics/holdout/threshold_report.txt`

## Thresholds & Calibration

- Selected threshold: `0.12` (max F1 and cost-optimal in sweep).
- Threshold sweep: detailed in `metrics/holdout/threshold_report.txt`.
- Calibration: reliability curves and Brier improvements indicate well-calibrated probabilities.

## Artifacts & Paths

- Models
  - Model A: `models/model_a/ai_score_model.pkl`
  - Model B: `models/model_b/recruiter_model.pkl` (current best)
- Metrics
  - Regression CV: `metrics/cv/ai_score_cv_metrics.json`
  - Classification CV: `metrics/cv/recruiter_cv_metrics.json`
  - Holdout: `metrics/holdout/holdout_metrics.json`, `metrics/holdout/threshold_report.txt`
- Plots
  - Regression: `plots/model_a/error_hist.png`, `plots/model_a/y_true_vs_pred_scatter.png`
  - Classification: `plots/model_b/pr_curve_recruiter.png`, `plots/model_b/confusion_matrix_recruiter.png`, `plots/model_b/reliability_plot_recruiter.png`
  - Benchmark: `plots/benchmark/*`
  - Baseline archive: `plots/archive/*`
- Reports
  - Summary: `reports/project_summary_20251112_0255.md`
  - Model card: `reports/model_card.txt`
  - Audits: `reports/audits/*`
- Pointers
  - Latest artifact map: `configs/latest.json`
  - Manifest with hashes: `manifest.json`

## Repro & Ops

- Train pipeline: `python train_two_model_pipeline.py`
- Regenerate manifest: `python scripts/regenerate_manifest.py`
- Data and columns: `configs/columns_clean.json`, `data/` directory

## Guardrails & Audits

- Numeric features: `8` (winsorized tails)
- Boolean/binary features: `44`
- No non-binary categorical columns found.
- Imbalance best strategy (CV): `class_weights`
- See: `reports/audits/step3_4_audit.txt`, `reports/audits/leakage_audit.txt`, `reports/audits/numeric_scaling_report.json`, `reports/audits/cats_encoding_report.txt`, `reports/audits/imbalance_report.txt`

## Next Work Items (for later in chat)

- Hyperparameter tuning: explore regularization or model alternatives for Model A/B.
- Feature ablation: quantify contribution of top features; consider adding/removing engineered features.
- Calibration alternatives: test isotonic vs. Platt scaling; monitor Brier and reliability.
- Threshold sensitivity: derive business-optimal thresholds beyond F1 (vary costs).
- Fairness checks: subgroup performance and calibration across demographics if available.
- Robustness: drift monitoring and re-training cadence; add data quality checks.

---

For quick navigation and latest pointers, use `configs/latest.json`. For verification and integrity, use `manifest.json`.