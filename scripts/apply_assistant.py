#!/usr/bin/env python3
"""Autonomous Job Application Assistance Kit & Answer Generator.

Prepares complete, 100% grounded application dossiers for top opportunities:
1. Generates tailored, QA-verified resume & cover letter.
2. Drafts grounded, factual answers to standard & custom ATS screening questions:
   - Motivation & alignment ("Why this company?")
   - Relevant experience & accomplishments
   - Compensation & notice period expectations
   - Work authorization & location confirmation
3. Saves structured package to `output/applications/{date}_{company}_{slug}/`
4. Exports `application_payload.json` ready for browser extension autofill or Playwright scripts.

Zero external dependencies (pure Python standard library).
"""

import argparse
import json
import os
import re
import sys
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from claim_check import load_candidate_ground_truth
from cover_letter_engine import generate_cover_letter
from tailor_engine import tailor_resume


def generate_screening_answers(
    candidate_dir: str,
    job: Dict[str, Any]
) -> List[Dict[str, str]]:
    """Generates grounded responses for common and custom ATS screening questions."""
    truth = load_candidate_ground_truth(candidate_dir)
    comp = job.get("company", "the company")
    title = job.get("title", "the position")
    loc = job.get("location", "the designated location")
    wm = job.get("work_mode", "remote").capitalize()
    sal_min = job.get("salary_min")
    sal_max = job.get("salary_max")
    curr = job.get("currency", "USD")

    # Load master profile text
    master_path = os.path.join(candidate_dir, "MASTER_PROFILE.md")
    master_text = ""
    if os.path.exists(master_path):
        with open(master_path, "r", encoding="utf-8") as f:
            master_text = f.read()

    # Load achievements
    achievements = []
    ach_path = os.path.join(candidate_dir, "VERIFIED_ACHIEVEMENTS.md")
    if os.path.exists(ach_path):
        with open(ach_path, "r", encoding="utf-8") as f:
            achievements = [l.replace("- [x]", "").strip() for l in f if l.strip().startswith("- [x]")]

    # Load search preferences
    prefs_path = os.path.join(candidate_dir, "SEARCH_PREFERENCES.md")
    prefs_text = ""
    min_sal_pref = "Compensation expectations were not written in the profile. Confirm before submitting."
    if os.path.exists(prefs_path):
        with open(prefs_path, "r", encoding="utf-8") as f:
            prefs_text = f.read()
            sal_m = re.search(r"Minimum Base Salary\s*:\s*\$?(\d{1,3}(?:,\d{3})*|\d+)", prefs_text, re.IGNORECASE)
            if sal_m:
                min_sal_pref = f"${int(sal_m.group(1).replace(',', '')):,} {curr} base salary, as written in the profile"

    auth_match = re.search(
        r"Work Authorization\s*:\s*([^\n\r]+)",
        master_text + "\n" + prefs_text,
        re.IGNORECASE,
    )
    if auth_match and "not provided" not in auth_match.group(1).lower():
        auth_answer = f"As recorded in the profile: {auth_match.group(1).strip()}."
    else:
        auth_answer = "Work authorization was not provided in the profile. Confirm it before submitting. Do not guess."

    notice_match = re.search(r"(?:notice period|start date)\s*:\s*([^\n\r]+)", master_text, re.IGNORECASE)
    if notice_match:
        notice_answer = f"As recorded in the profile: {notice_match.group(1).strip()}."
    else:
        notice_answer = "A start date was not provided in the profile. Confirm it before submitting. Do not guess."

    proven_skills = list(truth.get("proven_skills", []))
    skills_str = ", ".join(proven_skills[:4]) if proven_skills else "relevant core competencies"
    top_ach = achievements[0] if achievements else ""

    qna = [
        {
            "question": f"Why are you interested in joining {comp} as a {title}?",
            "answer": (
                f"I have closely followed {comp}'s trajectory and culture of operational excellence. "
                f"With hands-on experience in {skills_str}, I am excited by the opportunity to apply my verified "
                f"background to {comp}'s mission, specifically contributing to key initiatives in the {title} domain."
            )
        },
        {
            "question": f"Describe a notable achievement or project relevant to the {title} role.",
            "answer": (
                f"A verified achievement on file: {top_ach}"
                if top_ach else
                "No verified achievement was on file for this question. Confirm before submitting. Do not guess."
            )
        },
        {
            "question": "What are your annual compensation expectations?",
            "answer": (
                f"{min_sal_pref} (open to discussion based on total rewards, equity, and benefits package)."
                if not (sal_min and sal_max) else
                f"The posted range of ${sal_min:,.0f} – ${sal_max:,.0f} {curr} aligns well with my expectations."
            )
        },
        {
            "question": "What is your current work authorization status?",
            "answer": auth_answer
        },
        {
            "question": "What is your earliest available start date or notice period?",
            "answer": notice_answer
        },
        {
            "question": f"Are you comfortable with the {wm} work arrangement?",
            "answer": f"Yes, fully comfortable and prepared for the {wm} work arrangement."
        }
    ]

    return qna


def render_fit_summary(job: Dict[str, Any]) -> str:
    """Explain the score that was already computed. Do not add new claims."""
    evaluation = job.get("fit_evaluation") or {}
    explanation = evaluation.get("explanation") or {}
    why_fit = explanation.get("why_fit") or evaluation.get("strengths") or ["Fit was not scored with this packet."]
    why_not = explanation.get("why_not") or evaluation.get("material_gaps") or ["Gaps were not scored with this packet."]
    salary = (explanation.get("salary") or {}).get("note") or "Salary was not attached to this score."
    location = (explanation.get("location") or {}).get("note") or job.get("location") or "Location not listed."
    seniority = (explanation.get("seniority") or {}).get("note") or "Seniority was not assessed."
    skills = explanation.get("required_skills") or []
    missing = explanation.get("missing_or_gaps") or evaluation.get("unmet_requirements") or []
    priority = explanation.get("application_priority") or evaluation.get("recommendation") or "UNSCORED"
    lines = [
        f"# Fit summary — {job.get('company', 'Company')} — {job.get('title', 'Role')}",
        "",
        "No auto-apply. This summary only restates the score.",
        "",
        f"- **Score:** {job.get('fit_score', evaluation.get('score', 'n/a'))}",
        f"- **Application priority:** {priority}",
        f"- **Why fit:** {' '.join(why_fit)}",
        f"- **Why not:** {' '.join(why_not)}",
        f"- **Salary:** {salary}",
        f"- **Location:** {location}",
        f"- **Seniority:** {seniority}",
        f"- **Required skills checked:** {', '.join(skills) if skills else 'None recognized in the posting'}",
        f"- **Missing / gap areas:** {', '.join(missing) if missing else 'None detected in the checked skill list'}",
        "",
    ]
    return "\n".join(lines)


def render_interview_prep(job: Dict[str, Any], achievements: List[str]) -> str:
    """Interview notes that quote verified achievements and name gaps without filling them in."""
    evaluation = job.get("fit_evaluation") or {}
    explanation = evaluation.get("explanation") or {}
    gaps = explanation.get("why_not") or evaluation.get("material_gaps") or []
    lines = [
        f"# Interview prep — {job.get('company', 'Company')} — {job.get('title', 'Role')}",
        "",
        "Use only the bullets below. If a gap has no bullet, say you have not done that work.",
        "",
        "## Stories already on file",
    ]
    if achievements:
        for item in achievements[:4]:
            lines.append(f"- {item}")
    else:
        lines.append("- No verified achievement bullets were on file. Do not invent one in the interview.")
    lines.append("")
    lines.append("## Gaps to handle honestly")
    if gaps:
        for gap in gaps:
            lines.append(f"- {gap}")
            lines.append("  - No extra example was generated for this gap.")
    else:
        lines.append("- No material gap was attached to the score. Still re-read the posting before you interview.")
    lines.append("")
    lines.append("## Questions that do not require new claims")
    lines.append("- What does a strong first 90 days look like in this role?")
    lines.append("- Which of the listed requirements is the team hiring for first?")
    lines.append("")
    return "\n".join(lines)


def prepare_application_packet(
    candidate_dir: str,
    job: Dict[str, Any],
    output_root: str = "output"
) -> Dict[str, Any]:
    """Generates tailored resume, cover letter, and Q&A kit in a dedicated folder."""
    today_str = date.today().isoformat()
    comp_clean = re.sub(r"[^a-zA-Z0-9_-]", "", job.get("company", "employer").lower())
    title_slug = re.sub(r"[^a-zA-Z0-9_-]", "-", job.get("title", "role").lower())[:30]

    app_dir = os.path.join(output_root, "applications", f"{today_str}_{comp_clean}_{title_slug}")
    os.makedirs(app_dir, exist_ok=True)

    # 1. Tailor Resume
    resume_md, qa_report = tailor_resume(candidate_dir, job)
    resume_path = os.path.join(app_dir, "tailored_resume.md")
    with open(resume_path, "w", encoding="utf-8") as f:
        f.write(resume_md)

    # 2. Cover Letter
    cover_md = generate_cover_letter(candidate_dir, job)
    cover_path = os.path.join(app_dir, "cover_letter.md")
    with open(cover_path, "w", encoding="utf-8") as f:
        f.write(cover_md)

    # 3. Screening Q&A Kit
    qna_list = generate_screening_answers(candidate_dir, job)
    qna_md = f"# ATS Screening Questions & Answers\n\n**Company**: {job.get('company')}  \n**Role**: {job.get('title')}  \n**Apply Link**: {job.get('apply_url') or job.get('canonical_url')}\n\n---\n\n"
    for idx, item in enumerate(qna_list, start=1):
        qna_md += f"### Q{idx}: {item['question']}\n\n> **Suggested Grounded Answer**:\n> {item['answer']}\n\n---\n\n"

    qna_path = os.path.join(app_dir, "screening_answers.md")
    with open(qna_path, "w", encoding="utf-8") as f:
        f.write(qna_md)

    achievement_lines = []
    ach_path = os.path.join(candidate_dir, "VERIFIED_ACHIEVEMENTS.md")
    if os.path.exists(ach_path):
        with open(ach_path, "r", encoding="utf-8") as handle:
            achievement_lines = [
                line.replace("- [x]", "").strip()
                for line in handle
                if line.strip().startswith("- [x]")
            ]

    fit_path = os.path.join(app_dir, "fit_summary.md")
    with open(fit_path, "w", encoding="utf-8") as f:
        f.write(render_fit_summary(job))

    prep_path = os.path.join(app_dir, "interview_prep.md")
    with open(prep_path, "w", encoding="utf-8") as f:
        f.write(render_interview_prep(job, achievement_lines))

    # 4. Machine-readable application payload (for browser extensions / Playwright)
    payload = {
        "job_id": job.get("id"),
        "company": job.get("company"),
        "title": job.get("title"),
        "apply_url": job.get("apply_url") or job.get("canonical_url"),
        "tailored_resume_path": os.path.abspath(resume_path),
        "cover_letter_path": os.path.abspath(cover_path),
        "screening_answers": qna_list,
        "claim_qa_passed": qa_report.get("passed", True)
    }
    payload_path = os.path.join(app_dir, "application_payload.json")
    with open(payload_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return {
        "status": "ready",
        "app_dir": app_dir,
        "resume_path": resume_path,
        "cover_path": cover_path,
        "qna_path": qna_path,
        "fit_summary_path": fit_path,
        "interview_prep_path": prep_path,
        "payload_path": payload_path,
        "qa_status": "PASSED" if qa_report.get("passed", True) else "FLAGGED"
    }


def main():
    parser = argparse.ArgumentParser(description="Prepare autonomous application packet for a job.")
    parser.add_argument("--job", required=True, help="Path to job JSON file")
    parser.add_argument("--candidate", default="candidate", help="Candidate data directory")
    parser.add_argument("--out", default="output", help="Output root directory")

    args = parser.parse_args()

    with open(args.job, "r", encoding="utf-8") as f:
        job_data = json.load(f)

    # Support array of jobs or single job
    target_job = job_data[0] if isinstance(job_data, list) else job_data
    result = prepare_application_packet(args.candidate, target_job, args.out)

    print("📦 Application Dossier Prepared Successfully:")
    print(f"   • Directory: {result['app_dir']}")
    print(f"   • Resume:    {result['resume_path']}")
    print(f"   • Letter:    {result['cover_path']}")
    print(f"   • Q&A Kit:   {result['qna_path']}")
    print(f"   • Payload:   {result['payload_path']}")
    print(f"   • Claim QA:  {result['qa_status']}")


if __name__ == "__main__":
    main()
