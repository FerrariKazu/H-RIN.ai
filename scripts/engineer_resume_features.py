"""
Engineer resume features from raw text columns to support a two-model ML pipeline.

Overview
- Preprocesses text fields (lowercase, strip HTML, normalize whitespace).
- Extracts skills (`feat_skill_*`), education degrees (`feat_degree_*`, `feat_top_degree_level`),
  job family flags (`feat_job_*`), and certifications (`feat_cert_*`).
- Derives work history and numeric features (promotions, years experience, evidence of metrics,
  numbers count, text length in chars/words, bullet count).
- Optionally builds TF-IDF ngrams and persists feature names.
- Normalizes target to binary Int64 if present for downstream tasks.

Usage
    python scripts/engineer_resume_features.py --path data/data_CLEANED_FIXED.csv --out enriched_dataset.csv

Inputs
- CSV dataset with resume-related text columns (e.g., `resume_text`, `experience_text`, `education_text`, etc.).

Outputs
- A CSV with added `feat_*` columns for skills, certifications, domains, education, and numeric features.
- Optional TF-IDF features and auxiliary artifacts stored under the specified output directory.

Notes
- Feature names align with `pipeline_config.json` and the agent registry for consistency.
- The script avoids leakage by excluding obvious non-feature text aggregations where applicable.
"""
# Standard library imports
import argparse # For argument parsing.
import re # For regular expressions to clean and match textual patterns.
from pathlib import Path # For object-oriented filesystem paths.
from typing import List, Dict, Tuple # For type hints for readability and static tooling.

# Third-party library imports
import numpy as np # For numerical computing library for handling arrays and NaNs.
import pandas as pd # For DataFrame manipulation and feature engineering.


def normalize_target(series: pd.Series) -> pd.Series:
    """Return target as Int64 0/1 with NA preserved."""
    # Create a copy of the series to avoid modifying the original data.
    s = series.copy()
    # If the series contains boolean values, convert them to 0s and 1s.
    if pd.api.types.is_bool_dtype(s):
        return s.replace({True: 1, False: 0}).astype("Int64")

    # If the series contains numeric values, ensure they are binary (0 or 1).
    if pd.api.types.is_numeric_dtype(s):
        s_num = pd.to_numeric(s, errors="coerce")
        # Identify non-binary numeric values.
        invalid = (~s_num.isna()) & (~s_num.isin([0, 1]))
        if invalid.any():
            raise ValueError("Target contains non-binary numeric values.")
        return s_num.astype("Int64")

    # If the series contains string values, map common labels to 0 or 1.
    mapping = {
        "1": 1, "0": 0, "true": 1, "false": 0, "t": 1, "f": 0,
        "yes": 1, "no": 0, "y": 1, "n": 0, "positive": 1, "negative": 0,
    }
    # Normalize string values by stripping whitespace and converting to lowercase.
    s_str = s.astype(str).str.strip().str.lower()
    # Apply the mapping to convert normalized strings to numeric values.
    s_map = s_str.map(mapping)
    # Preserve original missing values by re-applying the NA mask.
    s_map = s_map.where(~series.isna())
    # Cast the resulting series to pandas nullable Int64.
    return s_map.astype("Int64")


# Define a prioritized list of text columns to be used for building a combined text field.
PREFERRED_TEXT_COLS = [
    "resume_text",
    "resume",
    "experience_text",
    "summary",
    "skills_text",
    "education_text",
    "certifications",
    "job_title",
    "current_title",
    "title",
    "work_history",
]


def strip_html(text: str) -> str:
    """
    Removes HTML tags from a given string.

    Args:
        text (str): The input string potentially containing HTML tags.

    Returns:
        str: The string with HTML tags removed, replaced by spaces.
    """
    # Use a regular expression to find and replace HTML tags with a single space.
    return re.sub(r"<[^>]+>", " ", text)


def preprocess_text(s: pd.Series) -> pd.Series:
    """
    Performs a series of text preprocessing steps on a pandas Series.
    Steps include lowercasing, stripping HTML, normalizing whitespace, and removing most punctuation.

    Args:
        s (pd.Series): A pandas Series containing text data.

    Returns:
        pd.Series: A new Series with preprocessed text.
    """
    # Fill any NaN values with empty strings and ensure the Series elements are of string type.
    s = s.fillna("").astype(str)
    # Apply the strip_html function to remove HTML tags from each string in the Series.
    s = s.apply(strip_html)
    # Convert all characters in the Series to lowercase to ensure case-insensitivity.
    s = s.str.lower()
    # Remove punctuation except for '%' and '$' symbols, replacing them with spaces.
    # The regex `[^\w\s%$]` matches any character that is not a word character, whitespace, '%', or '$'.
    s = s.apply(lambda x: re.sub(r"[^\\w\\s%$]", " ", x))
    # Normalize whitespace by replacing multiple spaces with a single space and stripping leading/trailing spaces.
    s = s.apply(lambda x: re.sub(r"\\s+", " ", x).strip())
    return s


def build_text_all(df: pd.DataFrame) -> pd.Series:
    """
    Combines text from preferred columns in a DataFrame into a single Series.
    If preferred columns are not found, it falls back to concatenating all object-type columns.
    The combined text is then preprocessed.

    Args:
        df (pd.DataFrame): The input DataFrame containing text columns.

    Returns:
        pd.Series: A Series containing the preprocessed combined text.
    """
    # Identify which of the PREFERRED_TEXT_COLS are present in the DataFrame.
    cols_present = [c for c in PREFERRED_TEXT_COLS if c in df.columns]
    if not cols_present:
        # If no preferred text columns are found, fall back to all object-type columns.
        obj_cols = [c for c in df.columns if df[c].dtype == object]
        cols_present = obj_cols
    # Prepare a list to hold Series of text parts, ensuring they are strings and NaNs are filled.
    parts = []
    for c in cols_present:
        parts.append(df[c].astype(str).fillna(""))
    # Concatenate all selected text parts into a single combined Series.
    if parts:
        combined = parts[0]
        for p in parts[1:]:
            combined = combined.str.cat(p, sep=" ")
    else:
        # If no text parts were found, create an empty Series with the same index as the DataFrame.
        combined = pd.Series([""] * len(df), index=df.index)
    # Return the combined text after applying preprocessing steps.
    return preprocess_text(combined)

# Robust years-of-experience parser for reusable extraction across pipeline and tests.
def parse_years_experience(t: str) -> float:
    """
    Parses a string to extract years of experience, handling various numeric and date-based formats.

    Args:
        t (str): The input string potentially containing years of experience information.

    Returns:
        float: The maximum extracted years of experience, or NaN if no valid experience is found.
    """
    # Handle non-string inputs by returning NaN immediately.
    if not isinstance(t, str):
        return np.nan
    # Convert the input string to lowercase for case-insensitive matching.
    s = t.lower()
    # Initialize a list to store all successfully extracted numeric values for years of experience.
    vals: List[float] = []
    # Section for numeric forms: "5 years", "5+ years", decimals.
    # Define a list of regex patterns to capture years of experience in various numeric formats.
    for patt in [r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|hrs?|yrs?)\b", r"(\d+(?:\.\d+)?)\s*\+?\s*(?:year|yr)s?\b"]:
        # Find all occurrences of the current pattern in the string.
        for m in re.findall(patt, s, flags=re.IGNORECASE):
            try:
                # Attempt to convert the matched string to a float and add it to the list.
                vals.append(float(m))
            except Exception:
                # Silently ignore any conversion errors to continue processing other matches.
                pass
    # Section for spelled-out numbers.
    # Dictionary mapping common spelled-out numbers to their float equivalents.
    spelled = {
        'one': 1.0, 'two': 2.0, 'three': 3.0, 'four': 4.0, 'five': 5.0,
        'six': 6.0, 'seven': 7.0, 'eight': 8.0, 'nine': 9.0, 'ten': 10.0,
        'eleven': 11.0, 'twelve': 12.0, 'thirteen': 13.0, 'fourteen': 14.0,
        'fifteen': 15.0, 'sixteen': 16.0, 'seventeen': 17.0, 'eighteen': 18.0,
        'nineteen': 19.0, 'twenty': 20.0
    }
    # Iterate through the spelled-out numbers to find matches in the text.
    for w, v in spelled.items():
        # Construct a regex to find the spelled-out number followed by a word indicating years.
        if re.search(rf"\b{w}\b\s*(?:\+)?\s*(?:years?|hrs?|yrs?)\b", s):
            # If a match is found, add its numeric value to the list.
            vals.append(v)
    # Section for date-based experience: "since 2018", "since Jan 2018".
    try:
        # Import datetime for current year calculation within this scope.
        from datetime import datetime
        # Get the current year to calculate experience duration.
        now = datetime.now()
        # Extract years from patterns like "since 2018".
        for ystr in re.findall(r"since\s+(\d{4})", s):
            y = int(ystr)
            # Validate the extracted year and calculate experience, ensuring it's non-negative.
            if 1950 <= y <= now.year:
                vals.append(max(0.0, (now.year - y)))
        # Month mapping for parsing date strings like "Jan".
        month_map = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        # Extract month and year from patterns like "since Jan 2018".
        for m, y in re.findall(r"since\s+([a-z]{3})\s+(\d{4})", s):
            mi = month_map.get(m[:3])
            yi = int(y)
            # Validate month and year, then calculate experience including fractional years.
            if mi and 1950 <= yi <= now.year:
                delta = (now.year - yi) + max(0.0, (now.month - mi) / 12.0)
                vals.append(max(0.0, delta))
    except Exception:
        # Ignore any errors during date parsing to prevent script interruption.
        pass
    # Return the maximum extracted experience, or NaN if no valid experience values were found.
    return max(vals) if vals else np.nan


def add_skill_features(df: pd.DataFrame, text_col: str) -> List[str]:
    # Define a simple catalog of common skills to detect.
    skills = [
        "python",
        "sql",
        "excel",
        "tableau",
        "power bi",
        "project management",
        "machine learning",
        "deep learning",
        "nlp",
        "pandas",
        "numpy",
        "spark",
        "aws",
        "azure",
        "gcp",
        "docker",
        "kubernetes",
        "snowflake",
    ]
    # Track created feature column names.
    created = []
    for sk in skills:
        # Escape special regex characters in the skill string.
        patt = re.escape(sk)
        # word boundary for each term; for phrases allow spaces
        # Convert escaped spaces to whitespace regex and wrap with word boundaries.
        patt = r"\b" + patt.replace("\\ ", r"\s+") + r"\b"
        # Name of the binary feature for this skill.
        col = f"feat_skill_{sk.replace(' ', '_')}"
        # Mark presence of the term in the text column, case-insensitive.
        df[col] = df[text_col].str.contains(patt, case=False, regex=True).astype(int)
        # Record the feature name.
        created.append(col)
    # Aggregate number of matched skills.
    df["feat_num_skills_matched"] = df[created].sum(axis=1)
    created.append("feat_num_skills_matched")
    return created


def add_education_features(df: pd.DataFrame, text_col: str) -> List[str]:
    # Choose source column for education-related text.
    edu_source = text_col
    # If 'education_text' column exists, use it and preprocess.
    if "education_text" in df.columns:
        edu_source = "education_text"
        df[edu_source] = preprocess_text(df[edu_source])
    # Regex patterns to flag degree mentions.
    patterns = {
        "feat_degree_bachelor": r"\b(bachelor|ba|bs|b\.sc|bsc)\b",
        "feat_degree_master": r"\b(master|ms|msc|m\.sc)\b",
        "feat_degree_mba": r"\bmba\b",
        "feat_degree_phd": r"\b(phd|doctorate|dphil)\b",
    }
    # Create binary columns per degree pattern.
    created = []
    for col, patt in patterns.items():
        # Check for degree pattern presence and convert to integer (0 or 1).
        df[col] = df[edu_source].str.contains(patt, case=False, regex=True).astype(int)
        created.append(col)
    # Ordinal highest degree
    # Start with baseline 0 (no degree found).
    df["feat_top_degree_level"] = 0
    # Bachelor -> level 1.
    df.loc[df["feat_degree_bachelor"] == 1, "feat_top_degree_level"] = 1
    # Master or MBA -> level 2.
    df.loc[(df["feat_degree_master"] == 1) | (df["feat_degree_mba"] == 1), "feat_top_degree_level"] = 2
    # PhD -> level 3.
    df.loc[df["feat_degree_phd"] == 1, "feat_top_degree_level"] = 3
    created.append("feat_top_degree_level")
    return created


def add_job_title_features(df: pd.DataFrame, text_col: str) -> List[str]:
    # Determine which column to use for job titles, preferring specific fields.
    title_source = text_col
    # Iterate through preferred job title columns.
    for c in ["job_title", "current_title", "title"]:
        # If a preferred column exists, use it and preprocess its text.
        if c in df.columns:
            title_source = c
            df[title_source] = preprocess_text(df[title_source])
            break
    # Collect created feature names.
    created = []
    # Senior/high titles
    # List of terms indicating senior or high-level positions.
    high_terms = [
        "ceo", "cfo", "coo", "cto", "cio", "cpo", "chief",
        "vp", "vice president", "svp", "evp", "director",
        "head of", "managing director",
    ]
    # Build regex to catch seniority keywords and phrases.
    patt_high = r"(" + "|".join([re.escape(t).replace("\\ ", r"\s+") for t in high_terms]) + r")"
    # Flag presence of senior titles.
    df["feat_high_title"] = df[title_source].str.contains(patt_high, case=False, regex=True).astype(int)
    created.append("feat_high_title")

    # Job family flags
    # Dictionary mapping job family feature names to their regex patterns.
    families: Dict[str, str] = {
        "feat_job_tech": r"\b(engineer|developer|data\s+scientist|analyst|architect|software|devops|ml|ai|cloud)\b",
        "feat_job_sales": r"\b(sales|account\s+executive|business\s+development|inside\s+sales|outside\s+sales|account\s+manager)\b",
        "feat_job_marketing": r"\b(marketing|growth|seo|sem|brand|content|demand\s+generation)\b",
        "feat_job_finance": r"\b(finance|financial|accounting|controller|cfo|treasury|fp&a|audit)\b",
        "feat_job_operations": r"\b(operations|ops|supply\s+chain|logistics)\b",
        "feat_job_hr": r"\b(hr|human\s+resources|recruiter|talent|people\s+ops)\b",
        "feat_job_product": r"\b(product|product\s+manager|product\s+management|pm)\b",
        "feat_job_design": r"\b(design|designer|ux|ui|interaction|graphic)\b",
    }
    # Add binary flags per job family based on title text.
    for col, patt in families.items():
        # Check for job family pattern presence and convert to integer (0 or 1).
        df[col] = df[title_source].str.contains(patt, case=False, regex=True).astype(int)
        created.append(col)
    return created


def add_cert_features(df: pd.DataFrame, text_col: str) -> List[str]:
    # Compact regex dictionary to detect common certifications.
    certs = {
        "feat_cert_aws": r"\b(aws|aws\s+certified|aws\s+certification)\b",
        "feat_cert_pmp": r"\bpmp\b",
        "feat_cert_scrum": r"\bscrum\b",
        "feat_cert_csm": r"\bcsm\b",
        "feat_cert_six_sigma": r"\bsix\s+sigma\b",
        "feat_cert_cfa": r"\bcfa\b",
        "feat_cert_cpa": r"\bcpa\b",
        "feat_cert_azure": r"\bazure\b",
        "feat_cert_gcp": r"\b(gcp|google\s+cloud)\b",
    }
    # Track created binary certification features.
    created = []
    for col, patt in certs.items():
        # Check for certification pattern presence and convert to integer (0 or 1).
        df[col] = df[text_col].str.contains(patt, case=False, regex=True).astype(int)
        created.append(col)
    return created


def add_work_history_and_metrics(df: pd.DataFrame, text_col: str) -> List[str]:
    # Track created numeric and binary features.
    created = []
    # Count mentions of promotions and advancement.
    df["feat_num_promotions"] = df[text_col].str.count(r"\b(promoted|promotion|advanced)\b", flags=re.IGNORECASE)
    created.append("feat_num_promotions")

    # Years of experience extraction: numeric column fallback or robust text parsing
    years_col = None
    # Iterate through potential years of experience column names.
    for c in df.columns:
        lc = c.lower()
        # Check for common years of experience column names.
        if lc in {"years_experience", "experience (years)", "experience_years"}:
            years_col = c
            break
    # If a numeric years of experience column is found, use it.
    if years_col is not None:
        df["feat_years_experience_extracted"] = pd.to_numeric(df[years_col], errors="coerce")
    else:
        # Otherwise, parse years of experience from the text column.
        df["feat_years_experience_extracted"] = df[text_col].apply(parse_years_experience)
    created.append("feat_years_experience_extracted")

    # Evidence of impact/metrics
    # Presence of percent signs often indicates impact metrics.
    has_pct = df[text_col].str.contains(r"%", regex=True)
    # Currency symbols suggest monetary metrics.
    has_currency = df[text_col].str.contains(r"[$€£]", regex=True)
    # Abbreviations k/m/b after numbers imply magnitudes.
    has_km = df[text_col].str.contains(r"\b\d+\s?[kmb]\b", case=False, regex=True)
    # Combine indicators into a single binary flag.
    df["feat_has_metrics"] = (has_pct | has_currency | has_km).astype(int)
    created.append("feat_has_metrics")

    # Count numeric tokens (including decimals and thousands separators).
    df["feat_num_numbers"] = df[text_col].str.findall(r"\d+(?:[\.,]\d+)?(?:,\d{3})*").apply(len)
    created.append("feat_num_numbers")

    # Text size
    # Number of characters in the text.
    df["feat_text_len_chars"] = df[text_col].str.len()
    # Number of whitespace-delimited words.
    df["feat_text_len_words"] = df[text_col].str.split().apply(len)
    # Count bullet-like markers at line starts.
    df["feat_num_bullets"] = df[text_col].str.findall(r"(?:^|\n)\s*[-•]", flags=re.MULTILINE).apply(len)
    created.extend(["feat_text_len_chars", "feat_text_len_words", "feat_num_bullets"])
    return created


def add_tfidf_features(df: pd.DataFrame, text_col: str, out_dir: Path) -> Tuple[List[str], Path]:
    # Import TF-IDF vectorizer lazily to keep dependencies optional.
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
    except Exception:
        # Return empty outputs if scikit-learn is unavailable.
        return [], Path()
    # Configure vectorizer for word and bigram features with basic caps.
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=5, max_features=300)
    # Fit and transform the text into TF-IDF matrix.
    X = vectorizer.fit_transform(df[text_col].fillna(""))
    # Retrieve feature names as strings.
    feature_names = vectorizer.get_feature_names_out()
    # Sanitize feature names into valid column labels.
    tfidf_cols = [f"tfidf_{re.sub(r'[^a-z0-9_]+', '_', n)}" for n in feature_names]
    # Convert sparse matrix to dense DataFrame aligned with df index.
    tfidf_df = pd.DataFrame(X.toarray(), columns=tfidf_cols, index=df.index)
    # Persist TF-IDF features to parquet for reuse.
    tfidf_path = out_dir / "tfidf_features.parquet"
    tfidf_df.to_parquet(tfidf_path, index=False)
    # Join to df (safe at small scale)
    # Attach each TF-IDF column to the main DataFrame.
    for c in tfidf_df.columns:
        df[c] = tfidf_df[c]
    return tfidf_cols, tfidf_path


def compute_prevalence_and_rates(df: pd.DataFrame, target_col: str, feat_cols: List[str]) -> List[str]:
    # Collect human-readable lines summarizing prevalence and positive rates.
    lines = []
    # Normalize target and cast to float for mean computations.
    y = normalize_target(df[target_col]).astype(float)
    # Total number of samples.
    total = len(df)
    for c in feat_cols:
        # Feature values for column c.
        x = df[c]
        # Only consider binary features (0/1 values, ignoring NA).
        if set(pd.unique(x.dropna())) <= {0, 1}:
            # Count positives (1s) and compute prevalence.
            pos = int(x.sum())
            prev = (pos / total) * 100 if total else 0.0
            # Positive rate within 1s and 0s
            # Masks selecting rows where the feature is 1 or 0.
            mask1 = x == 1
            mask0 = x == 0
            # Compute average target rate within each mask.
            rate1 = float(y[mask1].mean() * 100) if mask1.any() else float('nan')
            rate0 = float(y[mask0].mean() * 100) if mask0.any() else float('nan')
            # Append a formatted summary line for this feature.
            lines.append(
                f"{c}: prevalence {prev:.1f}% | AI_High_Performer rate: 1s={rate1:.1f}%, 0s={rate0:.1f}%"
            )
    return lines


def compute_mutual_info(df: pd.DataFrame, target_col: str, feat_cols: List[str]) -> List[Tuple[str, float]]:
    # Compute mutual information scores for features against the target (if sklearn available).
    try:
        from sklearn.feature_selection import mutual_info_classif
    except Exception:
        # Return empty list when unavailable.
        return []
    # Select numeric/binary features
    # Start with a copy of the feature DataFrame.
    X = df[feat_cols].copy()
    for c in feat_cols:
        # Convert object dtype columns to numeric, fill NA with 0.
        if X[c].dtype == object:
            X[c] = pd.to_numeric(X[c], errors="coerce").fillna(0)
    # Normalize target and convert to int (fill NA as 0) for MI computation.
    y = normalize_target(df[target_col]).fillna(0).astype(int)
    # Compute mutual information scores.
    mi = mutual_info_classif(X.values, y.values, random_state=42)
    # Pair feature names with MI scores.
    pairs = list(zip(feat_cols, mi))
    # Sort descending by MI score.
    pairs.sort(key=lambda t: t[1], reverse=True)
    # Return top 20 features.
    return pairs[:20]


def main():
    # Fix the random seed for reproducibility.
    np.random.seed(42)
    # Configure CLI argument parser.
    parser = argparse.ArgumentParser(description="Engineer resume/CV features and report usefulness.")
    # Path to input dataset CSV.
    parser.add_argument("--path", default="data_CLEANED_FIXED.csv", help="Path to dataset CSV.")
    # Output directory for artifacts like enriched datasets and reports.
    parser.add_argument("--out_dir", default=".", help="Output directory for artifacts.")
    # Enable TF-IDF feature generation if scikit-learn is available.
    parser.add_argument("--enable_tfidf", action="store_true", help="Enable optional TF-IDF features (requires scikit-learn).")
    # Enable mutual information ranking if scikit-learn is available.
    parser.add_argument("--enable_mi", action="store_true", help="Enable mutual information ranking (requires scikit-learn).")
    # Parse CLI arguments into a namespace.
    args = parser.parse_args()

    # Create the output directory if it does not exist.
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load the dataset into a DataFrame.
    df = pd.read_csv(args.path)

    # Keep original columns unchanged; add new columns only
    # Build unified text from available resume-related fields.
    text_all = build_text_all(df)
    # Store combined text in a new column.
    df["text_all"] = text_all

    # Create features
    # Accumulate names of all created feature columns.
    created: List[str] = []
    # Add skill presence features.
    created += add_skill_features(df, "text_all")
    # Add education degree features and top-degree level.
    created += add_education_features(df, "text_all")
    # Add job title and job family flags.
    created += add_job_title_features(df, "text_all")
    # Add certification indicators.
    created += add_cert_features(df, "text_all")
    # Add work history and metrics-related features.
    created += add_work_history_and_metrics(df, "text_all")

    # Optional TF-IDF
    # Initialize outputs for optional TF-IDF block.
    tfidf_cols = []
    tfidf_path = Path()
    if args.enable_tfidf:
        # Generate TF-IDF features and add them to df.
        tfidf_cols, tfidf_path = add_tfidf_features(df, "text_all", out_dir)
        created += tfidf_cols

    # Quality checks and quick importance
    # Identify target column and handle case-insensitive variant.
    target_col = "AI_High_Performer"
    if target_col not in df.columns:
        # Case-insensitive fallback
        lower_map = {c.lower(): c for c in df.columns}
        if target_col.lower() in lower_map:
            target_col = lower_map[target_col.lower()]
        else:
            raise KeyError("AI_High_Performer target column not found.")

    # Prevalence and positive rates for binary features
    # Compute per-feature prevalence and class-conditional positive rates.
    prevalence_lines = compute_prevalence_and_rates(df, target_col, created)

    # Mutual information top-20 (optional)
    # Compute MI scores if requested and dependencies are available.
    mi_pairs: List[Tuple[str, float]] = []
    if args.enable_mi:
        mi_pairs = compute_mutual_info(df, target_col, created)

    # Save enriched dataset
    # Path for parquet output.
    enriched_path_parquet = out_dir / "enriched_dataset.parquet"
    # Track whether parquet save succeeded.
    parquet_ok = True
    try:
        df.to_parquet(enriched_path_parquet, index=False)
    except Exception:
        parquet_ok = False
    # Save CSV if small (< ~200MB)
    # Estimate memory footprint to decide whether to also save CSV.
    approx_bytes = int(df.memory_usage(deep=True).sum())
    enriched_path_csv = None
    if approx_bytes < 200 * 1024 * 1024:
        enriched_path_csv = out_dir / "enriched_dataset.csv"
        df.to_csv(enriched_path_csv, index=False)

    # Class imbalance reminder
    # Normalize target and compute basic class distribution.
    y = normalize_target(df[target_col]).astype(float)
    total = len(df)
    pos = int((y == 1).sum())
    neg = int((y == 0).sum())
    pct_pos = (pos / total) * 100 if total else 0.0
    pct_neg = (neg / total) * 100 if total else 0.0

    # Report
    # Build a human-readable report with dataset and feature summaries.
    # Start with an empty list of lines.
    report_lines = []
    # Title line.
    report_lines.append("Feature Engineering Report")
    # Underline separator.
    report_lines.append("--------------------------")
    # Total sample count.
    report_lines.append(f"Total samples: {total:,}")
    # Positive class count and rounded percentage.
    report_lines.append(f"AI_High_Performer (1): {pos:,} ({round(pct_pos)}%)")
    # Negative class count and rounded percentage.
    report_lines.append(f"AI_High_Performer (0): {neg:,} ({round(pct_neg)}%)\n")
    # Section header for created features.
    report_lines.append("Created features (prefix feat_ or tfidf_):")
    # List each feature name prefixed with a dash.
    for c in created:
        report_lines.append(f"- {c}")
    # Section header for prevalence and positive rates per feature.
    report_lines.append("\nPer-feature prevalence and positive rates:")
    # Add precomputed lines for prevalence and rates.
    report_lines.extend(prevalence_lines)
    # Section header for mutual information ranking.
    report_lines.append("\nTop 20 features by mutual information:")
    # Add name and MI score for each selected feature.
    for name, score in mi_pairs:
        report_lines.append(f"- {name}: MI={score:.4f}")
    # If MI was disabled/unavailable, include a note.
    if not mi_pairs:
        report_lines.append("(mutual information ranking disabled or unavailable)")
    # Reminder on class imbalance and mitigation strategies.
    report_lines.append(
        "\nNote: Class imbalance was previously detected; consider stratified splits,"
        " class weights, or resampling in later steps."
    )
    # Note TF-IDF status if no features were generated.
    if not tfidf_cols:
        report_lines.append("\nTF-IDF features not generated (disabled or unavailable).")

    # Save the text report to the output directory.
    # Determine path for the text report and write its contents.
    report_path = out_dir / "feature_engineering_report.txt"
    Path(report_path).write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    # Inform user about saved artifacts.
    # Print status messages for saved artifacts.
    if parquet_ok:
        print(f"Saved enriched dataset (parquet): {enriched_path_parquet.resolve()}")
    else:
        print("Parquet save failed (pyarrow/fastparquet missing). CSV saved if size permits.")
    # If CSV was saved, report its path.
    if enriched_path_csv:
        print(f"Saved enriched dataset (csv): {enriched_path_csv.resolve()}")
    # If TF-IDF features were generated, report their path.
    if tfidf_cols:
        print(f"Saved TF-IDF features: {tfidf_path.resolve()}")
    # Always report where the feature engineering report was saved.
    print(f"Saved report: {report_path.resolve()}")


# Standard script entry-point to allow both import and CLI execution.
if __name__ == "__main__":
    # Run main only when executed as a script.
    main()