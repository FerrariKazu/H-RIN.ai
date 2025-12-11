"""  # Module docstring: purpose and high-level behavior
Resume feature extraction agent: parse raw text and output a canonical
feature vector for the two-model ML pipeline.

Overview
- Loads canonical registries for skills, certifications, and job domains.
- Extracts raw skill/cert phrases using alias rules plus regex-based patterns
  with word-boundaries to prevent false positives (e.g., 'awsome' ≠ 'AWS').
- Normalizes phrases to canonical feature keys using a strict order:
  1) strict keyword (regex, word boundaries), 2) exact alias rules,
  3) embeddings with cosine similarity (SentenceTransformer) only if ≥ 0.78.
- Embedding-based mapping is disabled for certifications to prevent mis-mapping
  (unknown certs will never map to AWS or any other cert).
- Infers job domains using keyword heuristics over text and matched skills.
- Computes numeric features: years of experience, digits count, bullets, text lengths.
- Produces a complete JSON-ready dict with all schema keys present; missing values are 0.

Usage
    from agent import build_feature_vector
    fv = build_feature_vector("Senior Data Scientist... Python, SQL, AWS...")
    # fv is a dict with `feat_skill_*`, `feat_cert_*`, `feat_job_*`, and numeric keys.

Notes
- This module performs feature extraction only; no prediction or classification.
- Embedding model is optional; strict rules ensure safe behavior without it.
"""
import re  # Regular expressions for robust phrase detection
import json  # Load registries and alias rules
from pathlib import Path  # File path utilities
from typing import Dict, List, Tuple  # Type hints for clarity

SIM_THRESHOLD = 0.78  # Embedding similarity threshold; below this no mapping


def _load_json(path: Path):  # Read JSON file from disk
    return json.loads(path.read_text(encoding='utf-8'))


def _get_agent_dir() -> Path:  # Resolve the agent module directory
    return Path(__file__).resolve().parent


def _load_registry():  # Load canonical feature keys for skills/certs/domains
    agent_dir = _get_agent_dir()
    reg = _load_json(agent_dir / 'skill_registry.json')
    skills = reg.get('skills', [])
    certs = reg.get('certifications', [])
    domains = reg.get('job_domains', [])
    return skills, certs, domains


def _load_aliases() -> Dict[str, List[str]]:  # Load alias mapping rules
    agent_dir = _get_agent_dir()
    rules = _load_json(agent_dir / 'mapping_rules.json')
    return rules


_MODEL = None  # Cache for sentence-transformers model


def _get_model():  # Lazy-load embedding model for semantic similarity
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    try:
        from sentence_transformers import SentenceTransformer
        _MODEL = SentenceTransformer('all-MiniLM-L6-v2')
    except Exception:
        _MODEL = None
    return _MODEL


def _cosine(a, b) -> float:  # Cosine similarity with defensive checks
    try:
        import numpy as np
        an = np.linalg.norm(a)
        bn = np.linalg.norm(b)
        if an == 0 or bn == 0:
            return 0.0
        return float(np.dot(a, b) / (an * bn))
    except Exception:
        return 0.0


def _build_candidate_strings(skills: List[str], certs: List[str], aliases: Dict[str, List[str]]) -> List[Tuple[str, str]]:  # Build text→feature pairs
    candidates: List[Tuple[str, str]] = []
    for feat in skills + certs:  # Iterate all features
        disp = feat  # Derive a human-readable name from feature key
        if feat.startswith('feat_skill_'):
            disp = feat.replace('feat_skill_', '').replace('_', ' ')
        elif feat.startswith('feat_cert_'):
            disp = feat.replace('feat_cert_', '').replace('_', ' ')
        candidates.append((disp, feat))  # Include display name
        for alias in aliases.get(feat, []):  # Include each alias phrase
            candidates.append((alias, feat))
    return candidates


def extract_skills(text: str) -> List[str]:  # Detect skill phrases with word-boundary safety
    skills, certs, _ = _load_registry()  # Canonical registries
    aliases = _load_aliases()  # Alias rules
    t = text  # Keep original case for some patterns
    tl = text.lower()  # Lowercase for normalized scans
    found = set()  # Unique phrases

    # Build regex patterns with word boundaries for each alias under skill features
    for feat in skills:
        for alias in aliases.get(feat, []):
            # word-boundary anchored pattern, escape special characters
            pat = re.compile(rf"\b{re.escape(alias)}\b", flags=re.IGNORECASE)
            if pat.search(t):
                found.add(alias)

    # Detect common libraries and capitalized tools (fallback if aliases miss)
    lib_patterns = [
        r"\bPandas\b", r"\bNumPy\b", r"\bSciPy\b", r"\bSeaborn\b",
        r"\bTensorFlow\b", r"\bKeras\b", r"\bPyTorch\b", r"\bscikit\-learn\b",
        r"\bDocker\b", r"\bKubernetes\b", r"\bSpark\b", r"\bSnowflake\b",
        r"\bSQL\b", r"\bPython\b"
    ]
    for pat_s in lib_patterns:
        pat = re.compile(pat_s, flags=re.IGNORECASE)
        m = pat.search(t)
        if m:
            found.add(m.group(0))

    # Avoid false positives like 'awsome' triggering AWS via word-boundaries
    # Nothing more needed here because patterns use \b boundaries.

    return sorted(found)


def extract_certifications(text: str) -> List[str]:  # Robust certification extractor (regex + keywords)
    # Build explicit patterns for each certification to avoid mis-mapping
    patterns = {
        # AWS: Cloud Practitioner, Solutions Architect (Associate/Professional), Developer, SysOps
        'feat_cert_aws': [
            r"\bAWS\b",
            r"\bAmazon\s+Web\s+Services\b",
            r"\bAWS\s+Certified\b",
            r"\bCloud\s+Practitioner\b",
            r"\bSolutions?\s+Architect\b",
            r"\bDeveloper\s+Associate\b",
            r"\bSysOps\s+Administrator\b",
        ],
        # PMP: Project Management Professional
        'feat_cert_pmp': [
            r"\bPMP\b",
            r"\bProject\s+Management\s+Professional\b",
            r"\bPMI\s*\-?\s*PMP\b",
        ],
        # Scrum (generic) and CSM (Scrum Alliance)
        'feat_cert_scrum': [
            r"\bScrum\b",
            r"\bProfessional\s+Scrum\s+Master\b",
            r"\bPSM\b",
            r"\bScrum\.org\b",
        ],
        'feat_cert_csm': [
            r"\bCSM\b",
            r"\bCertified\s+Scrum\s+Master\b",
            r"\bScrum\s+Alliance\b",
        ],
        # Six Sigma / Lean Six Sigma
        'feat_cert_six_sigma': [
            r"\bSix\s+Sigma\b",
            r"\bLean\s+Six\s+Sigma\b",
            r"\bBlack\s+Belt\b",
            r"\bGreen\s+Belt\b",
        ],
        # Finance certs
        'feat_cert_cfa': [
            r"\bCFA\b",
            r"\bChartered\s+Financial\s+Analyst\b",
            r"\bCFA\s+Institute\b",
        ],
        'feat_cert_cpa': [
            r"\bCPA\b",
            r"\bCertified\s+Public\s+Accountant\b",
            r"\bAICPA\b",
        ],
        # Azure certifications with codes
        'feat_cert_azure': [
            r"\bAzure\b",
            r"\bMicrosoft\s+Certified\b",
            r"\bAZ\-?\s*900\b",
            r"\bAZ\-?\s*204\b",
            r"\bDP\-?\s*100\b",
            r"\bDP\-?\s*203\b",
            r"\bAzure\s+Administrator\b",
            r"\bAzure\s+Fundamentals\b",
        ],
        # GCP certifications and titles
        'feat_cert_gcp': [
            r"\bGCP\b",
            r"\bGoogle\s+Cloud\b",
            r"\bGoogle\s+Cloud\s+Certified\b",
            r"\bProfessional\s+Cloud\s+Engineer\b",
            r"\bAssociate\s+Cloud\s+Engineer\b",
            r"\bProfessional\s+Data\s+Engineer\b",
        ],
    }

    found_feats = set()  # Canonical cert feature keys detected
    for feat, pats in patterns.items():  # Iterate over each cert category
        for pat_s in pats:
            pat = re.compile(pat_s, flags=re.IGNORECASE)
            if pat.search(text):  # If any pattern matches
                found_feats.add(feat)
                break  # Move to next cert category to avoid duplicates

    # Convert canonical feature keys to representative phrases to pass through normalize
    # (normalize_skill will return these canonical keys directly via alias/equality matches)
    return sorted([f.replace('feat_cert_', '').replace('_', ' ') for f in found_feats])


def normalize_skill(name: str) -> str:  # Canonicalize phrase to feature key with safe order/thresholds
    skills, certs, _ = _load_registry()  # Canonical feature keys
    aliases = _load_aliases()  # Alias rules
    q = name.strip()  # Clean input phrase
    if not q:
        return ''  # Empty input yields no mapping

    ql = q.lower()  # Lowercase for matching

    # 1) Strict keyword: check for exact display name matches with word boundaries
    # Build display names for skills/certs
    display_map: Dict[str, str] = {}
    for feat in skills + certs:
        disp = feat
        if feat.startswith('feat_skill_'):
            disp = feat.replace('feat_skill_', '').replace('_', ' ')
        elif feat.startswith('feat_cert_'):
            disp = feat.replace('feat_cert_', '').replace('_', ' ')
        display_map[disp.lower()] = feat
    if ql in display_map:
        return display_map[ql]

    # 2) Exact alias rules: if phrase equals any alias (case-insensitive), map directly
    for feat, alias_list in aliases.items():
        for alias in alias_list:
            if ql == alias.lower():
                return feat

    # Determine if the phrase looks like a certification; if so, DO NOT use embeddings
    looks_like_cert = bool(re.search(r"\b(cert|certified|pmp|csm|psm|six\s+sigma|cfa|cpa|az\-?\d+|dp\-?\d+|associate\s+cloud|professional\s+cloud)\b", q, flags=re.IGNORECASE))
    if looks_like_cert:
        # Certification mapping is intentionally strict: no embeddings/fuzzy
        return ''  # If not matched by strict/alias, treat as unknown cert => no mapping

    # 3) Embeddings with threshold, restricted to skill mappings and guarded for AWS
    candidates = _build_candidate_strings(skills, [], aliases)  # Only skill candidates to avoid cert mis-mapping
    model = _get_model()  # Load semantic model if available
    best_feat = ''  # Track best feature
    best_sim = 0.0  # Track best similarity
    if model is not None:
        try:
            q_emb = model.encode([q])[0]  # Encode query
            cand_texts = [c[0] for c in candidates]  # Candidate texts
            cand_embs = model.encode(cand_texts)  # Encode candidates
            for (cand_text, feat), emb in zip(candidates, cand_embs):  # Iterate
                sim = _cosine(q_emb, emb)  # Cosine similarity
                if sim > best_sim:
                    # Guard: do not map to AWS skill unless explicit 'aws' present
                    if feat == 'feat_skill_aws' and not re.search(r"\baws\b|\bamazon\s+web\s+services\b", q, flags=re.IGNORECASE):
                        continue
                    best_sim = sim
                    best_feat = feat
            if best_sim >= SIM_THRESHOLD:  # Enforce strict threshold 0.78
                return best_feat
        except Exception:
            pass  # If embeddings unavailable, skip

    # Fuzzy exacts as a last resort (safe equality only)
    for disp_lower, feat in display_map.items():
        if ql == disp_lower:
            return feat

    return ''  # No mapping


def map_skill_to_feature(canonical_feat: str) -> str:  # Identity mapping for canonical feature keys
    # canonical_feat is already a feature key like 'feat_skill_python' or 'feat_cert_aws'
    return canonical_feat


def infer_job_domain(text: str, skills: List[str]) -> Dict[str, int]:  # Infer job domain flags
    domains = {
        'feat_job_tech': 0,
        'feat_job_sales': 0,
        'feat_job_marketing': 0,
        'feat_job_finance': 0,
        'feat_job_operations': 0,
        'feat_job_hr': 0,
        'feat_job_product': 0,
        'feat_job_design': 0,
    }
    t = text.lower()  # Lowercase for term checks
    # Tech: include common frameworks and dev terms
    tech_terms = ['react', 'node', 'django', 'flask', 'api', 'devops', 'backend', 'frontend', 'full stack', 'software engineer']
    if any(term in t for term in tech_terms) or any(s.startswith('feat_skill_') for s in skills):
        domains['feat_job_tech'] = 1
    # Sales
    sales_terms = ['crm', 'salesforce', 'pipeline', 'quota', 'account executive', 'bd', 'business development']
    if any(term in t for term in sales_terms):
        domains['feat_job_sales'] = 1
    # Marketing
    marketing_terms = ['seo', 'sem', 'content marketing', 'campaign', 'google ads', 'social media']
    if any(term in t for term in marketing_terms):
        domains['feat_job_marketing'] = 1
    # Finance
    finance_terms = ['financial modeling', 'budgeting', 'cfa', 'cpa', 'audit', 'valuation', 'excel modeling']
    if any(term in t for term in finance_terms):
        domains['feat_job_finance'] = 1
    # Operations
    ops_terms = ['operations', 'supply chain', 'logistics', 'process improvement', 'six sigma']
    if any(term in t for term in ops_terms):
        domains['feat_job_operations'] = 1
    # HR
    hr_terms = ['recruiting', 'talent acquisition', 'hr', 'human resources', 'onboarding']
    if any(term in t for term in hr_terms):
        domains['feat_job_hr'] = 1
    # Product
    product_terms = ['product manager', 'roadmap', 'feature prioritization', 'user stories', 'backlog']
    if any(term in t for term in product_terms):
        domains['feat_job_product'] = 1
    # Design
    design_terms = ['adobe', 'illustrator', 'photoshop', 'figma', 'ux', 'ui', 'wireframe']
    if any(term in t for term in design_terms):
        domains['feat_job_design'] = 1
    return domains


def extract_numeric_features(text: str) -> Dict[str, int]:  # Compute numeric features from text
    # Basic counts
    words = re.findall(r"\b\w+\b", text)
    chars = len(text)
    digits = re.findall(r"\d", text)
    bullets = sum(1 for line in text.splitlines() if re.match(r"^\s*[\-\*•]", line))

    # Robust years-of-experience extraction
    t = text.lower()
    years: float = 0.0

    # 1) Numeric forms: "5 years", "5+ years", "7 yrs", allow decimals
    num_patterns = [
        r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\b",
        r"(\d+(?:\.\d+)?)\s*\+?\s*\-?\s*(?:year|yr)s?\b",
    ]
    num_vals: list[float] = []
    for patt in num_patterns:
        matches = re.findall(patt, t, flags=re.IGNORECASE)
        num_vals.extend([float(m) for m in matches])

    # 2) Spelled-out numbers: "three years", "five yrs"
    spelled_map = {
        'one': 1.0, 'two': 2.0, 'three': 3.0, 'four': 4.0, 'five': 5.0,
        'six': 6.0, 'seven': 7.0, 'eight': 8.0, 'nine': 9.0, 'ten': 10.0,
        'eleven': 11.0, 'twelve': 12.0, 'thirteen': 13.0, 'fourteen': 14.0,
        'fifteen': 15.0, 'sixteen': 16.0, 'seventeen': 17.0, 'eighteen': 18.0,
        'nineteen': 19.0, 'twenty': 20.0
    }
    for word, val in spelled_map.items():
        if re.search(rf"\b{word}\b\s*(?:\+)?\s*(?:years?|yrs?)\b", t):
            num_vals.append(val)

    # 3) Date-based forms: "since 2018", "since Jan 2018"
    # Compute from current year; month granularity optional
    try:
        from datetime import datetime
        now = datetime.now()
        # Year-only
        for ystr in re.findall(r"since\s+(\d{4})", t):
            y = int(ystr)
            if 1950 <= y <= now.year:
                num_vals.append(max(0.0, (now.year - y)))
        # Month and year
        month_map = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        for m, y in re.findall(r"since\s+([a-z]{3})\s+(\d{4})", t):
            m_i = month_map.get(m[:3])
            y_i = int(y)
            if m_i and 1950 <= y_i <= now.year:
                delta_years = (now.year - y_i) + max(0.0, (now.month - m_i) / 12.0)
                num_vals.append(max(0.0, delta_years))
    except Exception:
        # If datetime fails, ignore date-based extraction
        pass

    # Choose the maximum plausible value to reflect total experience
    if num_vals:
        years = max(num_vals)

    return {
        'feat_num_skills_matched': 0,  # placeholder; set later
        'feat_num_certifications': 0,  # placeholder; set later
        'feat_years_experience_extracted': years,
        'feat_num_numbers': len(digits),
        'feat_text_len_chars': chars,
        'feat_text_len_words': len(words),
        'feat_num_bullets': bullets,
    }


def _empty_feature_vector() -> Dict[str, int]:  # Initialize complete feature vector with zeros
    skills, certs, domains = _load_registry()  # Load canonical keys
    fv: Dict[str, int] = {}  # Output dict
    for k in skills:  # Skill flags
        fv[k] = 0
    for k in certs:  # Certification flags
        fv[k] = 0
    for k in domains:  # Job domain flags
        fv[k] = 0
    # Numeric features placeholders
    fv.update({
        'feat_num_skills_matched': 0,
        'feat_num_certifications': 0,
        'feat_years_experience_extracted': 0,
        'feat_num_numbers': 0,
        'feat_text_len_chars': 0,
        'feat_text_len_words': 0,
        'feat_num_bullets': 0,
    })
    return fv


def build_feature_vector(text: str) -> Dict[str, int]:  # Main entry: produce canonical feature vector
    fv = _empty_feature_vector()  # Initialize all flags and numeric placeholders

    raw_skills = extract_skills(text)  # Detect skill phrases
    raw_certs = extract_certifications(text)  # Detect certification phrases

    normalized_feats = set()  # Accumulate canonical feature keys
    for s in raw_skills:  # Normalize each skill phrase
        feat = normalize_skill(s)
        if feat:
            normalized_feats.add(map_skill_to_feature(feat))
    for c in raw_certs:  # Normalize each certification phrase (strict rules)
        feat = normalize_skill(c)
        if feat:
            normalized_feats.add(map_skill_to_feature(feat))

    skill_feats = [f for f in normalized_feats if f.startswith('feat_skill_')]  # Skills only
    cert_feats = [f for f in normalized_feats if f.startswith('feat_cert_')]  # Certs only

    for f in skill_feats:  # Activate skill flags
        fv[f] = 1
    for f in cert_feats:  # Activate certification flags
        fv[f] = 1

    domains = infer_job_domain(text, list(normalized_feats))  # Infer domains from text/skills
    fv.update(domains)  # Merge domain flags

    nums = extract_numeric_features(text)  # Compute numeric features
    fv.update(nums)  # Merge numeric values
    fv['feat_num_skills_matched'] = len(skill_feats)  # Count skills
    fv['feat_num_certifications'] = len(cert_feats)  # Count certs

    return fv  # Final feature vector


if __name__ == '__main__':  # Simple manual test for local debugging
    sample = """
    Senior Data Scientist with 7 years of experience. Python, SQL, Pandas, NumPy, TensorFlow.
    AWS Certified Solutions Architect. Built APIs and DevOps pipelines; product roadmap collaboration.
    • Led ML model training and deployment
    - Managed backlog and user stories
    """
    vec = build_feature_vector(sample)  # Build features for sample text
    print(json.dumps(vec, indent=2))  # Pretty-print output JSON
    # Notes:
    # - Extend this with more realistic samples and unit tests as needed.