"""Tests for transparent rubric scoring engine."""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
from scorer import score_single_job, score_job_list


def test_rubric_scoring_high_match():
    profile = {
        "title": "Senior Backend Engineer",
        "target_titles": ["Senior Backend Engineer", "Distributed Systems Engineer"],
        "years_exp": 7,
        "work_mode_pref": "remote",
        "proven_skills": ["Python", "Go", "PostgreSQL", "Redis", "Kafka", "AWS", "Docker"],
        "transferable_skills": ["TypeScript", "Rust"],
        "domain_expertise": ["Cloud Infrastructure", "High-Throughput Ingestion"]
    }

    job_high_match = {
        "title": "Senior Backend Engineer, Distributed Systems",
        "description": "We are seeking a Senior Backend Engineer with 5+ years of experience in Python and Go to build high-throughput ingestion pipelines using Kafka, Redis, and PostgreSQL on AWS. Remote US.",
        "location": "Remote - US",
        "work_mode": "remote"
    }

    score_result = score_single_job(job_high_match, profile)
    
    assert score_result["score"] >= 80, f"Expected score >= 80, got {score_result['score']}"
    assert score_result["recommendation"] == "APPLY"
    assert score_result["confidence"] == "High"
    assert "Python" in score_result["proven_matches"]
    assert "Go" in score_result["proven_matches"]


def test_rubric_scoring_low_match():
    profile = {
        "title": "Senior Backend Engineer",
        "target_titles": ["Senior Backend Engineer"],
        "years_exp": 7,
        "work_mode_pref": "remote",
        "proven_skills": ["Python", "Go", "PostgreSQL"],
        "transferable_skills": [],
        "domain_expertise": []
    }

    job_low_match = {
        "title": "Lead iOS Mobile Engineer (Swift & SwiftUI)",
        "description": "Must have 8+ years developing native iOS mobile applications in Swift, SwiftUI, Objective-C, and CocoaPods.",
        "location": "New York, NY",
        "work_mode": "onsite"
    }

    score_result = score_single_job(job_low_match, profile)
    assert score_result["score"] < 65
    assert score_result["recommendation"] == "SKIP"
