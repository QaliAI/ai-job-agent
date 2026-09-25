"""Tests for persistent job and consulting outcome tracking."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from outcome_ledger import record_outcome, summarize_outcomes


def test_record_and_summarize_outcomes():
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger = os.path.join(tmpdir, "outcomes.json")

        record_outcome(
            ledger,
            "job-1",
            "applied",
            company="Example Co",
            title="AI Enablement Engineer",
            kind="employment",
            track_id="ai-transformation-enablement",
            source="greenhouse",
        )
        record_outcome(
            ledger,
            "job-1",
            "interview",
            track_id="ai-transformation-enablement",
            source="greenhouse",
            note="First interview booked",
        )
        record_outcome(
            ledger,
            "consulting-1",
            "won",
            company="Client Co",
            title="AI workflow implementation",
            kind="consulting_project",
            track_id="fractional-ai-advisory",
            source="referral",
            value=5000,
        )

        summary = summarize_outcomes(ledger)

        assert summary["total_items"] == 2
        assert summary["status_counts"]["interview"] == 1
        assert summary["status_counts"]["won"] == 1
        assert summary["positive_progress_count"] == 2
        assert summary["wins_or_hires"] == 1
        assert summary["known_won_value"] == 5000
        assert summary["by_track"]["ai-transformation-enablement"]["interview"] == 1
