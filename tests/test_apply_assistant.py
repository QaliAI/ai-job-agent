"""Tests for autonomous application assistance kit and Q&A generator."""

import json
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
from apply_assistant import generate_screening_answers, prepare_application_packet


def test_prepare_application_packet_e2e():
    """Verify application packet prepares resume, cover letter, Q&A, and payload JSON."""
    fixture_candidate = "examples/jordan-taylor"
    sample_job = {
        "id": "e2e_job_stripe",
        "company": "Stripe",
        "title": "Senior Backend Engineer, Infrastructure",
        "location": "Remote (US)",
        "work_mode": "remote",
        "salary_min": 190000,
        "salary_max": 230000,
        "currency": "USD",
        "apply_url": "https://boards.greenhouse.io/stripe/jobs/12345",
        "description": "Seeking a Senior Backend Engineer to architect distributed systems using Python, Go, and Redis."
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        res = prepare_application_packet(fixture_candidate, sample_job, output_root=tmpdir)

        assert res["status"] == "ready"
        assert res["qa_status"] == "PASSED"
        assert os.path.exists(res["resume_path"])
        assert os.path.exists(res["cover_path"])
        assert os.path.exists(res["qna_path"])
        assert os.path.exists(res["payload_path"])

        # Inspect Q&A content
        with open(res["qna_path"], "r", encoding="utf-8") as f:
            qna_text = f.read()
            assert "ATS Screening Questions" in qna_text
            assert "Why are you interested in joining Stripe" in qna_text
            assert "Stripe" in qna_text
            assert "$190,000 – $230,000 USD" in qna_text

        # Inspect machine-readable payload
        with open(res["payload_path"], "r", encoding="utf-8") as f:
            payload = json.load(f)
            assert payload["company"] == "Stripe"
            assert payload["title"] == "Senior Backend Engineer, Infrastructure"
            assert len(payload["screening_answers"]) >= 5
            assert payload["claim_qa_passed"] is True
