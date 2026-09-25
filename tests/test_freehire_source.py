"""Tests for optional FreeHire broad-job source."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

import freehire_source


def test_normalize_freehire_job_preserves_source_boundary():
    raw = {
        "public_slug": "ai-enablement-example-123",
        "source": "greenhouse",
        "external_id": "123",
        "url": "https://boards.example.com/jobs/123",
        "title": "AI Enablement Engineer",
        "company": "Example Co",
        "company_slug": "example-co",
        "location": "Remote",
        "description": "<p>Build AI agents and automation workflows.</p>",
        "skills": ["AI", "Automation"],
        "work_mode": "remote",
        "regions": ["us"],
        "countries": ["US"],
        "cities": [],
        "posted_at": "2026-09-24T00:00:00Z",
        "created_at": "2026-09-24T00:00:00Z",
        "enrichment": {
            "seniority": "senior",
            "category": "ml_ai",
            "employment_type": "full-time",
            "salary_min": 175000,
            "salary_max": 210000,
            "salary_currency": "USD",
        },
    }

    job = freehire_source.normalize_freehire_job(raw)

    assert job["source"] == "freehire"
    assert job["source_type"] == "aggregator_public_api"
    assert job["upstream_source"] == "greenhouse"
    assert job["apply_url"] == "https://boards.example.com/jobs/123"
    assert job["title"] == "AI Enablement Engineer"
    assert job["work_mode"] == "remote"
    assert job["salary_min"] == 175000
    assert job["description"] == "Build AI agents and automation workflows."


def test_search_freehire_builds_filters_and_normalizes(monkeypatch):
    captured = {}

    def fake_fetch(path, timeout=20):
        captured["path"] = path
        return {
            "data": [
                {
                    "public_slug": "one",
                    "source": "lever",
                    "external_id": "one",
                    "url": "https://example.com/jobs/one",
                    "title": "AI Solutions Engineer",
                    "company": "Example",
                    "company_slug": "example",
                    "location": "United States",
                    "description": "Customer-facing AI integration role",
                    "skills": [],
                    "work_mode": "remote",
                    "regions": ["us"],
                    "countries": ["US"],
                    "cities": [],
                    "posted_at": "2026-09-20",
                    "created_at": "2026-09-20",
                    "enrichment": {},
                }
            ]
        }

    monkeypatch.setattr(freehire_source, "fetch_envelope", fake_fetch)

    jobs = freehire_source.search_freehire(
        "AI Solutions Engineer",
        posted_within_days=21,
        country="US",
        work_mode="remote",
        limit=25,
    )

    assert len(jobs) == 1
    assert "posted_within_days=21" in captured["path"]
    assert "countries=US" in captured["path"]
    assert "work_mode=remote" in captured["path"]
