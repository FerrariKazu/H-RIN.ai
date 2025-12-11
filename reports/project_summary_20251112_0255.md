# Project Summary (run_id: 20251112_0255)

## Overview
- Two-model pipeline:
  - Model A (Regression): `AI Score (0-100)`
  - Model B (Classification): `Recruiter_Decision`
- Data: `data/enriched_dataset.csv`
- Folds: 5 GroupKFold by `Resume_ID`
- Calibration: Brier improved from 0.03135 to 0.02711 (CV mean)
- Categorical: No non-binary categorical columns found
- Imbalance: Best CV strategy = `class_weights`
- Winsorization: used

## Configuration
- Seed: 42
- Features used: see `pipeline_config.json` (`features_used` list)
- Thresholds (initial config): `max_f1=0.12`; cost-opt 1:1, 3:1, 5:1 → 0.12

## Model A (AI Score) — Cross-Validation
Source: `metrics/cv/ai_score_cv_metrics.json`
- MAE mean: 6.018 (std 0.130)
- RMSE mean: 8.133 (std 0.155)
- R² mean: 0.847 (std 0.017)
- Pearson r mean: 0.946 (std 0.008)
- Spearman ρ mean: 0.884 (std 0.040)
- Plots: `plots/model_a/y_true_vs_pred_scatter.png`, `plots/model_a/error_hist.png`

## Model B (Recruiter Decision) — Cross-Validation
Source: `metrics/cv/recruiter_cv_metrics.json`
- ROC AUC mean: 0.9976 (std 0.00176)
- PR AUC mean: 0.99947 (std 0.00037)
- F1 mean: 0.9902 (std 0.00334)
- Precision mean: 0.9866 (std 0.00486)
- Recall mean: 0.9938 (std 0.00432)
- Brier (before → after): 0.03135 → 0.02711
- Plots: `plots/model_b/pr_curve_recruiter.png`, `plots/model_b/confusion_matrix_recruiter.png`, `plots/model_b/reliability_plot_recruiter.png`

## Model B — Holdout Evaluation (Best Strategy)
Source: `metrics/holdout/holdout_metrics.json`
- ROC AUC: 0.99718
- PR AUC: 0.99936
- F1: 0.98788
- Best threshold: 0.12
- Cost-opt thresholds (1:1, 3:1, 5:1): 0.12
- Confusion matrix [[TN, FP],[FN, TP]]: [[33, 4],[0, 163]]
- Threshold sweep: `metrics/holdout/threshold_report.txt`

## Imbalance Benchmark (CV)
Source: `metrics/benchmark/imbalance_benchmark_report.json`
- Strategies: `class_weights` (baseline), `undersample`, `oversample`
- Baseline PR AUC (cw): 0.99955; Best PR AUC (oversample): 0.99963
- Baseline Brier (cw): 0.02607; Best Brier (oversample): 0.02263
- Selected best strategy overall: `class_weights` (as per pipeline selection)
- Plots: `plots/benchmark/pr_curve_recruiter_benchmark.png`, `plots/benchmark/reliability_plots_benchmark.png`

## Audits and Guardrails
- Numeric scaling per fold: `reports/audits/numeric_scaling_report.json` (train/val means approx 0; stds near 1)
- Categorical encoding: `reports/audits/cats_encoding_report.txt` → No non-binary categorical columns found
- Step3_4 summary: `reports/audits/step3_4_audit.txt`
  - Numeric features: 8; Boolean/binary: 44
  - Winsorization: used
  - Imbalance best strategy: class_weights
- Label prep: `reports/audits/label_prep_report.txt`

## Artifacts
- Models: `models/model_a/ai_score_model.pkl`, `models/model_b/recruiter_model.pkl`, `models/model_b/recruiter_model_best.pkl`
- Latest pointers: `models/latest/ai_score_model.pkl`, `models/latest/recruiter_model.pkl` (best)
- Metrics: see `metrics/*` subfolders
- Plots: see `plots/*` subfolders
- Relocation map: `relocation_map.json`
- Manifest: `manifest.json`

## Notes
- Baseline items retained at root for provenance: `pr_curve.png`, `pr_curve_clean.png`, `reliability_plot_fold*_{before,after}.png`, `confusion_matrix.png`, `confusion_matrix_clean.png`, `metrics_baseline*.txt`.
- Backward compatibility: use `relocation_map.json` for old→new path references.