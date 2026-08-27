"""Tests for persistent ledger and cross-run deduplication."""

import json
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
from jobstore import merge_and_deduplicate, load_store, update_job_status


def test_deduplication_preserves_first_seen_and_flags_new():
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = os.path.join(tmpdir, "history.json")
        
        job_a = {
            "id": "job_001_hash",
            "company": "Stripe",
            "title": "Backend Engineer",
            "location": "Remote",
            "apply_url": "https://stripe.com/jobs/1"
        }
        job_b = {
            "id": "job_002_hash",
            "company": "Ramp",
            "title": "Systems Engineer",
            "location": "Remote",
            "apply_url": "https://ramp.com/jobs/2"
        }

        # Run 1: Both jobs are new
        enriched1, new_jobs1, dupes1 = merge_and_deduplicate([job_a, job_b], store_path)
        assert len(enriched1) == 2
        assert len(new_jobs1) == 2
        assert dupes1 == 0
        assert enriched1[0]["is_new"] is True

        first_seen_a = enriched1[0]["first_seen_at"]

        # Run 2: Job A is seen again alongside Job C
        job_c = {
            "id": "job_003_hash",
            "company": "Linear",
            "title": "Infrastructure Engineer",
            "location": "Remote",
            "apply_url": "https://linear.app/jobs/3"
        }
        enriched2, new_jobs2, dupes2 = merge_and_deduplicate([job_a, job_c], store_path)
        
        assert len(enriched2) == 2
        assert len(new_jobs2) == 1  # Only Job C is new
        assert dupes2 == 1          # Job A is duplicate
        
        # Verify first_seen_at was preserved for Job A
        job_a_run2 = next(j for j in enriched2 if j["id"] == "job_001_hash")
        assert job_a_run2["is_new"] is False
        assert job_a_run2["first_seen_at"] == first_seen_a


def test_update_job_status():
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = os.path.join(tmpdir, "history.json")
        job = {"id": "job_123", "company": "Figma", "title": "Staff Engineer"}
        merge_and_deduplicate([job], store_path)
        
        # Update status to applied
        assert update_job_status("job_123", "applied", store_path) is True
        store = load_store(store_path)
        assert store["jobs"]["job_123"]["user_status"] == "applied"
