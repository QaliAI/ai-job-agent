"""End-to-end integration test for AI Job Agent daily workflow."""

import json
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
from daily_workflow import run_daily_pipeline


def test_full_daily_workflow_e2e():
    """Simulates a complete daily run using the Jordan Taylor candidate fixture."""
    fixture_candidate = "examples/jordan-taylor"
    fixture_jobs = "tests/fixtures/sample_jobs.json"
    
    assert os.path.exists(os.path.join(fixture_candidate, "MASTER_PROFILE.md"))
    assert os.path.exists(fixture_jobs)

    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = os.path.join(tmpdir, "output")
        jobs_dir = os.path.join(tmpdir, "jobs")

        result = run_daily_pipeline(
            candidate_dir=fixture_candidate,
            output_dir=out_dir,
            jobs_dir=jobs_dir,
            tailor_top=2,
            mock_input_file=fixture_jobs
        )

        assert result["status"] == "success"
        assert result["total_scanned"] == 3
        # The intern job should have been filtered out by SEARCH_PREFERENCES
        assert result["total_filtered"] == 2
        assert result["top_jobs_count"] == 2
        assert result["tailored_count"] == 2

        # Check generated morning brief
        assert os.path.exists(result["brief_path"])
        with open(result["brief_path"], "r", encoding="utf-8") as f:
            brief_content = f.read()
            assert "Daily Job Search Brief" in brief_content
            assert "Stripe" in brief_content
            assert "Ramp" in brief_content
            assert "Fit Score" in brief_content
            assert "Action Checklist" in brief_content

        # Check generated tailored resumes
        resumes = os.listdir(os.path.join(out_dir, "resumes"))
        assert len(resumes) == 2
        for r_file in resumes:
            r_path = os.path.join(out_dir, "resumes", r_file)
            with open(r_path, "r", encoding="utf-8") as f:
                r_text = f.read()
                assert "Jordan Taylor" in r_text
                assert "PROFESSIONAL SUMMARY" in r_text
                assert "CORE TECHNICAL SKILLS" in r_text

        # Check persistent history ledger
        ledger_path = os.path.join(jobs_dir, "history.json")
        assert os.path.exists(ledger_path)
        with open(ledger_path, "r", encoding="utf-8") as f:
            ledger_data = json.load(f)
            assert "e2e_job_stripe" in ledger_data["jobs"]
            assert "e2e_job_ramp" in ledger_data["jobs"]
