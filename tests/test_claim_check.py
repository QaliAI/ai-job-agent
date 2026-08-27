"""Tests for Claim Check QA anti-fabrication validator."""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
from claim_check import verify_content


def test_claim_check_passes_truthful_content():
    truth = {
        "raw_text": "Jordan Taylor. Senior Backend Engineer with experience in Python, Go, PostgreSQL, Redis, Kafka. Scaled to 35,000 tasks/min. Decreased query latency by 48%.",
        "proven_skills": {"Python", "Go", "PostgreSQL", "Redis", "Kafka", "Docker", "AWS"},
        "transferable_skills": {"TypeScript"},
        "all_skills_lower": {"python", "go", "postgresql", "redis", "kafka", "docker", "aws", "typescript"},
        "verified_metrics": {"35,000", "48%", "99.99%"},
        "companies": {"apex cloud systems", "beacon analytics"},
        "degrees": {"b.s. in computer engineering"},
        "achievements_text": "Scaled to 35,000 tasks/min with zero dropped jobs. Decreased latency by 48%."
    }

    truthful_resume = """
# Jordan Taylor
Senior Backend Engineer · Python, Go, PostgreSQL, Redis

## Experience
* Architected background processing in Go & Redis handling 35,000 tasks/min with zero dropped jobs.
* Decreased average query latency by 48% across database clusters.
"""

    report = verify_content(truthful_resume, truth)
    assert report["passed"] is True
    assert report["status"] == "PASSED"
    assert len(report["violations"]) == 0


def test_claim_check_flags_hallucinated_skill():
    truth = {
        "raw_text": "Candidate with Python and SQL experience.",
        "proven_skills": {"Python", "SQL"},
        "transferable_skills": set(),
        "all_skills_lower": {"python", "sql"},
        "verified_metrics": set(),
        "companies": set(),
        "degrees": set(),
        "achievements_text": ""
    }

    # Draft claims Rust and Solidity which are NOT in candidate truth
    fabricated_resume = """
# Draft Candidate
* Built smart contracts using Solidity and high-frequency backend in Rust.
"""

    report = verify_content(fabricated_resume, truth)
    assert report["passed"] is False
    assert report["status"] == "FAILED"
    
    violation_skills = [v["skill"] for v in report["violations"] if v["type"] == "unsupported_skill"]
    assert "solidity" in violation_skills or "rust" in violation_skills


def test_claim_check_flags_unverified_metric():
    truth = {
        "raw_text": "Jordan Taylor with verified metrics: 48% latency reduction.",
        "proven_skills": {"Python", "SQL"},
        "transferable_skills": set(),
        "all_skills_lower": {"python", "sql"},
        "verified_metrics": {"48%"},
        "companies": set(),
        "degrees": set(),
        "achievements_text": "Decreased latency by 48%."
    }

    # Draft exaggerates to $50,000,000 and 800%
    inflated_resume = """
# Draft Candidate
* Generated $50,000,000 in new revenue and improved efficiency by 800%.
"""

    report = verify_content(inflated_resume, truth)
    assert report["passed"] is False
    assert any(v["type"] == "unverified_metric" for v in report["violations"])
