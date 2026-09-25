#!/usr/bin/env python3
"""Optional broad tech-job discovery via freehire.dev's public JSON API.

This source is intentionally separate from the direct-employer ATS core:
- reads are public and unauthenticated;
- freehire.dev is a third-party aggregator / hosted service with no SLA;
- FREEHIRE_API_URL can point at a self-hosted compatible backend;
- failures degrade gracefully and never break the direct ATS workflow.
"""

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ats_engine import clean_html, generate_job_id, infer_work_mode


DEFAULT_BASE_URL = "https://freehire.dev"
USER_AGENT = "AIJobAgent-FreeHire/0.1 (+https://github.com/QaliAI/ai-job-agent)"


def base_url() -> str:
    raw = os.getenv("FREEHIRE_API_URL", "").strip()
    return (raw or DEFAULT_BASE_URL).rstrip("/")


def fetch_envelope(path: str, timeout: int = 20) -> Optional[Dict[str, Any]]:
    url = f"{base_url()}{path}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status != 200:
                return None
            data = json.loads(response.read().decode("utf-8", errors="replace"))
            return data if isinstance(data, dict) else None
    except Exception as exc:
        sys.stderr.write(f"[freehire] unavailable: {exc}\n")
        return None


def normalize_freehire_job(item: Dict[str, Any]) -> Dict[str, Any]:
    enrichment = item.get("enrichment") or {}
    title = str(item.get("title") or "(untitled)").strip()
    company = str(item.get("company") or "").strip()
    location = str(item.get("location") or "").strip()
    description = clean_html(item.get("description") or "")
    slug = str(item.get("public_slug") or item.get("external_id") or "").strip()
    apply_url = str(item.get("url") or "").strip()
    work_mode = str(item.get("work_mode") or "").strip().lower()
    if work_mode not in {"remote", "hybrid", "onsite"}:
        work_mode = infer_work_mode(title, location, description)

    salary_min = enrichment.get("salary_min")
    salary_max = enrichment.get("salary_max")
    currency = enrichment.get("salary_currency")

    canonical_url = f"{base_url()}/jobs/{urllib.parse.quote(slug)}" if slug else apply_url
    now_iso = datetime.now(timezone.utc).isoformat()

    return {
        "id": generate_job_id(
            "freehire",
            company or "unknown",
            title,
            location,
            raw_id=slug or apply_url or None,
        ),
        "source": "freehire",
        "source_type": "aggregator_public_api",
        "upstream_source": item.get("source"),
        "company": company or "Unknown",
        "title": title,
        "location": location,
        "work_mode": work_mode,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "currency": currency,
        "employment_type": enrichment.get("employment_type") or "Unknown",
        "description": description,
        "posted_at": item.get("posted_at") or item.get("created_at"),
        "first_seen_at": now_iso,
        "last_verified_at": now_iso,
        "apply_url": apply_url or canonical_url,
        "canonical_url": canonical_url,
        "is_live": True,
        "skills": item.get("skills") or [],
        "seniority": enrichment.get("seniority"),
        "category": enrichment.get("category"),
        "regions": item.get("regions") or [],
        "countries": item.get("countries") or [],
    }


def search_freehire(
    query: str,
    posted_within_days: int = 30,
    country: str = "US",
    work_mode: str = "",
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    params: List[tuple[str, str]] = [
        ("q", query),
        ("limit", str(max(1, min(limit, 100)))),
        ("offset", str(max(0, offset))),
        ("semantic_ratio", "0"),
    ]
    if posted_within_days > 0:
        params.append(("posted_within_days", str(posted_within_days)))
    if country:
        params.append(("countries", country))
    if work_mode in {"remote", "hybrid", "onsite"}:
        params.append(("work_mode", work_mode))

    path = "/api/v1/jobs/search?" + urllib.parse.urlencode(params)
    envelope = fetch_envelope(path)
    if not envelope:
        return []

    raw_jobs = envelope.get("data") or []
    if not isinstance(raw_jobs, list):
        return []

    return [
        normalize_freehire_job(item)
        for item in raw_jobs
        if isinstance(item, dict)
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Search freehire.dev public jobs API.")
    parser.add_argument("--query", "-q", required=True)
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--country", default="US")
    parser.add_argument("--work-mode", choices=["remote", "hybrid", "onsite"], default="")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--out")
    args = parser.parse_args()

    jobs = search_freehire(
        query=args.query,
        posted_within_days=args.days,
        country=args.country,
        work_mode=args.work_mode,
        limit=args.limit,
    )
    payload = json.dumps(jobs, indent=2, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(payload)
        print(f"Saved {len(jobs)} FreeHire jobs to {args.out}")
    else:
        print(payload)


if __name__ == "__main__":
    main()
