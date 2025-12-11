Purpose
The agent module transforms raw resume text into a structured feature vector for a two-model ML pipeline. It extracts skills and certifications, normalizes them to a canonical vocabulary, infers job domains, and computes numeric features.

How it works
- Skill and certification extraction: Scans text using alias rules.
- Normalization: Uses sentence-transformers embeddings (all-MiniLM-L6-v2) with cosine similarity and RapidFuzz fallback to map phrases to canonical features.
- Job domain inference: Applies keyword rules over text and matched skills.
- Numeric features: Counts years of experience, numbers, bullets, and text lengths.

Key functions (agent/skill_normalization.py)
- extract_skills(text): returns raw skill phrases detected in text.
- extract_certifications(text): returns raw certification phrases.
- normalize_skill(name): canonicalizes a phrase to a feature key via embeddings/fuzzy.
- map_skill_to_feature(name): returns the canonical feature key.
- infer_job_domain(text, skills): returns all domain flags per schema.
- extract_numeric_features(text): returns numeric counts (years, digits, bullets, length).
- build_feature_vector(text): returns a dict with all features set.

Canonical features
- Skills: feat_skill_python, feat_skill_sql, feat_skill_excel, feat_skill_tableau, feat_skill_power_bi, feat_skill_project_management, feat_skill_machine_learning, feat_skill_deep_learning, feat_skill_nlp, feat_skill_pandas, feat_skill_numpy, feat_skill_spark, feat_skill_aws, feat_skill_azure, feat_skill_gcp, feat_skill_docker, feat_skill_kubernetes, feat_skill_snowflake
- Certifications: feat_cert_aws, feat_cert_pmp, feat_cert_scrum, feat_cert_csm, feat_cert_six_sigma, feat_cert_cfa, feat_cert_cpa, feat_cert_azure, feat_cert_gcp
- Job domains: feat_job_tech, feat_job_sales, feat_job_marketing, feat_job_finance, feat_job_operations, feat_job_hr, feat_job_product, feat_job_design
- Numeric features: feat_num_skills_matched, feat_num_certifications, feat_years_experience_extracted, feat_num_numbers, feat_text_len_chars, feat_text_len_words, feat_num_bullets

Usage
Python
from agent import build_feature_vector
text = "Senior Data Scientist with 7 years... Python, SQL, AWS..."
fv = build_feature_vector(text)
print(fv)

Integration
- model_a (regression): consumes numeric features plus skill flags as needed.
- model_b (classification): consumes skill/cert/job-domain flags and numeric features.
- The agent ensures a complete, stable schema: all features are always present with default 0 values when absent.

Extending registry or rules
- Update agent/skill_registry.json to add a new canonical feature key.
- Add aliases in agent/mapping_rules.json for the new key.
- The normalization function will automatically include the new candidates.

Notes
- Embedding model requires sentence-transformers; fuzzy fallback works if unavailable.
- No classification or scoring is performed here—only feature extraction and normalization.