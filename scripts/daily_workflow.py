#!/usr/bin/env python3
"""End-to-End Orchestrated Daily Job Search Workflow for AI Job Agent.

Orchestrates the complete autonomous daily cycle:
1. Load candidate profile & search preferences.
2. Query direct employer ATS feeds (Greenhouse, Lever, Ashby, SmartRecruiters, etc.).
3. Cross-run deduplication via persistent ledger (`jobs/history.json`).
4. Live verification of new postings.
5. Filter hard exclusions (companies, title keywords, salary, clearance).
6. Explainable rubric fit scoring & ranking.
7. Select Top 10 opportunities.
8. Auto-tailor resumes for Top 1–3 opportunities with Claim Check QA.
9. Format & save signature Daily Morning Brief (`output/morning_brief_YYYY-MM-DD.md`).
10. Update persistent history ledger.
"""

import argparse
import json
import os
import re
import sys
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from ats_engine import search_ats_postings
from claim_check import load_candidate_ground_truth
from filter_jobs import filter_job_list, parse_markdown_preferences
from jobstore import merge_and_deduplicate
from morning_brief import format_morning_brief
from opportunity_tracks import matching_queries_for_job, search_queries_from_tracks
from scorer import load_candidate_profile, score_job_list
from tailor_engine import tailor_resume
from verify_postings import verify_job_list


def run_daily_pipeline(
    candidate_dir: str = "candidate",
    output_dir: str = "output",
    jobs_dir: str = "jobs",
    query: str = "",
    tailor_top: int = 3,
    mock_input_file: Optional[str] = None,
    max_queries: int = 8,
    max_companies: int = 0
) -> Dict[str, Any]:
    """Executes the complete daily job search cycle."""
    today_str = date.today().isoformat()
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(jobs_dir, exist_ok=True)
    resumes_dir = os.path.join(output_dir, "resumes")
    os.makedirs(resumes_dir, exist_ok=True)

    print(f"\n🚀 [1/8] Loading candidate profile from '{candidate_dir}'...")
    profile = load_candidate_profile(candidate_dir)
    prefs_file = os.path.join(candidate_dir, "SEARCH_PREFERENCES.md")
    prefs = parse_markdown_preferences(prefs_file) if os.path.exists(prefs_file) else {}

    if query:
        search_queries = [query]
    else:
        search_queries = search_queries_from_tracks(
            profile.get("opportunity_tracks", []),
            limit=max_queries,
        )
        if not search_queries:
            search_queries = list(profile.get("target_titles", []))[:max_queries]
        if not search_queries:
            search_queries = [""]

    query_preview = ", ".join(search_queries[:4])
    if len(search_queries) > 4:
        query_preview += f", +{len(search_queries) - 4} more"
    print(
        f"    Candidate: {profile.get('title', 'Software Engineer')} | "
        f"Queries: {query_preview or '(all roles)'}"
    )

    # Step 2: Fetch raw postings
    raw_jobs: List[Dict[str, Any]] = []
    if mock_input_file and os.path.exists(mock_input_file):
        print(f"📦 [2/8] Loading jobs from fixture: '{mock_input_file}'...")
        with open(mock_input_file, "r", encoding="utf-8") as f:
            raw_jobs = json.load(f)
    else:
        print(
            "🌐 [2/8] Fetching direct employer ATS boards once, then "
            f"matching locally across {len(search_queries)} opportunity queries..."
        )
        registry_path = os.path.join("knowledge", "ats_patterns.json")
        companies = []
        if os.path.exists(registry_path):
            with open(registry_path, "r", encoding="utf-8") as f:
                companies = json.load(f).get("companies", [])

        target_companies = companies if companies else [
            {"name": "Stripe", "ats": "greenhouse", "token": "stripe"},
            {"name": "Ramp", "ats": "ashby", "token": "ramp"},
            {"name": "Linear", "ats": "ashby", "token": "linear"},
            {"name": "Anthropic", "ats": "lever", "token": "anthropic"}
        ]
        if max_companies and max_companies > 0:
            target_companies = target_companies[:max_companies]

        # Fetch each company board once. Re-querying the same board for every
        # title wastes requests and made the old workflow both narrow and costly.
        board_jobs = search_ats_postings(target_companies, query="")

        discovered: Dict[str, Dict[str, Any]] = {}
        for job in board_jobs:
            matched_queries = matching_queries_for_job(job, search_queries)
            if search_queries and not matched_queries:
                continue

            key = (
                job.get("canonical_url")
                or job.get("apply_url")
                or job.get("id")
                or "|".join(
                    [
                        str(job.get("company", "")).lower(),
                        str(job.get("title", "")).lower(),
                        str(job.get("location", "")).lower(),
                    ]
                )
            )
            job_copy = dict(job)
            job_copy["discovery_queries"] = matched_queries
            discovered[key] = job_copy


        raw_jobs = list(discovered.values())

    print(f"    Found {len(raw_jobs)} total postings.")

    # Step 3: Deduplication & Ledger Merge
    history_file = os.path.join(jobs_dir, "history.json")
    print(f"🗄️  [3/8] Checking against history ledger ('{history_file}')...")
    enriched_jobs, new_jobs, dupes = merge_and_deduplicate(raw_jobs, history_file)
    print(f"    New unseen postings: {len(new_jobs)} | Previously seen: {dupes}")

    # Step 4: Verification
    print("🔍 [4/8] Verifying active liveness of postings...")
    verified_jobs = verify_job_list(raw_jobs)
    live_jobs = [j for j in verified_jobs if j.get("is_live", True)]
    print(f"    Active live postings: {len(live_jobs)}/{len(verified_jobs)}")

    # Step 5: Filter Hard Exclusions
    print("🛡️  [5/8] Applying hard exclusion filters (salary, company blacklist, remote mode)...")
    passed_jobs, excluded_jobs = filter_job_list(live_jobs, prefs)
    print(f"    Passed strict filters: {len(passed_jobs)} | Excluded: {len(excluded_jobs)}")

    # Step 6: Transparent Rubric Fit Scoring
    print("⚖️  [6/8] Calculating explainable rubric fit scores & ranking...")
    weights_path = os.path.join("knowledge", "rubric_weights.json")
    weights = {}
    if os.path.exists(weights_path):
        with open(weights_path, "r", encoding="utf-8") as f:
            weights = json.load(f).get("weights", {})

    scored_jobs = score_job_list(passed_jobs, profile, weights) if passed_jobs else []
    top_10 = scored_jobs[:10]
    print(f"    Scored {len(scored_jobs)} jobs. Top score: {top_10[0].get('fit_score', 0) if top_10 else 0}/100")

    # Step 7: Auto-Tailor Top 1-3 Resumes with QA Check
    tailored_map = {}
    if tailor_top > 0 and top_10:
        print(f"✍️  [7/8] Tailoring grounded resumes for top {min(tailor_top, len(top_10))} opportunities...")
        for j in top_10[:tailor_top]:
            jid = j.get("id")
            comp = re.sub(r"[^a-zA-Z0-9_-]", "", j.get("company", "comp").lower())
            slug = re.sub(r"[^a-zA-Z0-9_-]", "-", j.get("title", "role").lower())[:30]
            out_filename = f"{today_str}_{comp}_{slug}.md"
            out_path = os.path.join(resumes_dir, out_filename)
            
            try:
                tailored_md, qa_rep = tailor_resume(candidate_dir, j)
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(tailored_md)
                tailored_map[jid] = os.path.relpath(out_path).replace("\\", "/")
                qa_status = "✅ PASSED" if qa_rep["passed"] else f"⚠️ {qa_rep['violation_count']} QA flags"
                print(f"    → Tailored {j.get('company')} ({j.get('title')}) | QA: {qa_status}")
            except Exception as e:
                sys.stderr.write(f"    Error tailoring resume for {j.get('company')}: {e}\n")

    # Step 8: Generate Daily Morning Brief
    print("🌅 [8/8] Generating signature Daily Morning Brief...")
    brief_md = format_morning_brief(
        top_10,
        profile,
        total_scanned=len(raw_jobs),
        total_filtered=len(passed_jobs),
        tailored_files=tailored_map
    )

    brief_path = os.path.join(output_dir, f"morning_brief_{today_str}.md")
    with open(brief_path, "w", encoding="utf-8") as f:
        f.write(brief_md)

    latest_brief_path = os.path.join(output_dir, "latest_brief.md")
    with open(latest_brief_path, "w", encoding="utf-8") as f:
        f.write(brief_md)

    print(f"\n✨ Daily job search complete! Morning brief saved to:\n   📄 {brief_path}\n")

    return {
        "status": "success",
        "date": today_str,
        "total_scanned": len(raw_jobs),
        "total_filtered": len(passed_jobs),
        "top_jobs_count": len(top_10),
        "tailored_count": len(tailored_map),
        "brief_path": brief_path,
        "top_jobs": top_10,
        "search_queries": search_queries
    }


def main():
    parser = argparse.ArgumentParser(description="Run end-to-end AI Job Agent daily workflow.")
    parser.add_argument("--candidate", default="candidate", help="Candidate data directory")
    parser.add_argument("--output", default="output", help="Output directory for reports & resumes")
    parser.add_argument("--jobs", default="jobs", help="Jobs directory for history ledger")
    parser.add_argument("--query", default="", help="Search query override")
    parser.add_argument("--tailor-top", type=int, default=3, help="Number of top jobs to auto-tailor")
    parser.add_argument("--fixture", help="Path to fixture JSON for offline/testing runs")
    parser.add_argument(
        "--max-queries",
        type=int,
        default=8,
        help="Maximum number of balanced opportunity-track queries per run"
    )
    parser.add_argument(
        "--max-companies",
        type=int,
        default=0,
        help="Maximum ATS companies to scan; 0 means the full registry"
    )

    args = parser.parse_args()

    # Fallback to example profile if candidate directory has no master profile yet
    cand_dir = args.candidate
    if not os.path.exists(os.path.join(cand_dir, "MASTER_PROFILE.md")):
        ex_dir = os.path.join("examples", "jordan-taylor")
        if os.path.exists(os.path.join(ex_dir, "MASTER_PROFILE.md")):
            print(f"Notice: 'candidate/MASTER_PROFILE.md' not found. Using fixture at '{ex_dir}'...")
            cand_dir = ex_dir

    result = run_daily_pipeline(
        candidate_dir=cand_dir,
        output_dir=args.output,
        jobs_dir=args.jobs,
        query=args.query,
        tailor_top=args.tailor_top,
        mock_input_file=args.fixture,
        max_queries=args.max_queries,
        max_companies=args.max_companies
    )


if __name__ == "__main__":
    main()
