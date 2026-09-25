"""Personal job-agent package: profiles, truthfulness, scoring, lifecycle, digest."""

import json
import os
import shutil
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from claim_check import load_candidate_ground_truth, verify_content
from digest_report import format_digest
from job_agent import run_profile
from jobstore import load_store, merge_and_deduplicate, set_lifecycle
from profile_config import preflight, resolve_profile_dir, validate_profile_name
from scorer import score_job_list, score_single_job
from truth_guard import check_truthfulness


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SAMPLE = os.path.join(ROOT, "examples", "sample-client")


def test_score_explains_fit_gap_salary_and_priority():
    profile = {
        "title": "Customer Operations Lead",
        "target_titles": ["Customer Operations Lead"],
        "years_exp": 7,
        "work_mode_pref": "remote",
        "proven_skills": ["Zendesk", "SQL"],
        "transferable_skills": [],
        "domain_expertise": ["Customer Operations"],
        "salary_expectation": {"min": 90000},
        "locations": ["Remote - US"],
        "location": "Remote - US",
    }
    hidden_pay = {
        "title": "Support Operations Manager",
        "company": "Harbor Museum",
        "description": "Required: SQL and Salesforce administration.",
        "location": "Remote - US",
        "work_mode": "remote",
    }
    result = score_single_job(hidden_pay, profile)
    explanation = result["explanation"]
    assert explanation["application_priority"] in {"APPLY", "CONSIDER", "SKIP"}
    assert explanation["why_fit"]
    assert explanation["why_not"]
    assert explanation["salary"]["known"] is False
    assert "not listed" in explanation["salary"]["note"].lower()
    assert any("salesforce" in item.lower() for item in explanation["why_not"])
    assert explanation["location"]["note"]
    assert explanation["seniority"]["note"]
    assert "sql" in explanation["required_skills"]


def test_priority_weights_change_rank():
    profile = {
        "title": "Customer Operations Lead",
        "target_titles": ["Customer Operations Lead"],
        "years_exp": 7,
        "work_mode_pref": "remote",
        "proven_skills": ["Zendesk", "SQL"],
        "transferable_skills": [],
        "domain_expertise": [],
    }
    title_job = {
        "id": "title",
        "title": "Customer Operations Lead",
        "description": "General coordination.",
        "location": "Remote - US",
        "work_mode": "remote",
        "posted_at": "2026-01-01",
    }
    skill_job = {
        "id": "skill",
        "title": "Mailbox Clerk",
        "description": "Daily Zendesk and SQL reporting.",
        "location": "Remote - US",
        "work_mode": "remote",
        "posted_at": "2026-01-01",
    }
    title_weights = {
        "title_and_role_relevance": 1,
        "core_required_skills": 0,
        "experience_seniority": 0,
        "domain_industry_fit": 0,
        "location_and_work_mode": 0,
        "preferred_qualifications": 0,
    }
    skill_weights = dict(title_weights)
    skill_weights["title_and_role_relevance"] = 0
    skill_weights["core_required_skills"] = 1
    by_title = score_job_list([title_job, skill_job], profile, title_weights)
    by_skill = score_job_list([title_job, skill_job], profile, skill_weights)
    assert by_title[0]["id"] == "title"
    assert by_skill[0]["id"] == "skill"


def test_dedupe_preserves_lifecycle_fields():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        store = os.path.join(tmp, "history.json")
        job = {"id": "job-a", "company": "Northwind Civic", "title": "Customer Operations Lead"}
        merge_and_deduplicate([job], store)
        assert set_lifecycle("job-a", "applied", store, notes="Sent Tuesday")
        record = load_store(store)["jobs"]["job-a"]
        first = record["first_seen"]
        assert record["applied"] is True
        assert record["status"] == "applied"
        assert record["notes"] == "Sent Tuesday"
        merge_and_deduplicate([job], store)
        again = load_store(store)["jobs"]["job-a"]
        assert again["first_seen"] == first
        assert again["applied"] is True
        assert again["last_seen"] >= first


def test_profile_name_rejects_traversal():
    with pytest.raises(ValueError):
        validate_profile_name("../other-client")
    with pytest.raises(ValueError):
        validate_profile_name("lucy/private")


def test_profile_runs_do_not_share_files():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        left = os.path.join(tmp, "left")
        right = os.path.join(tmp, "right")
        shutil.copytree(SAMPLE, left)
        shutil.copytree(SAMPLE, right)
        for dest in (left, right):
            for folder in ("jobs", "output"):
                generated = os.path.join(dest, folder)
                if os.path.isdir(generated):
                    shutil.rmtree(generated)
        with open(os.path.join(right, "fixtures", "jobs.json"), "w", encoding="utf-8") as handle:
            json.dump([{
                "id": "only-right",
                "source": "fixture",
                "company": "Right Co",
                "title": "Customer Operations Lead",
                "location": "Remote - US",
                "work_mode": "remote",
                "description": "Zendesk and SQL.",
                "apply_url": "https://example.com/right",
                "is_live": True,
            }], handle)
        run_profile(left, ROOT)
        run_profile(right, ROOT)
        with open(os.path.join(left, "jobs", "history.json"), encoding="utf-8") as handle:
            left_store = handle.read()
        with open(os.path.join(right, "jobs", "history.json"), encoding="utf-8") as handle:
            right_store = handle.read()
        assert "sample_northwind" in left_store
        assert "only-right" not in left_store
        assert "only-right" in right_store
        assert "sample_northwind" not in right_store
        assert os.path.commonpath([os.path.join(left, "output"), left]) == os.path.abspath(left)


def test_truth_guard_blocks_invented_facts_and_allows_source_facts():
    truth = load_candidate_ground_truth(SAMPLE)
    invented = """
## PROFESSIONAL EXPERIENCE
### **VP of Revenue** | Globex Corporation
*January 2010 – March 2012*
* Grew revenue by $4,000,000 and managed a team of 42 engineers.
* Earned an MBA from Harvard Business School.
* AWS Certified Solutions Architect
"""
    flags = {item["type"] for item in check_truthfulness(invented, truth, strict_bullets=True)}
    for required in (
        "invented_employer",
        "invented_title",
        "invented_employment_dates",
        "invented_revenue",
        "invented_team_size",
        "invented_degree",
        "invented_certification",
        "invented_accomplishment",
    ):
        assert required in flags

    copied = """
## PROFESSIONAL EXPERIENCE
### **Customer Operations Lead** | Lumen Desk
*Austin, TX (Remote) | March 2019 – Present*
* Built the Zendesk queue design used by a 12-person remote support team.
"""
    assert check_truthfulness(copied, truth, strict_bullets=True) == []


def test_digest_lists_the_fields_a_person_scans():
    text = format_digest(
        [{
            "company": "Northwind Civic",
            "title": "Customer Operations Lead",
            "location": "Remote - US",
            "source": "fixture",
            "apply_url": "https://example.com/jobs/sample-northwind",
            "first_seen": "2026-09-24",
            "fit_score": 88,
            "fit_evaluation": {
                "score": 88,
                "recommendation": "APPLY",
                "explanation": {
                    "application_priority": "APPLY",
                    "why_fit": ["Zendesk is on the profile."],
                    "why_not": ["Salary is not listed on this posting, so compensation fit is unknown."],
                    "salary": {"known": False, "note": "Salary is not listed on this posting."},
                    "location": {"note": "Posting location: Remote - US (remote)."},
                    "seniority": {"note": "Candidate seniority on file: lead."},
                    "required_skills": ["zendesk"],
                },
            },
        }],
        {"name": "Avery Quinn", "sample": True, "label": "SAMPLE CLIENT"},
        total_scanned=4,
        total_filtered=2,
    )
    for needle in (
        "Northwind Civic",
        "Customer Operations Lead",
        "Remote - US",
        "88",
        "APPLY",
        "Zendesk is on the profile.",
        "not listed",
        "fixture",
        "https://example.com/jobs/sample-northwind",
        "2026-09-24",
        "SAMPLE CLIENT",
        "No auto-apply",
    ):
        assert needle in text


def test_preflight_reports_missing_profile():
    report = preflight(os.path.join(ROOT, "profiles", "missing-client-xyz"), ROOT)
    assert report["ok"] is False
    assert report["blockers"]


def test_disabled_portals_do_not_search_and_sample_workflow_runs(monkeypatch):
    calls = []

    def boom(*_args, **_kwargs):
        calls.append(True)
        raise AssertionError("live portal search should not run")

    monkeypatch.setattr("daily_workflow.search_ats_postings", boom)
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        dest = os.path.join(tmp, "avery")
        shutil.copytree(SAMPLE, dest)
        result = run_profile(dest, ROOT)
        assert calls == []
        assert result["status"] == "success"
        assert result["total_scanned"] == 4
        assert result["total_filtered"] == 2
        digest = open(result["digest_path"], encoding="utf-8").read()
        assert "Northwind Civic" in digest
        assert "Harbor Museum" in digest
        assert "ExcludedCo" not in digest
        assert "Bright Path" not in digest
        assert "Salesforce" in digest
        dashboard = open(result["dashboard_path"], encoding="utf-8").read()
        assert "Avery Quinn" in dashboard
        assert "No auto-apply" in dashboard
        history = load_store(os.path.join(dest, "jobs", "history.json"))
        assert history["jobs"]["sample_northwind"]["score"] is not None
        assert history["jobs"]["sample_northwind"]["first_seen"]
        assert history["jobs"]["sample_northwind"]["last_seen"]
        resumes = []
        for dirpath, _dirs, files in os.walk(os.path.join(dest, "output")):
            for name in files:
                if name == "tailored_resume.md":
                    resumes.append(os.path.join(dirpath, name))
        assert resumes
        truth = load_candidate_ground_truth(dest)
        for path in resumes:
            text = open(path, encoding="utf-8").read()
            report = verify_content(text, truth)
            assert report["passed"], report["violations"]
            assert "Globex" not in text
            assert "Lumen Desk" in text
            assert "12-person" in text or "12" in text
        fit = open(os.path.join(os.path.dirname(resumes[0]), "fit_summary.md"), encoding="utf-8").read()
        prep = open(os.path.join(os.path.dirname(resumes[0]), "interview_prep.md"), encoding="utf-8").read()
        assert "Application priority" in fit
        assert "Do not invent" in prep or "No extra example" in prep


def test_enabled_portals_call_search_when_no_fixture(monkeypatch):
    calls = []

    def fake_search(*_args, **_kwargs):
        calls.append(True)
        return []

    monkeypatch.setattr("daily_workflow.search_ats_postings", fake_search)
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "profile.json"), "w", encoding="utf-8") as handle:
            json.dump({"name": "Live Test", "portals": {"enabled": True}, "search": {"offline": True}}, handle)
        with open(os.path.join(tmp, "MASTER_PROFILE.md"), "w", encoding="utf-8") as handle:
            handle.write("# Master Profile: Live Test\n* **Full Name**: Live Test\n")
        run_profile(tmp, ROOT)
        assert calls == [True]


def test_sample_profile_resolves_inside_examples():
    path = resolve_profile_dir("sample-client", ROOT)
    assert path.endswith(os.path.join("examples", "sample-client"))
    report = preflight(path, ROOT)
    assert report["ok"] is True
