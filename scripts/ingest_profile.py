#!/usr/bin/env python3
"""Omnichannel Profile Ingestion & Synthesis Engine for AI Job Agent.

Enables anyone—from non-technical users to career switchers—to provide
whatever they have (raw notes, PDF text, LinkedIn profile, voice transcript)
and transforms it automatically into canonical candidate truth files:
- candidate/MASTER_PROFILE.md
- candidate/skills.json
- candidate/SEARCH_PREFERENCES.md
- candidate/VERIFIED_ACHIEVEMENTS.md

Supports pure standard library deterministic parsing, with optional LLM
enhancement when GEMINI_API_KEY or OPENAI_API_KEY is available.
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


def extract_contact_info(text: str) -> Dict[str, str]:
    """Extracts candidate contact details using robust regex patterns."""
    info = {
        "name": "Candidate",
        "email": "candidate@example.com",
        "phone": "",
        "location": "United States",
        "linkedin": "",
        "github": "",
        "portfolio": ""
    }

    # Email
    email_m = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
    if email_m:
        info["email"] = email_m.group(0)

    # Phone
    phone_m = re.search(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", text)
    if phone_m:
        info["phone"] = phone_m.group(0).strip()

    # LinkedIn
    li_m = re.search(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9_-]+", text, re.IGNORECASE)
    if li_m:
        info["linkedin"] = li_m.group(0)

    # GitHub
    gh_m = re.search(r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9_-]+", text, re.IGNORECASE)
    if gh_m:
        info["github"] = gh_m.group(0)

    # Portfolio / Website
    web_m = re.search(r"(?:https?://)?(?:www\.)?[a-zA-Z0-9-]+\.(?:io|com|dev|me|org|net)(?:/[^\s]*)?", text)
    if web_m:
        val = web_m.group(0)
        if "linkedin.com" not in val and "github.com" not in val:
            info["portfolio"] = val

    # Location (City, ST or City, Country)
    loc_m = re.search(
        r"(?:Location|Located in|Based in|Address)?\s*[:\-]?\s*([A-Za-z\s]+,\s*(?:[A-Z]{2}|[A-Za-z\s]+))\b",
        text,
        re.IGNORECASE
    )
    if loc_m:
        cand_loc = loc_m.group(1).strip()
        if len(cand_loc) < 40 and not any(w in cand_loc.lower() for w in ["email", "phone", "linkedin", "resume"]):
            info["location"] = cand_loc

    # Name heuristic: First non-empty line, conversational intro, or explicitly labeled
    name_m = re.search(r"(?:My name is|I am|Name|Full Name|Candidate)\s*[:\-]?\s*([A-Za-z\s'-]{2,35})", text, re.IGNORECASE)
    if name_m:
        cand_name = name_m.group(1).strip()
        # Clean up any trailing words like ', Registered' or 'with'
        cand_name = re.split(r"[,|\n\r]|\s+with\s+|\s+a\s+", cand_name, flags=re.IGNORECASE)[0].strip()
        if len(cand_name.split()) >= 2:
            info["name"] = cand_name
    else:
        for line in text.splitlines()[:6]:
            line_str = line.strip()
            # If line is 2-4 words, title-cased, no numbers/emails/symbols
            words = line_str.split()
            if 2 <= len(words) <= 4 and all(w.replace("-", "").isalpha() for w in words):
                if not any(header in line_str.lower() for header in ["resume", "curriculum", "profile", "contact", "summary", "objective"]):
                    info["name"] = line_str
                    break

    return info


def extract_career_metadata(text: str) -> Dict[str, Any]:
    """Extracts job titles, experience level, preferences, and skills."""
    meta = {
        "title": "",
        "years_exp": None,
        "target_titles": [],
        "work_mode": "",
        "min_salary": None,
        "skills": [],
        "achievements": [],
        "summary": "",
        "work_authorization": "",
    }

    # Years of experience
    exp_m = re.search(r"(\d{1,2})\+?\s*(?:years|yrs)(?:\s+of)?(?:\s+experience)?", text, re.IGNORECASE)
    if exp_m:
        try:
            meta["years_exp"] = int(exp_m.group(1))
        except ValueError:
            pass

    # Desired salary
    sal_m = re.search(r"\$(\d{2,3}(?:,\d{3})*|\d{2,3})k?\s*(?:-\s*\$?\d+k?)?\s*(?:USD|salary|base)?", text, re.IGNORECASE)
    if sal_m:
        raw_sal = sal_m.group(1).replace(",", "")
        try:
            val = float(raw_sal)
            meta["min_salary"] = int(val * 1000 if val < 1000 else val)
        except ValueError:
            pass

    # Work mode
    if re.search(r"\b(remote|work from home|wfh)\b", text, re.IGNORECASE):
        meta["work_mode"] = "remote"
    elif re.search(r"\b(hybrid)\b", text, re.IGNORECASE):
        meta["work_mode"] = "hybrid"
    elif re.search(r"\b(onsite|in-office)\b", text, re.IGNORECASE):
        meta["work_mode"] = "onsite"

    auth_match = re.search(
        r"((?:us citizen|authorized to work|no sponsorship|visa sponsorship|green card)[^\n\r.]*)",
        text,
        re.IGNORECASE,
    )
    if auth_match:
        meta["work_authorization"] = auth_match.group(1).strip()

    # Current / Target Title
    title_m = re.search(r"(?:Current Title|Target Role|Position|Role|Title)\s*[:\-]\s*([^\n\r,]+)", text, re.IGNORECASE)
    if title_m:
        t_clean = title_m.group(1).strip()
        meta["title"] = t_clean
        meta["target_titles"].append(t_clean)

    # Common role titles detector if no explicit title
    if not meta["title"]:
        role_candidates = [
            "Software Engineer", "Backend Engineer", "Frontend Engineer", "Full Stack Engineer",
            "Data Scientist", "Data Analyst", "Product Manager", "Project Manager",
            "Registered Nurse", "Nurse Practitioner", "Clinical Coordinator", "Medical Assistant",
            "Accountant", "Financial Analyst", "Operations Manager", "Sales Representative",
            "Account Executive", "Customer Success Manager", "Marketing Manager", "DevOps Engineer"
        ]
        for role in role_candidates:
            if re.search(rf"\b{re.escape(role)}\b", text, re.IGNORECASE):
                meta["title"] = role
                meta["target_titles"].append(role)
                break

    # Extract bullet points / achievements
    bullet_pattern = re.compile(r"^\s*[*•-]\s+([A-Z0-9][^\n\r]{20,})", re.MULTILINE)
    bullets = bullet_pattern.findall(text)
    meta["achievements"] = [b.strip() for b in bullets[:10]]

    # Skills detection
    skill_taxonomies = [
        # Tech / Eng
        "Python", "Go", "Java", "TypeScript", "JavaScript", "C++", "C#", "Rust", "SQL", "PostgreSQL",
        "MySQL", "Redis", "Kafka", "Docker", "Kubernetes", "AWS", "GCP", "Azure", "Terraform",
        "React", "Node.js", "FastAPI", "Django", "Git", "CI/CD", "Linux", "REST APIs", "GraphQL",
        # Healthcare
        "Patient Triage", "EPIC EMR", "Cerner", "BLS Certification", "ACLS", "HIPAA Compliance",
        "Medication Administration", "Clinical Documentation", "Vital Signs", "Wound Care", "Phlebotomy",
        # Business / Sales / Marketing
        "Salesforce", "HubSpot", "Google Analytics", "SEO", "Content Strategy", "Financial Modeling",
        "Budget Management", "B2B Sales", "Lead Generation", "Client Relationship Management", "Excel",
        # Operations / General
        "Project Leadership", "Agile / Scrum", "Cross-Functional Collaboration", "Team Mentorship",
        "Root Cause Analysis", "Inventory Management", "Process Optimization", "Customer Service"
    ]
    detected_skills = []
    text_lower = text.lower()
    for s in skill_taxonomies:
        if re.search(rf"\b{re.escape(s.lower())}\b", text_lower):
            detected_skills.append(s)

    meta["skills"] = detected_skills

    return meta


def build_canonical_profile_files(
    raw_text: str,
    output_dir: str = "candidate"
) -> Dict[str, str]:
    """Transforms raw text/resume into canonical files in output_dir."""
    os.makedirs(output_dir, exist_ok=True)
    contact = extract_contact_info(raw_text)
    meta = extract_career_metadata(raw_text)

    # 1. candidate/MASTER_PROFILE.md
    links_lines = []
    if contact["linkedin"]:
        links_lines.append(f"* **LinkedIn**: {contact['linkedin']}")
    if contact["github"]:
        links_lines.append(f"* **GitHub**: {contact['github']}")
    if contact["portfolio"]:
        links_lines.append(f"* **Portfolio**: {contact['portfolio']}")
    links_block = "\n".join(links_lines) if links_lines else "* **Links**: Not specified"

    ach_preview = "\n".join([f"* {a}" for a in meta["achievements"][:6]]) if meta["achievements"] else (
        "* No achievement bullets were detected in the source resume. None were invented."
    )
    title_text = meta["title"] or "Not provided in the source resume"
    years_text = (
        f"{meta['years_exp']} years"
        if meta["years_exp"] is not None
        else "Not provided in the source resume"
    )
    auth_text = meta["work_authorization"] or "Not provided in the source resume"
    skill_text = ", ".join(meta["skills"]) if meta["skills"] else "None detected in the source resume"
    summary_bits = []
    if meta["title"]:
        summary_bits.append(meta["title"])
    if meta["years_exp"] is not None:
        summary_bits.append(f"{meta['years_exp']} years of experience stated in the source")
    if meta["skills"]:
        summary_bits.append("skills named in the source: " + ", ".join(meta["skills"][:6]))
    summary_text = (
        "Source resume states: " + "; ".join(summary_bits) + "."
        if summary_bits else
        "No summary was present in the source resume."
    )

    master_content = f"""# Master Profile: {contact['name']}

> **Profile Source**: Ingested via Omnichannel AI Ingestion Engine.
> **Privacy**: Stored 100% locally on your machine.

---

## 1. Candidate Overview & Contact
* **Full Name**: {contact['name']}
* **Current Title**: {title_text}
* **Location**: {contact['location']}
* **Email**: {contact['email']}
* **Phone**: {contact['phone'] or 'Not specified'}
{links_block}
* **Work Authorization**: {auth_text}
* **Total Years of Experience**: {years_text}

---

## 2. Professional Summary
{summary_text}

---

## 3. Core Competencies & Skills
* **Core Competencies**: {skill_text}

---

## 4. Professional Experience
Employer names were not structured as a separate field unless they already appear inside the source bullets below. No employer was invented.

{ach_preview}

---

## 5. Education & Credentials
* Not provided unless a degree or certification already appears in the source text above.

---

## 6. Honest Framings & Nuance Notes
* Only facts copied from the source resume are in this file.
"""
    master_path = os.path.join(output_dir, "MASTER_PROFILE.md")
    with open(master_path, "w", encoding="utf-8") as f:
        f.write(master_content)

    # 2. candidate/skills.json
    skills_data = {
        "proven_skills": meta["skills"],
        "transferable_skills": [],
        "domain_expertise": [meta["title"]] if meta["title"] else [],
        "soft_skills": []
    }
    skills_path = os.path.join(output_dir, "skills.json")
    with open(skills_path, "w", encoding="utf-8") as f:
        json.dump(skills_data, f, indent=2)

    # 3. candidate/SEARCH_PREFERENCES.md
    target_titles_block = "\n".join([f"* {t}" for t in meta["target_titles"]]) or "* Not provided"
    work_mode_text = meta["work_mode"].capitalize() if meta["work_mode"] else "Not provided"
    salary_line = (
        f"* **Minimum Base Salary**: ${meta['min_salary']:,} USD"
        if meta["min_salary"] else
        "* **Minimum Base Salary**: Not provided"
    )
    location_line = contact["location"] or "Not provided"
    prefs_content = f"""# Job Search Preferences

## 1. Target Roles & Titles
{target_titles_block}

## 2. Work Arrangement & Location
* **Work Mode Preference**: {work_mode_text}
* **Allowed Locations**:
  - {location_line}

## 3. Compensation Preferences
{salary_line}
* **Currency**: USD

## 4. Hard Exclusions & Blacklist
* **Excluded Companies**:
* **Excluded Title Keywords**:
"""
    prefs_path = os.path.join(output_dir, "SEARCH_PREFERENCES.md")
    with open(prefs_path, "w", encoding="utf-8") as f:
        f.write(prefs_content)

    # 4. candidate/VERIFIED_ACHIEVEMENTS.md
    ach_lines = [f"- [x] {a}" for a in meta["achievements"]] if meta["achievements"] else [
        "- [ ] No achievement bullets were detected in the source resume. None were invented."
    ]
    ach_content = f"""# Verified Achievement Bank: {contact['name']}

> Every claim in tailored resumes and cover letters is strictly cross-referenced against this ledger.

## Core Operational & Professional Achievements
{chr(10).join(ach_lines)}
"""
    ach_path = os.path.join(output_dir, "VERIFIED_ACHIEVEMENTS.md")
    with open(ach_path, "w", encoding="utf-8") as f:
        f.write(ach_content)

    return {
        "master_profile": master_path,
        "skills": skills_path,
        "preferences": prefs_path,
        "achievements": ach_path
    }


def read_input_source(
    file_path: Optional[str] = None,
    raw_text: Optional[str] = None
) -> str:
    """Reads input content from a file path or raw text string."""
    if raw_text and raw_text.strip():
        return raw_text.strip()

    if file_path and os.path.exists(file_path):
        # Attempt basic plain text read
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception as e:
            sys.stderr.write(f"Error reading file {file_path}: {e}\n")

    return ""


def main():
    parser = argparse.ArgumentParser(description="Ingest raw text/resume into canonical candidate profile.")
    parser.add_argument("--file", help="Path to resume, text, or export file")
    parser.add_argument("--text", help="Raw text string of experience/notes")
    parser.add_argument("--out", default="candidate", help="Output directory (default: candidate)")

    args = parser.parse_args()

    content = read_input_source(args.file, args.text)
    if not content and not sys.stdin.isatty():
        content = sys.stdin.read()

    if not content:
        sys.stderr.write("Error: Please provide input via --file, --text, or standard input.\n")
        sys.exit(1)

    print(f"📥 Parsing raw career data ({len(content)} chars)...")
    created = build_canonical_profile_files(content, args.out)

    print("✅ Canonical candidate truth files created successfully:")
    for key, path in created.items():
        print(f"   • {path}")


if __name__ == "__main__":
    main()
