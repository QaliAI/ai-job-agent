#!/usr/bin/env python3
"""Company ATS Sniffer & Board Resolver for AI Job Agent.

Given a company name, slug, or careers URL, detects which ATS platform
they use and extracts the public board token.

Supports:
- Greenhouse
- Lever
- Ashby
- SmartRecruiters
- Workable
- Recruitee
- BambooHR
- Personio
- Teamtailor
"""

import argparse
import json
import os
import re
import sys
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

USER_AGENT = "AIJobAgent-Discover/0.1.0 (+https://github.com/QaliAI/ai-job-agent)"
HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/json, text/plain, */*"}


def test_endpoint(url: str, timeout: int = 5) -> bool:
    """Tests if an ATS public endpoint returns HTTP 200."""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                # Basic check for non-empty response
                data = resp.read(500)
                return len(data) > 20
    except Exception:
        pass
    return False


def discover_ats_for_slug(slug: str) -> Optional[Dict[str, str]]:
    """Probes all supported ATS platforms for a given company slug."""
    clean_slug = re.sub(r"[^a-zA-Z0-9_-]", "", slug.lower().strip())
    if not clean_slug:
        return None

    probes = [
        ("greenhouse", f"https://boards-api.greenhouse.io/v1/boards/{clean_slug}/jobs?content=false"),
        ("ashby", f"https://api.ashbyhq.com/posting-api/job-board/{clean_slug}"),
        ("lever", f"https://api.lever.co/v0/postings/{clean_slug}?mode=json"),
        ("smartrecruiters", f"https://api.smartrecruiters.com/v1/companies/{clean_slug}/postings?limit=1"),
        ("recruitee", f"https://{clean_slug}.recruitee.com/api/offers/"),
        ("workable", f"https://apply.workable.com/api/v1/widget/accounts/{clean_slug}?details=true"),
        ("bamboohr", f"https://{clean_slug}.bamboohr.com/careers/list"),
        ("personio", f"https://{clean_slug}.jobs.personio.de/xml"),
        ("teamtailor", f"https://{clean_slug}.teamtailor.com/jobs.rss")
    ]

    for ats_type, test_url in probes:
        if test_endpoint(test_url):
            return {
                "name": slug.capitalize(),
                "ats": ats_type,
                "token": clean_slug,
                "verified_endpoint": test_url
            }

    return None


def main():
    parser = argparse.ArgumentParser(description="Sniff and detect company ATS board.")
    parser.add_argument("company", help="Company name or slug (e.g. stripe, ramp, figma)")
    parser.add_argument("--add-to-registry", help="Path to JSON registry to append discovered company")

    args = parser.parse_args()

    result = discover_ats_for_slug(args.company)
    if result:
        print(f"✅ Found ATS board for '{args.company}':")
        print(f"   Platform: {result['ats'].capitalize()}")
        print(f"   Token:    {result['token']}")
        print(f"   Endpoint: {result['verified_endpoint']}")
        
        if args.add_to_registry and os.path.exists(args.add_to_registry):
            with open(args.add_to_registry, "r", encoding="utf-8") as f:
                data = json.load(f)
            comps = data.get("companies", [])
            # Avoid duplicate
            if not any(c.get("token") == result["token"] and c.get("ats") == result["ats"] for c in comps):
                comps.append({"name": result["name"], "ats": result["ats"], "token": result["token"]})
                data["companies"] = comps
                with open(args.add_to_registry, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                print(f"   Saved to registry '{args.add_to_registry}'")
    else:
        print(f"❌ Could not automatically detect a public ATS board for '{args.company}'.")
        print("   Tips: Try the company's careers URL or exact subdomain slug.")


if __name__ == "__main__":
    main()
