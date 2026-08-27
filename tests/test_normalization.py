"""Tests for job normalization, HTML stripping, salary extraction, and work mode inference."""

import pytest
import sys
import os

# Add scripts directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from ats_engine import clean_html, extract_salary, generate_job_id, infer_work_mode


def test_clean_html_strips_tags_and_decodes_entities():
    raw = "<p>We are hiring a <strong>Senior Backend Engineer</strong> &amp; leader.&nbsp;<br/>Apply now!</p>"
    cleaned = clean_html(raw)
    assert "<p>" not in cleaned
    assert "<strong>" not in cleaned
    assert "&amp;" not in cleaned
    assert "Senior Backend Engineer & leader." in cleaned
    assert "Apply now!" in cleaned


def test_extract_salary_various_formats():
    # Format: $150,000 - $190,000
    text1 = "The expected base salary range for this role is $150,000 - $190,000 USD per year."
    s_min, s_max, curr = extract_salary(text1)
    assert s_min == 150000.0
    assert s_max == 190000.0
    assert curr == "USD"

    # Format: $140k - $180k
    text2 = "Compensation: $140k – $180k plus equity."
    s_min, s_max, curr = extract_salary(text2)
    assert s_min == 140000.0
    assert s_max == 180000.0
    assert curr == "USD"

    # Format: €90,000 to €120,000
    text3 = "Salary range €90,000 to €120,000 gross annual."
    s_min, s_max, curr = extract_salary(text3)
    assert s_min == 90000.0
    assert s_max == 120000.0
    assert curr == "EUR"


def test_infer_work_mode():
    assert infer_work_mode("Backend Engineer", "Remote - US", "Work from anywhere") == "remote"
    assert infer_work_mode("Software Engineer", "New York, NY", "Hybrid schedule 2 days in office") == "hybrid"
    assert infer_work_mode("Systems Engineer", "Austin, TX", "Must be onsite in our Austin headquarters") == "onsite"


def test_deterministic_job_id():
    id1 = generate_job_id("greenhouse", "stripe", "Senior Backend Engineer", "Remote")
    id2 = generate_job_id("greenhouse", "stripe", "Senior Backend Engineer", "Remote")
    id3 = generate_job_id("lever", "stripe", "Senior Backend Engineer", "Remote")
    
    assert id1 == id2, "Job IDs must be deterministic for identical inputs"
    assert id1 != id3, "Job IDs from different sources must differ"
    assert len(id1) == 16, "Job ID should be 16-character hex hash"
