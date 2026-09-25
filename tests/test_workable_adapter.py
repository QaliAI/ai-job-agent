"""Tests for ATS adapters that require source-specific normalization."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

import ats_engine


def test_parse_workable_normalizes_public_widget_payload(monkeypatch):
    payload = {
        "name": "Example AI",
        "jobs": [
            {
                "title": "AI Enablement Engineer",
                "shortcode": "ABC123",
                "url": "https://apply.workable.com/example-ai/j/ABC123/",
                "published_on": "2026-09-24",
                "country": "United States",
                "city": "Dallas",
                "state": "Texas",
                "telecommuting": True,
                "description": "<p>Build AI agents and workflow automation.</p>",
            }
        ],
    }

    monkeypatch.setattr(ats_engine, "fetch_json", lambda url, timeout=15: payload)

    jobs = ats_engine.parse_workable("example-ai", query="AI Enablement")

    assert len(jobs) == 1
    job = jobs[0]
    assert job["source"] == "workable"
    assert job["company"] == "Example AI"
    assert job["title"] == "AI Enablement Engineer"
    assert job["work_mode"] == "remote"
    assert "Dallas" in job["location"]
    assert "Remote" in job["location"]
    assert job["description"] == "Build AI agents and workflow automation."
    assert job["posted_at"] == "2026-09-24"
    assert job["apply_url"].endswith("/ABC123/")


def test_workable_is_registered_in_dispatcher():
    assert ats_engine.ATS_PARSERS["workable"] is ats_engine.parse_workable
