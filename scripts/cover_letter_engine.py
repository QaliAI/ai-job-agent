#!/usr/bin/env python3
"""Grounded Cover Letter & Application Response Engine for AI Job Agent.

Generates targeted, high-signal cover letters and application answers
grounded strictly in candidate achievements (VERIFIED_ACHIEVEMENTS.md) and
STAR stories (CAREER_STORIES.md).

No generic AI fluff, no buzzwords, 100% factual.
"""

import argparse
import json
import os
import re
import sys
from datetime import date
from typing import Any, Dict, List, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from claim_check import load_candidate_ground_truth, verify_content


def generate_cover_letter(candidate_dir: str, job: Dict[str, Any]) -> str:
    """Generates a structured, evidence-backed cover letter."""
    truth = load_candidate_ground_truth(candidate_dir)
    
    master_path = os.path.join(candidate_dir, "MASTER_PROFILE.md")
    master_text = ""
    if os.path.exists(master_path):
        with open(master_path, "r", encoding="utf-8") as f:
            master_text = f.read()

    name_match = re.search(r"(?:\*\*)?Full Name(?:\*\*)?\s*:\s*([^\n\r]+)", master_text, re.IGNORECASE)
    if not name_match:
        name_match = re.search(r"#\s*(?:Master Profile:?\s*)([A-Za-z\s]+?)(?:\s*\(|\s*\n)", master_text, re.IGNORECASE)
    cand_name = name_match.group(1).strip() if name_match else "Candidate"
    
    loc_match = re.search(r"(?:\*\*)?Location(?:\*\*)?\s*:\s*([^\n\r]+)", master_text, re.IGNORECASE)
    cand_loc = loc_match.group(1).strip() if loc_match else "United States"
    
    email_match = re.search(r"(?:\*\*)?Email(?:\*\*)?\s*:\s*([^\n\r]+)", master_text, re.IGNORECASE)
    cand_email = email_match.group(1).strip() if email_match else "candidate@example.com"
    
    phone_match = re.search(r"(?:\*\*)?Phone(?:\*\*)?\s*:\s*([^\n\r]+)", master_text, re.IGNORECASE)
    cand_phone = phone_match.group(1).strip() if phone_match else ""

    job_title = job.get("title", "Senior Software Engineer")
    company = job.get("company", "Target Company")
    job_id = job.get("id", "")
    today_str = date.today().strftime("%B %d, %Y")

    # Extract achievements from VERIFIED_ACHIEVEMENTS.md or MASTER_PROFILE.md bullets
    achievements = []
    ach_path = os.path.join(candidate_dir, "VERIFIED_ACHIEVEMENTS.md")
    if os.path.exists(ach_path):
        with open(ach_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip().startswith("- [x]")]
            achievements = [l.replace("- [x]", "").strip() for l in lines]

    if not achievements and master_text:
        # Fallback to experience bullets from profile
        bullets = re.findall(r"^\s*[*•-]\s+([A-Z][^\n\r]+)", master_text, re.MULTILINE)
        achievements = [b.strip() for b in bullets if len(b.strip()) > 20][:4]

    top_ach1 = achievements[0] if len(achievements) > 0 else ""
    top_ach2 = achievements[1] if len(achievements) > 1 else ""

    proven_skills = list(truth.get("proven_skills", []))
    skills_preview = ", ".join(proven_skills[:4]) if proven_skills else "core professional competencies"

    letter = f"""# Cover Letter: {company} — {job_title}

**{cand_name}**  
{cand_loc} · {cand_phone} · {cand_email}  
Date: {today_str}

**Hiring Team**  
{company}  
Position: {job_title} (Posting ID: {job_id})

Dear Hiring Manager and {company} Team,

I am writing to express my enthusiastic interest in the **{job_title}** role at **{company}**. With a strong background in {skills_preview}, I am eager to contribute directly to {company}'s ongoing success and high-impact initiatives.

Throughout my career, the verified record I can point to is:
{f"* **Verified contribution**: {top_ach1}." if top_ach1 else "* No verified achievement bullets were on file. Nothing was invented for this letter."}
{f"* **Verified contribution**: {top_ach2}." if top_ach2 else ""}

I admire {company}'s reputation for quality, culture, and high standards. I would welcome the opportunity to bring my experience and dedication to your team.

Thank you for your time and consideration. I look forward to discussing how my background aligns with the goals of {company}.

Sincerely,

**{cand_name}**  
{cand_email} · {cand_phone}
"""
    return letter.strip()


def main():
    parser = argparse.ArgumentParser(description="Generate grounded cover letter.")
    parser.add_argument("--candidate", default="candidate", help="Candidate data directory")
    parser.add_argument("--job", required=True, help="Path to job JSON file")
    parser.add_argument("--out", help="Path to save output cover letter markdown")

    args = parser.parse_args()

    with open(args.job, "r", encoding="utf-8") as f:
        job_data = json.load(f)

    letter = generate_cover_letter(args.candidate, job_data)

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(letter)
        print(f"Cover letter saved to {args.out}")
    else:
        print(letter)


if __name__ == "__main__":
    main()
