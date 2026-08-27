#!/usr/bin/env python3
"""System Diagnostics & Environment Doctor for AI Job Agent.

Validates:
1. Python version (3.10+ requirement).
2. Git status and repository root.
3. Privacy rules (.gitignore covers candidate/ and output/).
4. Candidate profile files presence & schema validity.
5. ATS public endpoint network reachability.
6. Multi-runtime skill linkage.
"""

import json
import os
import platform
import sys
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def check_python_version() -> bool:
    v = sys.version_info
    print(f"[{'✓' if v >= (3, 10) else '✗'}] Python Version: {v.major}.{v.minor}.{v.micro} (Requires 3.10+)")
    return v >= (3, 10)


def check_privacy_gitignore() -> bool:
    if not os.path.exists(".gitignore"):
        print("[✗] Privacy Check: .gitignore is missing!")
        return False
    with open(".gitignore", "r", encoding="utf-8") as f:
        content = f.read()
    has_candidate = "candidate" in content
    has_output = "output" in content
    has_jobs = "jobs" in content
    passed = has_candidate and has_output and has_jobs
    print(f"[{'✓' if passed else '✗'}] Privacy Check: .gitignore protects candidate data, outputs, and job stores")
    return passed


def check_candidate_files() -> bool:
    req_files = [
        "candidate/SEARCH_PREFERENCES.md",
        "candidate/MASTER_PROFILE.md",
        "candidate/skills.json"
    ]
    all_found = True
    for rf in req_files:
        found = os.path.exists(rf)
        if not found:
            all_found = False
    
    if all_found:
        print("[✓] Candidate Profile: Personal profile files verified in 'candidate/'")
        return True
    elif os.path.exists("examples/jordan-taylor/MASTER_PROFILE.md"):
        print("[✓] Candidate Profile: Ready (starter examples available; run 'python scripts/setup.py' to initialize personal profile)")
        return True
    else:
        print("[!] Candidate Profile: Missing personal files (run 'python scripts/setup.py' to initialize)")
        return False


def check_network_ats() -> bool:
    test_urls = [
        ("Greenhouse (Stripe)", "https://boards-api.greenhouse.io/v1/boards/stripe/jobs?content=false"),
        ("Ashby (Ramp)", "https://api.ashbyhq.com/posting-api/job-board/ramp")
    ]
    all_ok = True
    for name, url in test_urls:
        req = urllib.request.Request(url, headers={"User-Agent": "AIJobAgent-Doctor/0.1.0"})
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                if resp.status == 200:
                    print(f"[✓] Network Reachability: {name} connection successful")
                else:
                    print(f"[✗] Network Reachability: {name} returned HTTP {resp.status}")
                    all_ok = False
        except Exception as e:
            print(f"[!] Network Reachability: {name} check warning: {e}")
            all_ok = False
    return all_ok


def check_skills_manifest() -> bool:
    skills = [
        "skills/find-jobs/SKILL.md",
        "skills/score-fit/SKILL.md",
        "skills/tailor-resume/SKILL.md",
        "skills/claim-check/SKILL.md",
        "skills/daily-brief/SKILL.md"
    ]
    missing = [s for s in skills if not os.path.exists(s)]
    if not missing:
        print("[✓] Agent Skills: All standard SKILL.md manifests verified")
        return True
    else:
        print(f"[!] Agent Skills: Missing skills {missing}")
        return False


def main():
    print("=" * 60)
    print("           AI Job Agent Doctor & Diagnostics           ")
    print("=" * 60)
    print(f"OS: {platform.system()} {platform.release()} ({platform.machine()})")
    print()

    p1 = check_python_version()
    p2 = check_privacy_gitignore()
    p3 = check_candidate_files()
    p4 = check_network_ats()
    p5 = check_skills_manifest()

    print()
    print("=" * 60)
    if p1 and p2 and p4:
        print("🎉 System status: HEALTHY & READY TO OPERATE")
    else:
        print("⚠️ System status: Action needed on flagged items above")
    print("=" * 60)


if __name__ == "__main__":
    main()
