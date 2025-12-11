
# Feature Extraction Updates

## Issues Found
- Years-of-experience extraction was too coarse (integer-only, missed forms like "5+ years", spelled numbers, and "since YEAR").
- Numeric features showed clipping (e.g., decimals ignored) and limited variance in counts for numbers/bullets.
- Certification and skill flags had narrow vocabularies; AWS bias present.
- Recruiter decision label definition needed confirmation across aliases.

## Fixes Applied
- Implemented robust years-of-experience parsing (numeric + spelled-out + date-based) with decimals.
- Counted numeric tokens including decimals and thousands separators; refined bullet detection.
- Expanded skill/cert vocabularies with non-overlapping aliases; enforced strict certification mapping.
- Confirmed recruiter decision mapping: strings {hire, accept, advance, yes, move forward} → 1; {reject, decline, no} → 0.

## Features Dropped or Renamed
- None dropped in the normalized dataset; near-constant features are flagged in the numeric audit for review.
- Column rename previously confirmed: `Recruiter Decision` → `Recruiter_Decision` (values preserved).

## Class Distribution (Post-Fix)
- AI_High_Performer: pos=0 (0.0%), neg=0 (0.0%)
- Recruiter_Decision: pos=0, neg=0

## Notes
- Plots regenerated and overwritten under `plots/normalized/`.
- Numeric features audit saved to `reports/audits/numeric_features_audit.txt`.
