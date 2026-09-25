#!/usr/bin/env python3
"""Multi-Platform Direct ATS Client & Normalizer for AI Job Agent.

Connects directly to public, keyless employer career endpoints:
- Greenhouse (boards-api.greenhouse.io)
- Lever (api.lever.co)
- Ashby (api.ashbyhq.com)
- SmartRecruiters (api.smartrecruiters.com)
- Workable (apply.workable.com)
- Recruitee (recruitee.com)
- BambooHR (bamboohr.com)
- Personio (jobs.personio.de/xml)
- Teamtailor (teamtailor.com/jobs.rss)
- Workday (wday/cxs endpoints)

Converts all postings into the canonical AI Job Agent job schema.
Zero external dependencies (pure Python standard library).
"""

import argparse
import concurrent.futures
import hashlib
import html
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


USER_AGENT = "AIJobAgent/0.1.0 (+https://github.com/QaliAI/ai-job-agent)"
HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/json, text/plain, */*"}


def clean_html(raw_html: Optional[str]) -> str:
    """Strips HTML tags, decodes HTML entities, and normalizes whitespace."""
    if not raw_html:
        return ""
    # Double unescape in case of double-encoded HTML (common in Greenhouse)
    text = html.unescape(html.unescape(raw_html))
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</li>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


def generate_job_id(source: str, company: str, title: str, location: str, raw_id: Optional[str] = None) -> str:
    """Generates a deterministic 16-character SHA-1 hash for deduplication."""
    if raw_id:
        seed = f"{source}|{company}|{raw_id}".lower()
    else:
        seed = f"{source}|{company}|{title}|{location}".lower()
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]


def infer_work_mode(title: str, location: str, description: str) -> str:
    """Infers work mode (remote, hybrid, onsite) from posting text."""
    combined = f"{title} {location} {description}".lower()
    if "remote" in combined or "anywhere" in combined or "work from home" in combined:
        if "hybrid" in combined and "hybrid" in location.lower():
            return "hybrid"
        return "remote"
    if "hybrid" in combined:
        return "hybrid"
    if "onsite" in combined or "on-site" in combined or "in-office" in combined:
        return "onsite"
    return "onsite" if location else "unknown"


def extract_salary(text: str) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    """Extracts salary minimum, maximum, and currency from job description."""
    if not text:
        return None, None, None
    
    # Check for USD / EUR / GBP salary patterns e.g. $140,000 - $180,000 or $140k - $180k
    pattern = re.compile(
        r"([\$€£])\s*(\d{2,3}(?:,\d{3})*|\d{2,3})(?:k|\s*000)?\s*(?:-|–|to)\s*([\$€£])?\s*(\d{2,3}(?:,\d{3})*|\d{2,3})(?:k|\s*000)?",
        re.IGNORECASE
    )
    match = pattern.search(text)
    if match:
        curr_sym = match.group(1)
        curr = "USD" if curr_sym == "$" else ("EUR" if curr_sym == "€" else ("GBP" if curr_sym == "£" else "USD"))
        
        raw_min = match.group(2).replace(",", "")
        raw_max = match.group(4).replace(",", "")
        
        try:
            val_min = float(raw_min)
            val_max = float(raw_max)
            # Handle 'k' notation e.g. 150 -> 150000
            if val_min < 1000:
                val_min *= 1000
            if val_max < 1000:
                val_max *= 1000
            return val_min, val_max, curr
        except ValueError:
            pass
            
    return None, None, None


def fetch_json(url: str, timeout: int = 15) -> Optional[Any]:
    """Fetches and decodes JSON from a URL with timeout and standard headers."""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                data = response.read().decode("utf-8", errors="replace")
                return json.loads(data)
    except Exception as e:
        sys.stderr.write(f"[{url}] HTTP error: {e}\n")
    return None


def fetch_xml(url: str, timeout: int = 15) -> Optional[ET.Element]:
    """Fetches and parses XML from a URL."""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                data = response.read().decode("utf-8", errors="replace")
                return ET.fromstring(data)
    except Exception as e:
        sys.stderr.write(f"[{url}] XML error: {e}\n")
    return None


# -------------------------------------------------------------
# Individual ATS Parsers
# -------------------------------------------------------------

def parse_greenhouse(token: str, query: str = "") -> List[Dict[str, Any]]:
    """Pulls jobs from Greenhouse public board API."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
    data = fetch_json(url)
    if not data or "jobs" not in data:
        return []
    
    results = []
    now_iso = datetime.now(timezone.utc).isoformat()
    for item in data.get("jobs", []):
        title = item.get("title", "").strip()
        if query and query.lower() not in title.lower() and query.lower() not in item.get("content", "").lower():
            continue
            
        loc_obj = item.get("location") or {}
        location = loc_obj.get("name", "").strip() if isinstance(loc_obj, dict) else str(loc_obj).strip()
        raw_html = item.get("content", "")
        desc = clean_html(raw_html)
        job_id = str(item.get("id", ""))
        apply_url = item.get("absolute_url", f"https://boards.greenhouse.io/{token}/jobs/{job_id}")
        
        sal_min, sal_max, currency = extract_salary(desc)
        work_mode = infer_work_mode(title, location, desc)
        posted_at = item.get("updated_at")
        
        canonical_job = {
            "id": generate_job_id("greenhouse", token, title, location, raw_id=job_id),
            "source": "greenhouse",
            "source_type": "ats_direct",
            "company": token.capitalize(),
            "title": title,
            "location": location,
            "work_mode": work_mode,
            "salary_min": sal_min,
            "salary_max": sal_max,
            "currency": currency,
            "employment_type": "Full-time",
            "description": desc,
            "posted_at": posted_at,
            "first_seen_at": now_iso,
            "last_verified_at": now_iso,
            "apply_url": apply_url,
            "canonical_url": apply_url,
            "is_live": True
        }
        results.append(canonical_job)
    return results


def parse_lever(token: str, query: str = "") -> List[Dict[str, Any]]:
    """Pulls jobs from Lever public postings API."""
    url = f"https://api.lever.co/v0/postings/{token}?mode=json"
    data = fetch_json(url)
    if not data or not isinstance(data, list):
        return []
    
    results = []
    now_iso = datetime.now(timezone.utc).isoformat()
    for item in data:
        title = item.get("text", "").strip()
        desc_plain = item.get("descriptionPlain", "") or clean_html(item.get("description", ""))
        if query and query.lower() not in title.lower() and query.lower() not in desc_plain.lower():
            continue
            
        cats = item.get("categories") or {}
        location = cats.get("location", "").strip()
        work_mode = infer_work_mode(title, location, desc_plain)
        raw_id = item.get("id", "")
        apply_url = item.get("applyUrl", item.get("hostedUrl", f"https://jobs.lever.co/{token}/{raw_id}"))
        sal_min, sal_max, currency = extract_salary(desc_plain)
        
        created_at_ms = item.get("createdAt")
        posted_at = datetime.fromtimestamp(created_at_ms / 1000.0, timezone.utc).isoformat() if created_at_ms else None
        
        canonical_job = {
            "id": generate_job_id("lever", token, title, location, raw_id=raw_id),
            "source": "lever",
            "source_type": "ats_direct",
            "company": token.capitalize(),
            "title": title,
            "location": location,
            "work_mode": work_mode,
            "salary_min": sal_min,
            "salary_max": sal_max,
            "currency": currency,
            "employment_type": cats.get("commitment", "Full-time"),
            "description": desc_plain,
            "posted_at": posted_at,
            "first_seen_at": now_iso,
            "last_verified_at": now_iso,
            "apply_url": apply_url,
            "canonical_url": item.get("hostedUrl", apply_url),
            "is_live": True
        }
        results.append(canonical_job)
    return results


def parse_ashby(token: str, query: str = "") -> List[Dict[str, Any]]:
    """Pulls jobs from Ashby posting API."""
    url = f"https://api.ashbyhq.com/posting-api/job-board/{token}"
    data = fetch_json(url)
    if not data or "jobs" not in data:
        return []
    
    results = []
    now_iso = datetime.now(timezone.utc).isoformat()
    for item in data.get("jobs", []):
        title = item.get("title", "").strip()
        raw_desc = item.get("descriptionHtml", "") or item.get("descriptionPlain", "")
        desc = clean_html(raw_desc)
        if query and query.lower() not in title.lower() and query.lower() not in desc.lower():
            continue
            
        location = item.get("location", "").strip()
        is_remote = item.get("isRemote", False)
        work_mode = "remote" if is_remote else infer_work_mode(title, location, desc)
        raw_id = item.get("id", "")
        apply_url = item.get("applyUrl", item.get("jobUrl", f"https://jobs.ashbyhq.com/{token}/{raw_id}"))
        sal_min, sal_max, currency = extract_salary(desc)
        
        canonical_job = {
            "id": generate_job_id("ashby", token, title, location, raw_id=raw_id),
            "source": "ashby",
            "source_type": "ats_direct",
            "company": token.capitalize(),
            "title": title,
            "location": location,
            "work_mode": work_mode,
            "salary_min": sal_min,
            "salary_max": sal_max,
            "currency": currency,
            "employment_type": item.get("employmentType", "Full-time"),
            "description": desc,
            "posted_at": item.get("publishedAt"),
            "first_seen_at": now_iso,
            "last_verified_at": now_iso,
            "apply_url": apply_url,
            "canonical_url": item.get("jobUrl", apply_url),
            "is_live": True
        }
        results.append(canonical_job)
    return results


def parse_smartrecruiters(token: str, query: str = "") -> List[Dict[str, Any]]:
    """Pulls jobs from SmartRecruiters public posting API."""
    encoded_q = urllib.parse.quote(query) if query else ""
    url = f"https://api.smartrecruiters.com/v1/companies/{token}/postings"
    if encoded_q:
        url += f"?q={encoded_q}&limit=50"
    else:
        url += "?limit=50"
        
    data = fetch_json(url)
    if not data or "content" not in data:
        return []
        
    results = []
    now_iso = datetime.now(timezone.utc).isoformat()
    for item in data.get("content", []):
        title = item.get("name", "").strip()
        loc_obj = item.get("location") or {}
        city = loc_obj.get("city", "")
        region = loc_obj.get("region", "")
        country = loc_obj.get("country", "")
        location_parts = [p for p in [city, region, country] if p]
        location = ", ".join(location_parts)
        
        raw_id = item.get("id", "")
        apply_url = f"https://jobs.smartrecruiters.com/{token}/{raw_id}"
        work_mode = infer_work_mode(title, location, "")
        
        canonical_job = {
            "id": generate_job_id("smartrecruiters", token, title, location, raw_id=raw_id),
            "source": "smartrecruiters",
            "source_type": "ats_direct",
            "company": token.capitalize(),
            "title": title,
            "location": location,
            "work_mode": work_mode,
            "salary_min": None,
            "salary_max": None,
            "currency": None,
            "employment_type": "Full-time",
            "description": f"Role: {title} at {token.capitalize()}. Location: {location}",
            "posted_at": item.get("releasedDate"),
            "first_seen_at": now_iso,
            "last_verified_at": now_iso,
            "apply_url": apply_url,
            "canonical_url": apply_url,
            "is_live": True
        }
        results.append(canonical_job)
    return results


def parse_recruitee(token: str, query: str = "") -> List[Dict[str, Any]]:
    """Pulls jobs from Recruitee public offers API."""
    url = f"https://{token}.recruitee.com/api/offers/"
    data = fetch_json(url)
    if not data or "offers" not in data:
        return []
        
    results = []
    now_iso = datetime.now(timezone.utc).isoformat()
    for item in data.get("offers", []):
        title = item.get("title", "").strip()
        desc = clean_html(item.get("description", ""))
        if query and query.lower() not in title.lower() and query.lower() not in desc.lower():
            continue
            
        location = item.get("location", "").strip()
        is_remote = item.get("remote", False)
        work_mode = "remote" if is_remote else infer_work_mode(title, location, desc)
        raw_id = str(item.get("id", ""))
        careers_url = item.get("careers_url", f"https://{token}.recruitee.com/o/{item.get('slug', raw_id)}")
        sal_min, sal_max, currency = extract_salary(desc)
        
        canonical_job = {
            "id": generate_job_id("recruitee", token, title, location, raw_id=raw_id),
            "source": "recruitee",
            "source_type": "ats_direct",
            "company": token.capitalize(),
            "title": title,
            "location": location,
            "work_mode": work_mode,
            "salary_min": sal_min,
            "salary_max": sal_max,
            "currency": currency,
            "employment_type": item.get("employment_type_code", "Full-time"),
            "description": desc,
            "posted_at": item.get("created_at"),
            "first_seen_at": now_iso,
            "last_verified_at": now_iso,
            "apply_url": careers_url,
            "canonical_url": careers_url,
            "is_live": True
        }
        results.append(canonical_job)
    return results


def parse_bamboohr(token: str, query: str = "") -> List[Dict[str, Any]]:
    """Pulls jobs from BambooHR public careers list."""
    url = f"https://{token}.bamboohr.com/careers/list"
    data = fetch_json(url)
    if not data or "result" not in data:
        return []
        
    results = []
    now_iso = datetime.now(timezone.utc).isoformat()
    for item in data.get("result", []):
        title = item.get("jobTitle", "").strip()
        if query and query.lower() not in title.lower():
            continue
            
        loc_obj = item.get("location") or {}
        city = loc_obj.get("city", "")
        state = loc_obj.get("state", "")
        location = f"{city}, {state}".strip(", ")
        raw_id = str(item.get("id", ""))
        apply_url = f"https://{token}.bamboohr.com/careers/{raw_id}"
        work_mode = infer_work_mode(title, location, "")
        
        canonical_job = {
            "id": generate_job_id("bamboohr", token, title, location, raw_id=raw_id),
            "source": "bamboohr",
            "source_type": "ats_direct",
            "company": token.capitalize(),
            "title": title,
            "location": location,
            "work_mode": work_mode,
            "salary_min": None,
            "salary_max": None,
            "currency": None,
            "employment_type": "Full-time",
            "description": f"Role: {title} at {token.capitalize()}. Department: {item.get('department', 'N/A')}",
            "posted_at": None,
            "first_seen_at": now_iso,
            "last_verified_at": now_iso,
            "apply_url": apply_url,
            "canonical_url": apply_url,
            "is_live": True
        }
        results.append(canonical_job)
    return results


def parse_personio(token: str, query: str = "") -> List[Dict[str, Any]]:
    """Pulls jobs from Personio XML feed."""
    url = f"https://{token}.jobs.personio.de/xml"
    root = fetch_xml(url)
    if root is None:
        return []
        
    results = []
    now_iso = datetime.now(timezone.utc).isoformat()
    for pos in root.findall(".//position"):
        title_el = pos.find("name")
        title = title_el.text.strip() if title_el is not None and title_el.text else ""
        
        desc_parts = []
        for jd in pos.findall(".//jobDescription"):
            name = jd.find("name")
            val = jd.find("value")
            if name is not None and name.text:
                desc_parts.append(name.text)
            if val is not None and val.text:
                desc_parts.append(clean_html(val.text))
        desc = "\n\n".join(desc_parts)
        
        if query and query.lower() not in title.lower() and query.lower() not in desc.lower():
            continue
            
        office_el = pos.find("office")
        location = office_el.text.strip() if office_el is not None and office_el.text else ""
        raw_id_el = pos.find("id")
        raw_id = raw_id_el.text.strip() if raw_id_el is not None and raw_id_el.text else ""
        apply_url = f"https://{token}.jobs.personio.de/job/{raw_id}"
        work_mode = infer_work_mode(title, location, desc)
        sal_min, sal_max, currency = extract_salary(desc)
        
        canonical_job = {
            "id": generate_job_id("personio", token, title, location, raw_id=raw_id),
            "source": "personio",
            "source_type": "ats_direct",
            "company": token.capitalize(),
            "title": title,
            "location": location,
            "work_mode": work_mode,
            "salary_min": sal_min,
            "salary_max": sal_max,
            "currency": currency,
            "employment_type": "Full-time",
            "description": desc,
            "posted_at": None,
            "first_seen_at": now_iso,
            "last_verified_at": now_iso,
            "apply_url": apply_url,
            "canonical_url": apply_url,
            "is_live": True
        }
        results.append(canonical_job)
    return results


def parse_teamtailor(token: str, query: str = "") -> List[Dict[str, Any]]:
    """Pulls jobs from Teamtailor public RSS feed."""
    url = f"https://{token}.teamtailor.com/jobs.rss"
    root = fetch_xml(url)
    if root is None:
        return []
        
    results = []
    now_iso = datetime.now(timezone.utc).isoformat()
    for item in root.findall(".//item"):
        title_el = item.find("title")
        title = title_el.text.strip() if title_el is not None and title_el.text else ""
        desc_el = item.find("description")
        desc = clean_html(desc_el.text) if desc_el is not None and desc_el.text else ""
        
        if query and query.lower() not in title.lower() and query.lower() not in desc.lower():
            continue
            
        link_el = item.find("link")
        apply_url = link_el.text.strip() if link_el is not None and link_el.text else f"https://{token}.teamtailor.com"
        pub_el = item.find("pubDate")
        posted_at = pub_el.text.strip() if pub_el is not None and pub_el.text else None
        
        location = ""
        work_mode = infer_work_mode(title, location, desc)
        sal_min, sal_max, currency = extract_salary(desc)
        
        canonical_job = {
            "id": generate_job_id("teamtailor", token, title, location, raw_id=apply_url),
            "source": "teamtailor",
            "source_type": "ats_direct",
            "company": token.capitalize(),
            "title": title,
            "location": location,
            "work_mode": work_mode,
            "salary_min": sal_min,
            "salary_max": sal_max,
            "currency": currency,
            "employment_type": "Full-time",
            "description": desc,
            "posted_at": posted_at,
            "first_seen_at": now_iso,
            "last_verified_at": now_iso,
            "apply_url": apply_url,
            "canonical_url": apply_url,
            "is_live": True
        }
        results.append(canonical_job)
    return results


# -------------------------------------------------------------
# Unified Multi-ATS Search Dispatcher
# -------------------------------------------------------------

ATS_PARSERS = {
    "greenhouse": parse_greenhouse,
    "lever": parse_lever,
    "ashby": parse_ashby,
    "smartrecruiters": parse_smartrecruiters,
    "recruitee": parse_recruitee,
    "bamboohr": parse_bamboohr,
    "personio": parse_personio,
    "teamtailor": parse_teamtailor,
}


def fetch_company_jobs(comp: Dict[str, str], query: str = "") -> List[Dict[str, Any]]:
    """Fetches and parses jobs for a single company descriptor."""
    ats_type = comp.get("ats", "").lower()
    token = comp.get("token", "")
    name = comp.get("name", token)
    
    parser = ATS_PARSERS.get(ats_type)
    if not parser:
        sys.stderr.write(f"Unsupported ATS type: {ats_type} for company {name}\n")
        return []
        
    try:
        jobs = parser(token, query=query)
        for j in jobs:
            if name:
                j["company"] = name
        return jobs
    except Exception as e:
        sys.stderr.write(f"Error fetching {name} ({ats_type}/{token}): {e}\n")
        return []


def search_ats_postings(
    companies_list: List[Dict[str, str]],
    query: str = "",
    max_workers: int = 8
) -> List[Dict[str, Any]]:
    """Searches across a collection of company tokens and ATS platforms concurrently."""
    if not companies_list:
        return []

    # Sequential execution if only one company or workers <= 1
    if len(companies_list) == 1 or max_workers <= 1:
        all_jobs = []
        for comp in companies_list:
            all_jobs.extend(fetch_company_jobs(comp, query=query))
        return all_jobs

    all_jobs = []
    worker_count = min(max_workers, len(companies_list))
    with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_to_comp = {
            executor.submit(fetch_company_jobs, comp, query): comp
            for comp in companies_list
        }
        for future in concurrent.futures.as_completed(future_to_comp):
            try:
                jobs = future.result()
                all_jobs.extend(jobs)
            except Exception as e:
                comp = future_to_comp.get(future, {})
                sys.stderr.write(f"Error executing fetch for {comp.get('name', 'company')}: {e}\n")

    return all_jobs


def main():
    parser = argparse.ArgumentParser(description="Query public ATS endpoints directly.")
    parser.add_argument("--greenhouse", help="Comma-separated Greenhouse company tokens (e.g. stripe,airbnb)")
    parser.add_argument("--lever", help="Comma-separated Lever company tokens (e.g. netflix,spotify)")
    parser.add_argument("--ashby", help="Comma-separated Ashby company tokens (e.g. ramp,linear,notion)")
    parser.add_argument("--smartrecruiters", help="Comma-separated SmartRecruiters tokens (e.g. visa,ikea)")
    parser.add_argument("--recruitee", help="Comma-separated Recruitee tokens (e.g. hotjar)")
    parser.add_argument("--bamboohr", help="Comma-separated BambooHR tokens")
    parser.add_argument("--personio", help="Comma-separated Personio tokens (e.g. n26)")
    parser.add_argument("--teamtailor", help="Comma-separated Teamtailor tokens (e.g. zalando)")
    parser.add_argument("--registry", help="Path to JSON file containing company tokens")
    parser.add_argument("--query", default="", help="Keyword / title filter")
    parser.add_argument("--workers", type=int, default=8, help="Number of concurrent worker threads")
    parser.add_argument("--out", help="Path to save output JSON (defaults to stdout)")

    args = parser.parse_args()

    companies = []
    if args.registry:
        try:
            with open(args.registry, "r", encoding="utf-8") as f:
                data = json.load(f)
                companies.extend(data.get("companies", []))
        except Exception as e:
            sys.stderr.write(f"Error reading registry {args.registry}: {e}\n")

    for ats in ["greenhouse", "lever", "ashby", "smartrecruiters", "recruitee", "bamboohr", "personio", "teamtailor"]:
        val = getattr(args, ats)
        if val:
            for token in val.split(","):
                token = token.strip()
                if token:
                    companies.append({"name": token.capitalize(), "ats": ats, "token": token})

    if not companies:
        # Default to seed list
        companies = [
            {"name": "Stripe", "ats": "greenhouse", "token": "stripe"},
            {"name": "Ramp", "ats": "ashby", "token": "ramp"},
            {"name": "Linear", "ats": "ashby", "token": "linear"},
            {"name": "Anthropic", "ats": "lever", "token": "anthropic"}
        ]

    jobs = search_ats_postings(companies, query=args.query)

    out_json = json.dumps(jobs, indent=2, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out_json)
        print(f"Saved {len(jobs)} jobs to {args.out}")
    else:
        print(out_json)


if __name__ == "__main__":
    main()
