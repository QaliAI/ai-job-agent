#!/usr/bin/env python3
"""Hard Exclusion & Strict Filtering Engine for AI Job Agent.

Filters incoming jobs against candidate SEARCH_PREFERENCES:
- Excluded company blacklist
- Excluded title keywords (e.g. 'intern', 'junior', 'contract')
- Below minimum salary threshold (when salary is disclosed)
- Location & remote/hybrid constraints
- Work authorization / security clearance disqualifiers

Outputs filtered jobs and an audit trail of why jobs were rejected.
"""

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def _extract_section(content: str, heading_fragment: str) -> str:
    """Extract a markdown heading section without leaking bullets from other sections."""
    pattern = (
        r"(?ims)^##+\\s*[^\\n]*"
        + re.escape(heading_fragment)
        + r"[^\\n]*\\n(.*?)(?=^##+\\s|\\Z)"
    )
    match = re.search(pattern, content)
    return match.group(1) if match else ""


def _extract_bullets(section: str) -> List[str]:
    values = []
    for line in section.splitlines():
        match = re.match(r"^\\s*[-*]\\s+(.*)$", line)
        if not match:
            continue
        value = match.group(1).strip()
        # Ignore parent labels such as "* **Primary Target Titles**:".
        if value.startswith("**") and value.endswith(":"):
            continue
        if value:
            values.append(value.strip('"').strip())
    return values


def parse_markdown_preferences(filepath: str) -> Dict[str, Any]:
    """Parse SEARCH_PREFERENCES.md into structured criteria.

    The previous parser treated nearly every bullet in the document as a target
    title. That polluted role matching with locations, industries, and blacklist
    entries. This parser scopes extraction to the intended markdown sections.
    """
    if not os.path.exists(filepath):
        return {}

    prefs: Dict[str, Any] = {
        "target_titles": [],
        "work_mode": "any",
        "allowed_locations": [],
        "min_salary": None,
        "excluded_companies": [],
        "excluded_title_keywords": [],
        "requires_clearance": False
    }

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        target_section = _extract_section(content, "Target Roles")
        prefs["target_titles"] = [
            value
            for value in _extract_bullets(target_section)
            if not value.lower().startswith((
                "primary target titles",
                "secondary / adjacent titles",
                "secondary target titles",
            ))
        ]

        wm_match = re.search(
            r"Work Mode(?: Preference)?\\*{0,2}\\s*:\\s*([^\\n\\r]+)",
            content,
            re.IGNORECASE,
        )
        if wm_match:
            wm_text = wm_match.group(1).lower()
            if "remote" in wm_text:
                prefs["work_mode"] = "remote"
            elif "hybrid" in wm_text:
                prefs["work_mode"] = "hybrid"
            elif "onsite" in wm_text or "on-site" in wm_text:
                prefs["work_mode"] = "onsite"

        location_section = _extract_section(content, "Work Arrangement")
        allowed_match = re.search(
            r"(?ims)Allowed Locations\\*{0,2}\\s*:\\s*\\n(.*?)(?=^\\s*[-*]\\s*\\*\\*[^\\n]+:\\*\\*|\\Z)",
            location_section,
        )
        if allowed_match:
            prefs["allowed_locations"] = _extract_bullets(allowed_match.group(1))

        sal_match = re.search(
            r"Minimum Base Salary\\*{0,2}\\s*:\\s*\\$?(\\d{1,3}(?:,\\d{3})*|\\d+)",
            content,
            re.IGNORECASE,
        )
        if sal_match:
            try:
                prefs["min_salary"] = float(sal_match.group(1).replace(",", ""))
            except ValueError:
                pass

        exclusion_section = _extract_section(content, "Hard Exclusions")
        company_match = re.search(
            r"(?ims)Excluded Companies\\*{0,2}\\s*:\\s*\\n(.*?)(?=^\\s*[-*]\\s*\\*\\*[^\\n]+:\\*\\*|\\Z)",
            exclusion_section,
        )
        if company_match:
            prefs["excluded_companies"] = [
                value.lower() for value in _extract_bullets(company_match.group(1))
            ]

        keyword_match = re.search(
            r"Excluded (?:Keywords in Titles|Title Keywords)\\*{0,2}\\s*:\\s*([^\\n\\r]+)",
            exclusion_section,
            re.IGNORECASE,
        )
        if keyword_match:
            raw = keyword_match.group(1)
            quoted = re.findall(r'"([^"]+)"', raw)
            values = quoted or [part.strip() for part in raw.split(",")]
            prefs["excluded_title_keywords"] = [
                value.lower().strip() for value in values if value.strip()
            ]

    except Exception as e:
        sys.stderr.write(f"Error parsing preferences {filepath}: {e}\\n")

    return prefs


def evaluate_exclusion(job: Dict[str, Any], prefs: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Evaluates if a single job should be excluded.

    Returns:
        (is_excluded, reason)
    """
    company = (job.get("company") or "").strip().lower()
    title = (job.get("title") or "").strip().lower()
    location = (job.get("location") or "").strip().lower()
    desc = (job.get("description") or "").strip().lower()
    work_mode = job.get("work_mode", "unknown").lower()
    sal_max = job.get("salary_max")
    
    # 1. Company Blacklist
    for exc_comp in prefs.get("excluded_companies", []):
        if exc_comp and exc_comp in company:
            return True, f"Excluded company: '{exc_comp}' matches company '{job.get('company')}'"

    # 2. Excluded Title Keywords
    for kw in prefs.get("excluded_title_keywords", []):
        if kw and kw in title:
            return True, f"Excluded title keyword: '{kw}' found in title '{job.get('title')}'"

    # 3. Minimum Salary Disqualification (only if salary is explicitly disclosed)
    min_sal_pref = prefs.get("min_salary")
    if min_sal_pref and sal_max:
        if sal_max < min_sal_pref:
            return True, f"Disclosed max salary ${sal_max:,.0f} is below candidate minimum threshold ${min_sal_pref:,.0f}"

    # 4. Strict Remote Constraint
    pref_work_mode = prefs.get("work_mode")
    if pref_work_mode == "remote":
        if work_mode == "onsite" and "remote" not in location:
            # Check if location is allowed
            allowed_locs = [l.lower() for l in prefs.get("allowed_locations", [])]
            if not any(al in location for al in allowed_locs if al):
                return True, f"Remote required, but job is strictly onsite at '{job.get('location')}'"

    # 5. Security Clearance Disqualification
    if not prefs.get("requires_clearance", False):
        if "active top secret" in desc or "ts/sci clearance required" in desc:
            return True, "Requires active Top Secret / TS-SCI clearance which candidate does not hold"

    return False, None


def filter_job_list(
    jobs: List[Dict[str, Any]],
    prefs: Dict[str, Any]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Filters a list of jobs against search preferences.

    Returns:
        (passed_jobs, excluded_jobs_with_reasons)
    """
    passed = []
    excluded = []
    
    for job in jobs:
        is_exc, reason = evaluate_exclusion(job, prefs)
        if is_exc:
            job_copy = dict(job)
            job_copy["exclusion_reason"] = reason
            excluded.append(job_copy)
        else:
            passed.append(job)
            
    return passed, excluded


def main():
    parser = argparse.ArgumentParser(description="Filter jobs against hard exclusion rules.")
    parser.add_argument("--in", dest="in_file", required=True, help="Input jobs JSON file (or - for stdin)")
    parser.add_argument("--prefs", default="candidate/SEARCH_PREFERENCES.md", help="Path to SEARCH_PREFERENCES.md")
    parser.add_argument("--out", help="Output passed jobs JSON path")
    parser.add_argument("--audit", help="Output excluded jobs JSON path")

    args = parser.parse_args()

    raw_data = []
    if args.in_file == "-":
        raw_data = json.load(sys.stdin)
    else:
        with open(args.in_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

    prefs = parse_markdown_preferences(args.prefs)
    passed, excluded = filter_job_list(raw_data, prefs)

    out_json = json.dumps(passed, indent=2, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out_json)
        print(f"Filtered: {len(passed)} passed, {len(excluded)} excluded. Saved to {args.out}")
    else:
        print(out_json)

    if args.audit:
        with open(args.audit, "w", encoding="utf-8") as f:
            json.dump(excluded, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
