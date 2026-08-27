"""Tests for hard exclusion filtering engine."""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
from filter_jobs import evaluate_exclusion, filter_job_list


def test_filter_drops_blacklisted_company():
    prefs = {"excluded_companies": ["spamcorp", "revokedvendor"]}
    
    job_bad = {"company": "SpamCorp", "title": "Senior Engineer", "location": "Remote"}
    job_good = {"company": "Stripe", "title": "Senior Engineer", "location": "Remote"}
    
    is_exc, reason = evaluate_exclusion(job_bad, prefs)
    assert is_exc is True
    assert "Excluded company" in reason

    is_exc2, _ = evaluate_exclusion(job_good, prefs)
    assert is_exc2 is False


def test_filter_drops_excluded_title_keywords():
    prefs = {"excluded_title_keywords": ["junior", "intern"]}
    
    job_intern = {"company": "Google", "title": "Software Engineer Intern", "location": "Remote"}
    job_senior = {"company": "Google", "title": "Senior Software Engineer", "location": "Remote"}
    
    is_exc, reason = evaluate_exclusion(job_intern, prefs)
    assert is_exc is True
    assert "Excluded title keyword" in reason

    is_exc2, _ = evaluate_exclusion(job_senior, prefs)
    assert is_exc2 is False


def test_filter_drops_below_minimum_salary():
    prefs = {"min_salary": 160000.0}
    
    job_low_pay = {"company": "Acme", "title": "Dev", "salary_min": 100000.0, "salary_max": 120000.0}
    job_high_pay = {"company": "Acme", "title": "Dev", "salary_min": 170000.0, "salary_max": 210000.0}
    job_undisclosed = {"company": "Acme", "title": "Dev", "salary_min": None, "salary_max": None}
    
    is_exc1, reason1 = evaluate_exclusion(job_low_pay, prefs)
    assert is_exc1 is True
    assert "below candidate minimum threshold" in reason1

    is_exc2, _ = evaluate_exclusion(job_high_pay, prefs)
    assert is_exc2 is False

    is_exc3, _ = evaluate_exclusion(job_undisclosed, prefs)
    assert is_exc3 is False  # Keep undisclosed jobs by default


def test_filter_drops_incompatible_onsite_work_mode():
    prefs = {"work_mode": "remote", "allowed_locations": ["Austin, TX"]}
    
    job_onsite_foreign = {"company": "Acme", "title": "Dev", "work_mode": "onsite", "location": "Berlin, Germany"}
    job_remote = {"company": "Acme", "title": "Dev", "work_mode": "remote", "location": "Remote"}
    
    is_exc1, reason1 = evaluate_exclusion(job_onsite_foreign, prefs)
    assert is_exc1 is True
    assert "Remote required" in reason1

    is_exc2, _ = evaluate_exclusion(job_remote, prefs)
    assert is_exc2 is False
