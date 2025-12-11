import re
from datetime import datetime

from agent.skill_normalization import extract_numeric_features
from scripts.engineer_resume_features import parse_years_experience


def test_numeric_forms():
    assert parse_years_experience("5 years of experience") == 5.0
    assert parse_years_experience("7.5 yrs in data science") == 7.5
    assert parse_years_experience("10+ years in engineering") == 10.0


def test_spelled_out_numbers():
    assert parse_years_experience("three years experience") == 3.0
    assert parse_years_experience("Five yrs in analytics") == 5.0


def test_since_year():
    now = datetime.now()
    yrs = parse_years_experience("Experience since 2018")
    assert yrs >= (now.year - 2018) - 0.01
    assert yrs <= (now.year - 2018) + 0.99


def test_since_month_year():
    now = datetime.now()
    yrs = parse_years_experience("Experience since Jan 2020")
    assert yrs >= (now.year - 2020) - 0.01
    assert yrs <= (now.year - 2020) + 1.0  # month delta <= ~1 year


def test_agent_numeric_extraction():
    txt = "Senior Data Scientist with 7 years of experience."
    fv = extract_numeric_features(txt)
    assert abs(fv['feat_years_experience_extracted'] - 7.0) < 1e-6