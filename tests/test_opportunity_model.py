"""Tests for consulting/fractional opportunity normalization and person-role targeting."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from opportunity_model import infer_signal_category, normalize_opportunity


def test_growth_signal_targets_revenue_and_marketing_owners():
    raw = {
        "opportunity_type": "buyer_signal",
        "source": "public_web",
        "source_url": "https://example.com/news",
        "company": "Acme",
        "title": "Acme is rebuilding lead routing and CRM automation",
        "description": "The team is focused on HubSpot, speed to lead, pipeline conversion, and RevOps.",
        "signals": ["CRM automation", "lead response"],
        "evidence": ["Company announcement describes a CRM and lead-response initiative."],
    }

    item = normalize_opportunity(raw)
    assert item["signal_category"] == "crm_or_lead_response"
    assert "Chief Revenue Officer" in item["target_person_roles"]
    assert "Chief Marketing Officer" in item["target_person_roles"]
    assert item["source_url"] == "https://example.com/news"


def test_ai_transformation_track_targets_ai_and_operating_leaders():
    tracks = [
        {
            "id": "ai-transformation-enablement",
            "label": "AI Transformation & Enablement",
            "priority": 1,
            "search_queries": ["AI Transformation Consultant"],
            "title_keywords": ["ai transformation"],
            "positive_signals": ["workflow", "adoption", "roadmap"],
            "negative_signals": [],
            "preferred_engagements": ["consulting"],
        }
    ]
    raw = {
        "opportunity_type": "consulting_project",
        "company": "ExampleCo",
        "title": "AI transformation and workflow adoption program",
        "description": "Build the roadmap and improve adoption across business workflows.",
        "engagement_type": "consulting",
        "evidence": ["Public RFP requests an AI transformation roadmap."],
    }

    item = normalize_opportunity(raw, tracks=tracks)
    assert item["opportunity_track"]["id"] == "ai-transformation-enablement"
    assert "Chief AI Officer" in item["target_person_roles"]
    assert "Chief Operating Officer" in item["target_person_roles"]


def test_unknown_opportunity_type_is_rejected():
    raw = {
        "opportunity_type": "made_up_type",
        "company": "Acme",
        "title": "Something",
    }

    try:
        normalize_opportunity(raw)
    except ValueError as exc:
        assert "Unsupported opportunity_type" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
