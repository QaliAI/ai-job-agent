#!/usr/bin/env python3
"""Explainable, Rubric-Based Fit Scoring Engine for AI Job Agent.

Calculates transparent candidate-to-job fit without ungrounded LLM 'guess percentages'.
Evaluates 6 weighted dimensions:
1. Title & Role Relevance (25%)
2. Core Required Skills (25%)
3. Seniority & Experience (15%)
4. Domain & Industry Fit (15%)
5. Location & Work Arrangement (10%)
6. Preferred Qualifications & Nice-to-Haves (10%)

Outputs:
- Score (0–100)
- Confidence (High / Medium / Low)
- Recommendation (APPLY / CONSIDER / SKIP)
- Strengths & Proven Matches
- Material Gaps & Unmet Requirements
- Detailed Rationale
"""

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


DEFAULT_WEIGHTS = {
    "title_and_role_relevance": 0.25,
    "core_required_skills": 0.25,
    "experience_seniority": 0.15,
    "domain_industry_fit": 0.15,
    "location_and_work_mode": 0.10,
    "preferred_qualifications": 0.10
}


def load_candidate_profile(candidate_dir: str = "candidate") -> Dict[str, Any]:
    """Loads all structured facts from candidate directory."""
    profile_data: Dict[str, Any] = {
        "title": "",
        "years_exp": None,
        "location": "",
        "work_mode_pref": "",
        "proven_skills": [],
        "transferable_skills": [],
        "domain_expertise": [],
        "achievements": [],
        "target_titles": []
    }

    # Load skills.json
    skills_path = os.path.join(candidate_dir, "skills.json")
    if os.path.exists(skills_path):
        try:
            with open(skills_path, "r", encoding="utf-8") as f:
                sdata = json.load(f)
                profile_data["proven_skills"] = sdata.get("proven_skills", [])
                profile_data["transferable_skills"] = sdata.get("transferable_skills", [])
                profile_data["domain_expertise"] = sdata.get("domain_expertise", [])
        except Exception as e:
            sys.stderr.write(f"Error loading {skills_path}: {e}\n")

    # Load MASTER_PROFILE.md
    master_path = os.path.join(candidate_dir, "MASTER_PROFILE.md")
    if os.path.exists(master_path):
        try:
            with open(master_path, "r", encoding="utf-8") as f:
                m_text = f.read()
                
            def field(label: str) -> Optional[str]:
                match = re.search(
                    rf"(?:\*\*)?{re.escape(label)}(?:\*\*)?\s*:\s*([^\n\r]+)",
                    m_text,
                    re.IGNORECASE,
                )
                if not match:
                    return None
                return match.group(1).strip().strip("*").strip()

            title_value = field("Current / Target Title") or field("Current Title")
            if title_value:
                profile_data["title"] = title_value
            name_value = field("Full Name")
            if name_value:
                profile_data["name"] = name_value
            years_value = field("Total Years of Experience")
            if years_value:
                years_match = re.search(r"(\d+)", years_value)
                if years_match:
                    profile_data["years_exp"] = int(years_match.group(1))
            location_value = field("Location")
            if location_value:
                profile_data["location"] = location_value

        except Exception as e:
            sys.stderr.write(f"Error loading {master_path}: {e}\n")

    # Load SEARCH_PREFERENCES.md
    prefs_path = os.path.join(candidate_dir, "SEARCH_PREFERENCES.md")
    if os.path.exists(prefs_path):
        try:
            with open(prefs_path, "r", encoding="utf-8") as f:
                p_text = f.read()
            titles = re.findall(r"[-*]\s*([A-Za-z0-9\s\(\)/,]+)", p_text)
            profile_data["target_titles"] = [t.strip() for t in titles if len(t.strip()) > 3]
        except Exception as e:
            sys.stderr.write(f"Error loading {prefs_path}: {e}\n")

    return profile_data


def _title_match_score(title_lower: str, titles: List[str], current: int, full_match: int) -> int:
    """Score how completely a posting title covers a configured title list."""
    score = current
    for target in titles:
        words = [word.lower() for word in str(target).split() if len(word) > 2]
        if not words:
            continue
        matches = sum(1 for word in words if word in title_lower)
        if matches == len(words):
            return full_match
        if matches > 0:
            ratio = matches / max(len(words), 1)
            score = max(score, int(50 + ratio * 40))
    return score


def _salary_explanation(job: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    salary_min = job.get("salary_min")
    salary_max = job.get("salary_max")
    currency = job.get("currency") or "USD"
    expectation = profile.get("salary_expectation") or {}
    if not salary_min and not salary_max:
        return {
            "known": False,
            "min": None,
            "max": None,
            "currency": currency,
            "note": "Salary is not listed on this posting.",
        }
    if salary_min and salary_max:
        note = f"${salary_min:,.0f} – ${salary_max:,.0f} {currency}"
    elif salary_min:
        note = f"From ${salary_min:,.0f} {currency}"
    else:
        note = f"Up to ${salary_max:,.0f} {currency}"
    expected_min = expectation.get("min") if isinstance(expectation, dict) else None
    if expected_min and salary_max and salary_max < float(expected_min):
        note += f". Posted maximum is below the configured minimum of ${float(expected_min):,.0f}."
    elif expected_min and salary_min and salary_min >= float(expected_min):
        note += ". Posted range meets the configured minimum."
    elif expected_min:
        note += f". Configured minimum is ${float(expected_min):,.0f}."
    return {
        "known": True,
        "min": salary_min,
        "max": salary_max,
        "currency": currency,
        "note": note,
    }


def score_single_job(
    job: Dict[str, Any],
    profile: Dict[str, Any],
    weights: Dict[str, float] = DEFAULT_WEIGHTS
) -> Dict[str, Any]:
    """Calculates explainable rubric score and gap analysis for a single job."""
    title = (job.get("title") or "").strip()
    desc = (job.get("description") or "").strip()
    location = (job.get("location") or "").strip()
    work_mode = job.get("work_mode", "unknown")
    
    desc_lower = desc.lower()
    title_lower = title.lower()

    # 1. Title & Role Relevance (0 to 100)
    title_score = 40
    target_titles = profile.get("target_titles", []) or ([profile["title"]] if profile.get("title") else [])
    title_score = _title_match_score(title_lower, target_titles, title_score, full_match=100)
    acceptable_titles = profile.get("acceptable_titles") or []
    if acceptable_titles and title_score < 100:
        title_score = _title_match_score(title_lower, acceptable_titles, title_score, full_match=85)

    # 2. Core Required Skills (0 to 100)
    proven_skills = profile.get("proven_skills", [])
    matched_proven = []
    missing_critical = []
    
    for skill in proven_skills:
        # Check skill in JD (word boundary safe)
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, desc_lower) or re.search(pattern, title_lower):
            matched_proven.append(skill)

    # Detect technologies mentioned in JD
    common_tech_keywords = [
        "python", "go", "golang", "rust", "java", "c++", "c#", "typescript", "javascript",
        "react", "node", "fastapi", "django", "postgresql", "mysql", "redis", "kafka",
        "rabbitmq", "docker", "kubernetes", "aws", "gcp", "azure", "terraform", "graphql",
        "rest", "grpc", "microservices", "snowflake", "spark", "sql",
        "salesforce", "zendesk", "excel", "jira", "hubspot"
    ]
    jd_tech_mentioned = [t for t in common_tech_keywords if re.search(r"\b" + re.escape(t) + r"\b", desc_lower)]
    
    proven_lower = {s.lower() for s in proven_skills}
    for tech in jd_tech_mentioned:
        if tech not in proven_lower:
            # Check if transferable
            if tech not in {s.lower() for s in profile.get("transferable_skills", [])}:
                missing_critical.append(tech.capitalize())

    if jd_tech_mentioned:
        overlap_count = sum(1 for t in jd_tech_mentioned if t in proven_lower)
        skills_score = min(100, int((overlap_count / len(jd_tech_mentioned)) * 100) + 15)
    else:
        skills_score = 75 if matched_proven else 50

    # 3. Experience & Seniority (0 to 100)
    cand_exp = profile.get("years_exp")
    if not isinstance(cand_exp, int):
        cand_exp = None
    jd_exp_match = re.search(r"(\d+)\+?\s*(?:-\s*(\d+))?\s*(?:years|yrs)(?:\s*of)?\s*experience", desc_lower)
    if cand_exp is None:
        exp_score = 70
    elif jd_exp_match:
        req_exp = int(jd_exp_match.group(1))
        if cand_exp >= req_exp:
            exp_score = 100
        elif cand_exp >= req_exp - 1:
            exp_score = 80
        else:
            exp_score = max(30, int((cand_exp / req_exp) * 80))
    else:
        # Check title seniority
        if "senior" in title_lower or "lead" in title_lower:
            exp_score = 90 if cand_exp >= 5 else 60
        elif "staff" in title_lower or "principal" in title_lower:
            exp_score = 90 if cand_exp >= 8 else 60
        else:
            exp_score = 85

    # 4. Domain & Industry Fit (0 to 100)
    domains = profile.get("domain_expertise", [])
    matched_domains = []
    for d in domains:
        if d.lower() in desc_lower:
            matched_domains.append(d)
    domain_score = min(100, 50 + len(matched_domains) * 20) if domains else 70

    # 5. Location & Work Arrangement (0 to 100)
    cand_mode = profile.get("work_mode_pref") or "remote"
    if cand_mode == "remote":
        if work_mode == "remote" or "remote" in location.lower():
            loc_score = 100
        elif work_mode == "hybrid":
            loc_score = 65
        else:
            loc_score = 40
    else:
        loc_score = 90

    # 6. Preferred Qualifications & Transferable Skills (0 to 100)
    transferable = profile.get("transferable_skills", [])
    matched_transferable = [t for t in transferable if t.lower() in desc_lower]
    pref_score = min(100, 60 + len(matched_transferable) * 15)

    excluded_hit = False
    for excluded in profile.get("excluded_titles") or []:
        if excluded and excluded.lower() in title_lower:
            excluded_hit = True
            title_score = min(title_score, 20)

    # Weighted Total Score
    total_score = (
        title_score * weights["title_and_role_relevance"] +
        skills_score * weights["core_required_skills"] +
        exp_score * weights["experience_seniority"] +
        domain_score * weights["domain_industry_fit"] +
        loc_score * weights["location_and_work_mode"] +
        pref_score * weights["preferred_qualifications"]
    )
    final_score = int(round(total_score))
    if excluded_hit:
        final_score = min(final_score, 40)

    # Recommendation
    if excluded_hit:
        recommendation = "SKIP"
        confidence = "High"
    elif final_score >= 80:
        recommendation = "APPLY"
        confidence = "High"
    elif final_score >= 65:
        recommendation = "CONSIDER"
        confidence = "Medium"
    else:
        recommendation = "SKIP"
        confidence = "High" if final_score < 50 else "Medium"

    # Compile strengths & material gaps
    strengths = []
    if matched_proven:
        strengths.append(f"Core proven technical skills: {', '.join(matched_proven[:6])}")
    if matched_domains:
        strengths.append(f"Direct domain alignment: {', '.join(matched_domains[:3])}")
    if exp_score >= 90 and isinstance(cand_exp, int):
        strengths.append(f"Strong seniority fit ({cand_exp} years proven experience)")
    if loc_score == 100:
        strengths.append("Matches preferred remote work arrangement")
    company_name = job.get("company") or ""
    for preferred in profile.get("preferred_companies") or []:
        if preferred and preferred.lower() in company_name.lower():
            strengths.append(f"Company is on the preferred list ({preferred})")
            break

    gaps = []
    if missing_critical:
        gaps.append(f"Technologies mentioned in JD not in proven skills: {', '.join(missing_critical[:4])}")
    if cand_exp is None:
        gaps.append("Years of experience were not provided, so seniority was not confirmed")
    elif exp_score < 70:
        gaps.append("Required years of experience exceeds candidate profile")
    if loc_score < 60:
        gaps.append(f"Work arrangement ({work_mode}) may require onsite presence in {location}")
    if excluded_hit:
        gaps.append("Title matches a configured excluded title")

    salary = _salary_explanation(job, profile)
    posting_level = "unspecified"
    for label in ("intern", "junior", "senior", "staff", "principal", "lead", "director"):
        if label in title_lower:
            posting_level = label
            break
    if profile.get("seniority"):
        candidate_level = str(profile["seniority"])
    elif isinstance(cand_exp, int):
        candidate_level = f"{cand_exp} years on file"
    else:
        candidate_level = "not provided"
    if cand_exp is None:
        seniority_note = f"Posting reads as {posting_level}. Candidate seniority is not provided, so this was not treated as a match."
    else:
        seniority_note = f"Posting reads as {posting_level}. Candidate seniority on file: {candidate_level}."
    if location:
        location_note = f"Posting location: {location} ({work_mode})."
    else:
        location_note = "Location is not listed on this posting."
    if profile.get("locations") or profile.get("location"):
        location_note += f" Configured locations: {profile.get('location') or ', '.join(profile.get('locations') or [])}."
    if loc_score < 60:
        location_note += " This does not match the configured work mode."
    elif loc_score == 100:
        location_note += " Work mode matches."

    why_fit = list(strengths) or ["No verified strength lined up with the checked requirements."]
    why_not = list(gaps)
    if not salary["known"]:
        why_not.append("Salary is not listed on this posting, so compensation fit is unknown.")
    if not why_not:
        why_not = ["No material gap was found in title, checked skills, seniority, location, or disclosed salary."]

    explanation = {
        "why_fit": why_fit,
        "why_not": why_not,
        "salary": salary,
        "location": {"posting": location or None, "work_mode": work_mode, "note": location_note},
        "seniority": {"posting": posting_level, "candidate": candidate_level, "note": seniority_note},
        "required_skills": jd_tech_mentioned,
        "missing_or_gaps": list(missing_critical),
        "application_priority": recommendation,
    }

    rationale = (
        f"Score {final_score}/100 ({recommendation}). Title relevance is {title_score}%, "
        f"core skills match is {skills_score}%, and experience alignment is {exp_score}%. "
    )
    if matched_proven:
        rationale += f"Candidate has verified production experience in {', '.join(matched_proven[:4])}. "
    if missing_critical:
        rationale += f"Gaps identified in {', '.join(missing_critical[:3])}."

    return {
        "score": final_score,
        "confidence": confidence,
        "recommendation": recommendation,
        "dimension_scores": {
            "title_relevance": title_score,
            "core_skills": skills_score,
            "seniority_exp": exp_score,
            "domain_fit": domain_score,
            "location_work_mode": loc_score,
            "preferred_qualifications": pref_score
        },
        "strengths": strengths,
        "material_gaps": gaps,
        "proven_matches": matched_proven,
        "transferable_matches": matched_transferable,
        "unmet_requirements": missing_critical,
        "rationale": rationale,
        "why_fit": why_fit,
        "why_not": why_not,
        "salary": salary,
        "location_assessment": explanation["location"],
        "seniority_assessment": explanation["seniority"],
        "required_skills": jd_tech_mentioned,
        "missing_or_gaps": list(missing_critical),
        "application_priority": recommendation,
        "explanation": explanation,
    }


def score_job_list(
    jobs: List[Dict[str, Any]],
    profile: Dict[str, Any],
    weights: Dict[str, float] = DEFAULT_WEIGHTS
) -> List[Dict[str, Any]]:
    """Scores and ranks a list of jobs, sorting highest score first."""
    scored = []
    for job in jobs:
        score_eval = score_single_job(job, profile, weights)
        enriched = dict(job)
        enriched["fit_score"] = score_eval["score"]
        enriched["fit_evaluation"] = score_eval
        scored.append(enriched)

    # Sort descending by fit score, then by date posted
    scored.sort(key=lambda x: (x.get("fit_score", 0), x.get("posted_at") or ""), reverse=True)
    return scored


def main():
    parser = argparse.ArgumentParser(description="Score and rank jobs using transparent rubric.")
    parser.add_argument("--in", dest="in_file", required=True, help="Input jobs JSON file (or - for stdin)")
    parser.add_argument("--candidate", default="candidate", help="Candidate data directory")
    parser.add_argument("--weights", help="Path to custom rubric_weights.json")
    parser.add_argument("--top", type=int, default=10, help="Number of top jobs to return")
    parser.add_argument("--out", help="Output scored jobs JSON path")

    args = parser.parse_args()

    raw_data = []
    if args.in_file == "-":
        raw_data = json.load(sys.stdin)
    else:
        with open(args.in_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

    weights = DEFAULT_WEIGHTS
    if args.weights and os.path.exists(args.weights):
        try:
            with open(args.weights, "r", encoding="utf-8") as f:
                w_data = json.load(f)
                weights = w_data.get("weights", DEFAULT_WEIGHTS)
        except Exception as e:
            sys.stderr.write(f"Error reading weights: {e}\n")

    profile = load_candidate_profile(args.candidate)
    scored = score_job_list(raw_data, profile, weights)

    top_jobs = scored[:args.top] if args.top > 0 else scored

    out_json = json.dumps(top_jobs, indent=2, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out_json)
        print(f"Scored {len(scored)} jobs. Saved top {len(top_jobs)} to {args.out}")
    else:
        print(out_json)


if __name__ == "__main__":
    main()
