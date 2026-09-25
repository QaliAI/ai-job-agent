"""Tests for multi-track opportunity discovery and preference parsing."""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from filter_jobs import parse_markdown_preferences
from opportunity_tracks import best_track_for_job, load_opportunity_tracks, search_queries_from_tracks


def test_round_robin_queries_balances_tracks():
    tracks = [
        {"id": "a", "priority": 1, "search_queries": ["A1", "A2", "A3"]},
        {"id": "b", "priority": 2, "search_queries": ["B1", "B2"]},
        {"id": "c", "priority": 3, "search_queries": ["C1"]},
    ]
    assert search_queries_from_tracks(tracks, limit=5) == ["A1", "B1", "C1", "A2", "B2"]


def test_best_track_for_job_prefers_transformation_lane():
    tracks = [
        {
            "id": "ai-transformation",
            "label": "AI Strategy & Transformation",
            "priority": 1,
            "search_queries": ["AI Transformation Consultant"],
            "title_keywords": ["ai transformation", "ai consultant"],
            "positive_signals": ["roadmap", "workflow", "adoption", "roi"],
            "negative_signals": ["research scientist"],
            "preferred_engagements": ["contract"],
        },
        {
            "id": "backend",
            "label": "Backend Engineering",
            "priority": 2,
            "search_queries": ["Backend Engineer"],
            "title_keywords": ["backend"],
            "positive_signals": ["kafka", "go"],
            "negative_signals": [],
            "preferred_engagements": ["full-time"],
        },
    ]

    job = {
        "title": "Senior AI Transformation Consultant",
        "description": "Lead executive roadmap workshops, workflow automation, adoption, and ROI planning.",
        "employment_type": "Contract",
    }

    track, score = best_track_for_job(job, tracks)
    assert track is not None
    assert track["id"] == "ai-transformation"
    assert score >= 70


def test_load_tracks_and_section_aware_preferences():
    with tempfile.TemporaryDirectory() as tmpdir:
        tracks_path = os.path.join(tmpdir, "OPPORTUNITY_TRACKS.json")
        with open(tracks_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "tracks": [
                        {
                            "id": "ai-product",
                            "label": "AI Product",
                            "priority": 1,
                            "search_queries": ["AI Product Builder"],
                        }
                    ]
                },
                f,
            )

        prefs_path = os.path.join(tmpdir, "SEARCH_PREFERENCES.md")
        with open(prefs_path, "w", encoding="utf-8") as f:
            f.write(
                """# Job Search Preferences

## 1. Target Roles & Titles
* **Primary Target Titles**:
  - AI Product Builder
  - AI Solutions Engineer

## 2. Work Arrangement & Location
* **Work Mode Preference**: Remote Only
* **Allowed Locations**:
  - United States (Remote)
  - Dallas, TX, USA

## 5. Industries & Domains
* **Preferred Industries**:
  - SaaS
  - AI

## 6. Hard Exclusions & Blacklist
* **Excluded Companies**:
  - ExampleScamCorp
* **Excluded Keywords in Titles**:
  - "Intern", "Junior"
"""
            )

        tracks = load_opportunity_tracks(tmpdir)
        prefs = parse_markdown_preferences(prefs_path)

        assert tracks[0]["id"] == "ai-product"
        assert prefs["target_titles"] == ["AI Product Builder", "AI Solutions Engineer"]
        assert "Dallas, TX, USA" in prefs["allowed_locations"]
        assert "SaaS" not in prefs["target_titles"]
        assert prefs["excluded_companies"] == ["examplescamcorp"]
        assert prefs["excluded_title_keywords"] == ["intern", "junior"]
