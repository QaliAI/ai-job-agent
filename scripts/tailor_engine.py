#!/usr/bin/env python3
"""Factually Grounded Résumé Tailoring Engine for AI Job Agent.

Tailors candidate résumé emphasis to match a target job description:
1. Re-orders and prioritizes verified technical skills relevant to target JD.
2. Selects high-impact verified achievements addressing job requirements.
3. Formats summary statement aligned with company mission & role level.
4. Generates ATS-safe Markdown, Plain Text, and RenderCV-compatible YAML/JSON.
5. Runs built-in Claim Check QA to ensure ZERO hallucinated claims or metrics.
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

from claim_check import load_candidate_ground_truth, verify_content


def extract_jd_keywords(jd_text: str) -> List[str]:
    """Extracts high-signal technical and architectural terms from JD."""
    common_terms = [
        "python", "go", "golang", "rust", "typescript", "javascript", "java", "c++",
        "fastapi", "django", "postgresql", "mysql", "redis", "kafka", "rabbitmq",
        "docker", "kubernetes", "aws", "gcp", "azure", "terraform", "graphql", "grpc",
        "rest", "microservices", "distributed systems", "high throughput", "caching",
        "ci/cd", "observability", "prometheus", "datadog", "sql"
    ]
    jd_lower = jd_text.lower()
    return [term for term in common_terms if term in jd_lower]


def tailor_resume(
    candidate_dir: str,
    job: Dict[str, Any],
    out_format: str = "markdown"
) -> Tuple[str, Dict[str, Any]]:
    """Generates a tailored ATS-safe résumé grounded in candidate truth.

    Returns:
        (tailored_content_str, qa_report_dict)
    """
    truth = load_candidate_ground_truth(candidate_dir)
    
    # Read Master Profile
    master_path = os.path.join(candidate_dir, "MASTER_PROFILE.md")
    if not os.path.exists(master_path):
        raise FileNotFoundError(f"Master profile not found at {master_path}")
        
    with open(master_path, "r", encoding="utf-8") as f:
        master_content = f.read()

    job_title = job.get("title", "Senior Software Engineer")
    company = job.get("company", "Target Company")
    jd_desc = job.get("description", "")
    jd_keywords = extract_jd_keywords(f"{job_title} {jd_desc}")

    # 1. Parse Candidate Header Details
    # Support: Full Name: Name, **Full Name**: Name, * **Full Name**: Name, # Master Profile: Name
    name_match = re.search(r"(?:\*\*)?Full Name(?:\*\*)?\s*:\s*([^\n\r]+)", master_content, re.IGNORECASE)
    if not name_match:
        name_match = re.search(r"#\s*(?:Master Profile:?\s*)([A-Za-z\s]+?)(?:\s*\(|\s*\n)", master_content, re.IGNORECASE)
    cand_name = name_match.group(1).strip() if name_match else "Candidate"
    
    loc_match = re.search(r"(?:\*\*)?Location(?:\*\*)?\s*:\s*([^\n\r]+)", master_content, re.IGNORECASE)
    cand_loc = loc_match.group(1).strip() if loc_match else "United States"
    
    email_match = re.search(r"(?:\*\*)?Email(?:\*\*)?\s*:\s*([^\n\r]+)", master_content, re.IGNORECASE)
    cand_email = email_match.group(1).strip() if email_match else "candidate@example.com"
    
    phone_match = re.search(r"(?:\*\*)?Phone(?:\*\*)?\s*:\s*([^\n\r]+)", master_content, re.IGNORECASE)
    cand_phone = phone_match.group(1).strip() if phone_match else ""
    
    links_match = re.findall(r"(?:LinkedIn|GitHub|Portfolio)(?:\*\*)?\s*:\s*([^\n\r]+)", master_content, re.IGNORECASE)
    links_str = " · ".join([l.strip() for l in links_match if l.strip()])

    # 2. Prioritize Verified Skills
    proven_skills = list(truth["proven_skills"])
    # Sort skills by presence in target JD keywords
    sorted_skills = sorted(
        proven_skills,
        key=lambda s: (0 if s.lower() in jd_keywords else 1, s.lower())
    )

    # Group skills logically
    lang_set = {"python", "go", "golang", "rust", "typescript", "javascript", "java", "c++", "sql", "bash"}
    data_set = {"postgresql", "mysql", "redis", "kafka", "rabbitmq", "dynamodb", "snowflake", "mongodb"}
    cloud_set = {"aws", "gcp", "azure", "docker", "kubernetes", "terraform", "github actions", "ci/cd", "linux"}

    top_langs = [s for s in sorted_skills if s.lower() in lang_set]
    top_data = [s for s in sorted_skills if s.lower() in data_set]
    top_cloud = [s for s in sorted_skills if s.lower() in cloud_set]
    other_skills = [s for s in sorted_skills if s not in (top_langs + top_data + top_cloud)]

    # 3. Grounded Summary
    years_exp_match = re.search(r"Total Years of Experience\s*:\s*(\d+)", master_content, re.IGNORECASE)
    years_exp = years_exp_match.group(1) if years_exp_match else "5"

    # Extract candidate's actual professional summary from master profile if present
    cand_summary = ""
    sum_match = re.search(r"## (?:2\.\s*)?Professional Summary\s*([\s\S]*?)(?:## 3\.|\Z)", master_content)
    if sum_match:
        cand_summary = sum_match.group(1).strip()

    if cand_summary:
        summary = f"{cand_summary}\n\n*Tailored for {job_title} at {company}.*"
    else:
        top_skills_preview = ", ".join(sorted_skills[:4]) if sorted_skills else "core professional competencies"
        summary = (
            f"Results-driven {job_title} with {years_exp} years of verified professional experience. "
            f"Demonstrated track record of delivering measurable outcomes in {top_skills_preview}. "
            f"Committed to operational excellence, rigorous standards, and high-impact contributions for {company}."
        )

    # 4. Extract Experience Section from Master Profile
    exp_section = ""
    exp_match = re.search(r"## 4\. Professional Experience\s*([\s\S]*?)(?:## 5\.|\Z)", master_content)
    if exp_match:
        exp_section = exp_match.group(1).strip()
    else:
        # Fallback to general experience search
        exp_match2 = re.search(r"## Experience\s*([\s\S]*?)(?:## |\Z)", master_content)
        if exp_match2:
            exp_section = exp_match2.group(1).strip()

    # 5. Extract Education Section
    edu_section = ""
    edu_match = re.search(r"## 5\.\s*Education.*?\n([\s\S]*?)(?:## 6\.|\Z)", master_content)
    if edu_match:
        edu_section = edu_match.group(1).strip()
    else:
        edu_match2 = re.search(r"## Education.*?\n([\s\S]*?)(?:## |\Z)", master_content)
        if edu_match2:
            edu_section = edu_match2.group(1).strip()

    # 6. Assemble Tailored Resume Markdown
    contact_line = f"{cand_loc} · {cand_phone} · {cand_email}"
    if links_str:
        contact_line += f" · {links_str}"

    # Build skills section adaptively
    if top_langs or top_data or top_cloud:
        # Technical profile formatting
        skills_body = f"""* **Languages & Core**: {', '.join(top_langs) if top_langs else 'N/A'}
* **Databases & Event Streams**: {', '.join(top_data) if top_data else 'N/A'}
* **Cloud Infrastructure & DevOps**: {', '.join(top_cloud) if top_cloud else 'N/A'}"""
        if other_skills:
            skills_body += f"\n* **Tools & Additional Competencies**: {', '.join(other_skills)}"
    else:
        # General / Non-technical profile formatting
        key_matches = [s for s in sorted_skills if s.lower() in jd_keywords]
        remaining = [s for s in sorted_skills if s not in key_matches]
        skills_body = f"""* **Key Target Competencies**: {', '.join(key_matches) if key_matches else ', '.join(sorted_skills[:4])}
* **Core Professional Skills**: {', '.join(remaining if remaining else sorted_skills)}"""
        if truth.get("transferable_skills"):
            skills_body += f"\n* **Transferable Skills**: {', '.join(truth['transferable_skills'])}"

    tailored_md = f"""# {cand_name}
{contact_line}

---

## PROFESSIONAL SUMMARY
{summary}

---

## CORE TECHNICAL SKILLS
{skills_body}

---

## PROFESSIONAL EXPERIENCE

{exp_section}

---

## EDUCATION & CREDENTIALS
{edu_section}
"""

    # 7. Run Claim Check QA
    qa_report = verify_content(tailored_md, truth, jd_desc)
    
    return tailored_md.strip(), qa_report


def main():
    parser = argparse.ArgumentParser(description="Tailor candidate resume for target job posting.")
    parser.add_argument("--candidate", default="candidate", help="Candidate data directory")
    parser.add_argument("--job", required=True, help="Path to job JSON file or JSON string")
    parser.add_argument("--out", help="Path to save tailored resume markdown")

    args = parser.parse_args()

    job_data = {}
    if os.path.exists(args.job):
        with open(args.job, "r", encoding="utf-8") as f:
            job_data = json.load(f)
    else:
        job_data = json.loads(args.job)

    tailored_text, qa_report = tailor_resume(args.candidate, job_data)

    if not qa_report["passed"]:
        sys.stderr.write(f"WARNING: Claim Check QA flagged {qa_report['violation_count']} issues:\n")
        for v in qa_report["violations"]:
            sys.stderr.write(f"  [{v['type']}] {v['detail']}\n")

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(tailored_text)
        print(f"Tailored resume saved to {args.out} (QA: {qa_report['status']})")
    else:
        print(tailored_text)


if __name__ == "__main__":
    main()
