"""Tests for concurrent ATS crawling and worker pool dispatch."""

import os
import sys
import unittest.mock as mock
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
from ats_engine import fetch_company_jobs, search_ats_postings


def test_search_ats_postings_concurrency():
    """Verify that search_ats_postings dispatches across workers and aggregates results."""
    mock_companies = [
        {"name": "MockCo A", "ats": "greenhouse", "token": "mock-a"},
        {"name": "MockCo B", "ats": "ashby", "token": "mock-b"},
        {"name": "MockCo C", "ats": "lever", "token": "mock-c"}
    ]

    def mock_fetch(comp, query=""):
        return [{
            "id": f"id_{comp['token']}",
            "company": comp["name"],
            "title": f"Engineer at {comp['name']}",
            "location": "Remote",
            "apply_url": "https://example.com"
        }]

    with mock.patch("ats_engine.fetch_company_jobs", side_effect=mock_fetch):
        # Test with 4 workers
        jobs = search_ats_postings(mock_companies, query="Engineer", max_workers=4)
        assert len(jobs) == 3
        companies_found = {j["company"] for j in jobs}
        assert companies_found == {"MockCo A", "MockCo B", "MockCo C"}


def test_search_ats_postings_handles_worker_exceptions():
    """Verify that if one company endpoint throws an exception, other workers succeed."""
    mock_companies = [
        {"name": "GoodCo", "ats": "greenhouse", "token": "good"},
        {"name": "ErrorCo", "ats": "greenhouse", "token": "error"}
    ]

    def mock_fetch_with_error(comp, query=""):
        if comp["token"] == "error":
            raise RuntimeError("Connection timed out")
        return [{"id": "good_id", "company": "GoodCo", "title": "Software Engineer"}]

    with mock.patch("ats_engine.fetch_company_jobs", side_effect=mock_fetch_with_error):
        jobs = search_ats_postings(mock_companies, query="", max_workers=2)
        assert len(jobs) == 1
        assert jobs[0]["company"] == "GoodCo"
