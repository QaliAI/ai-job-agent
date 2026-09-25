"""Tests for HTML morning brief rendering and email dispatcher."""

import json
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
from email_notifier import render_html_brief, send_email_brief


def test_render_html_brief():
    """Verify that HTML morning brief compiles cleanly with job stats and badges."""
    sample_jobs = [
        {
            "id": "job_abc",
            "company": "Figma",
            "title": "Staff Product Designer",
            "location": "San Francisco, CA",
            "work_mode": "hybrid",
            "salary_min": 210000,
            "salary_max": 250000,
            "currency": "USD",
            "source": "greenhouse",
            "fit_score": 92,
            "fit_evaluation": {
                "score": 92,
                "confidence": "High",
                "recommendation": "APPLY",
                "strengths": ["Design systems leadership", "High-fidelity prototyping"],
                "material_gaps": []
            },
            "apply_url": "https://boards.greenhouse.io/figma/jobs/123"
        }
    ]
    profile = {
        "name": "Maya Lin",
        "title": "Product Designer",
        "location": "San Francisco, CA",
        "work_mode_pref": "Hybrid"
    }

    html_out = render_html_brief(
        sample_jobs,
        profile,
        total_scanned=45,
        total_filtered=12,
        tailored_files={"job_abc": "output/resumes/maya_figma.md"}
    )

    assert "<!DOCTYPE html>" in html_out
    assert "Maya Lin" in html_out
    assert "Staff Product Designer" in html_out
    assert "Figma" in html_out
    assert "92/100" in html_out
    assert "APPLY" in html_out
    assert "$210,000 – $250,000 USD" in html_out
    assert "Design systems leadership" in html_out
    assert "View & Apply on Employer Site" in html_out
    assert "maya_figma.md" in html_out


def test_send_email_brief_preview_fallback():
    """Verify that send_email_brief falls back to local HTML preview when no SMTP credentials are set."""
    with tempfile.TemporaryDirectory() as tmpdir:
        preview_path = os.path.join(tmpdir, "test_preview.html")
        sample_html = "<html><body><h1>Job Brief</h1></body></html>"

        res = send_email_brief(
            sample_html,
            subject="Test Job Brief",
            preview_path=preview_path
        )

        assert res["status"] == "preview_saved"
        assert res["channel"] == "file"
        assert os.path.exists(preview_path)
        with open(preview_path, "r", encoding="utf-8") as f:
            assert f.read() == sample_html
