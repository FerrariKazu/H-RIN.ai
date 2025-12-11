# Model Training Verification Guide

This guide summarizes the key outcomes from the model training pipeline using `data/normalized_dataset_v3.csv`.

## Dataset Used
- `data/normalized_dataset_v3.csv` (477 unique records)

## Imbalance Handling Strategy
- The best imbalance handling strategy identified through benchmarking was `class_weights`.
  - Mean PR AUC: 1.0
  - Mean Brier Score: 0.0018

## Winsorization
- Winsorization was not used, as the base numeric features performed as well as or better than the winsorized features.
  - PR AUC (base vs. wins): 1.0000 vs. 1.0000
  - Brier (base vs. wins): 0.0018 vs. 0.0018
  - Decision: Keep base numeric

## Key Metrics (Model B - Recruiter Decision)
- The model achieved excellent performance with a mean PR AUC of 1.0 and a mean Brier score of 0.0018 using the `class_weights` strategy.

## Next Steps
- Review the generated plots in `models/pipeline_v3/` for visual confirmation of model performance and calibration.
- Further analysis can be done on the `ai_score_cv_metrics.json` and `recruiter_cv_metrics.json` for detailed per-fold metrics.