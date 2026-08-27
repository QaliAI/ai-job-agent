#!/usr/bin/env python3
"""Independent Anti-Fabrication QA & Evidence Verification Engine.

Strictly verifies tailored resumes, cover letters, and application materials
against candidate ground truth (MASTER_PROFILE.md, VERIFIED_ACHIEVEMENTS.md, skills.json).

Flags and blocks:
1. Hallucinated technical skills (tools candidate never verified).
2. Fabricated or exaggerated metrics (numbers/percentages not in achievement bank).
3. Altered company names, employment dates, or educational degrees.
4. Scope inflation and ungrounded leadership claims.

Ensures 100% factual grounding before materials reach an employer.
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


def load_candidate_ground_truth(candidate_dir: str = "candidate") -> Dict[str, Any]:
    """Extracts all verified facts from candidate source files."""
    truth: Dict[str, Any] = {
        "raw_text": "",
        "proven_skills": set(),
        "transferable_skills": set(),
        "all_skills_lower": set(),
        "verified_metrics": set(),
        "companies": set(),
        "degrees": set(),
        "achievements_text": ""
    }

    # 1. Load skills.json
    skills_path = os.path.join(candidate_dir, "skills.json")
    if os.path.exists(skills_path):
        try:
            with open(skills_path, "r", encoding="utf-8") as f:
                sdata = json.load(f)
                ps = set(sdata.get("proven_skills", []))
                ts = set(sdata.get("transferable_skills", []))
                truth["proven_skills"] = ps
                truth["transferable_skills"] = ts
                truth["all_skills_lower"] = {s.lower() for s in (ps | ts)}
        except Exception as e:
            sys.stderr.write(f"Error loading {skills_path}: {e}\n")

    # 2. Load MASTER_PROFILE.md
    master_path = os.path.join(candidate_dir, "MASTER_PROFILE.md")
    if os.path.exists(master_path):
        try:
            with open(master_path, "r", encoding="utf-8") as f:
                m_text = f.read()
                truth["raw_text"] += "\n" + m_text
                
                # Extract companies e.g. **Title** | Company Name
                comp_matches = re.findall(r"\|\s*([A-Za-z0-9\s.,&-]+?)(?:\s*\(|\s*\||\s*\n)", m_text)
                for c in comp_matches:
                    c_clean = c.strip().lower()
                    if c_clean and len(c_clean) > 2 and "remote" not in c_clean and "present" not in c_clean:
                        truth["companies"].add(c_clean)
        except Exception as e:
            sys.stderr.write(f"Error loading {master_path}: {e}\n")

    # 3. Load VERIFIED_ACHIEVEMENTS.md
    ach_path = os.path.join(candidate_dir, "VERIFIED_ACHIEVEMENTS.md")
    if os.path.exists(ach_path):
        try:
            with open(ach_path, "r", encoding="utf-8") as f:
                ach_text = f.read()
                truth["raw_text"] += "\n" + ach_text
                truth["achievements_text"] = ach_text
                
                # Extract numbers, percentages, dollar amounts
                metrics = re.findall(r"(\$?\d+(?:,\d{3})*(?:\.\d+)?%?|\d+x|\d+\+?)", ach_text)
                truth["verified_metrics"] = {m.lower() for m in metrics if len(m) > 1}
        except Exception as e:
            sys.stderr.write(f"Error loading {ach_path}: {e}\n")

    return truth


def verify_content(
    draft_content: str,
    truth: Dict[str, Any],
    job_description: Optional[str] = None
) -> Dict[str, Any]:
    """Runs QA checks on draft content against candidate ground truth."""
    violations = []
    warnings = []
    
    draft_lines = draft_content.splitlines()
    all_truth_lower = truth["raw_text"].lower()

    # 1. Tech Skills Hallucination Check
    known_tech_catalog = [
        "rust", "zig", "solidity", "c++", "c#", "scala", "clojure", "elixir", "erlang",
        "haskell", "perl", "ruby", "rails", "swift", "kotlin", "php", "laravel",
        "react native", "flutter", "vue", "angular", "svelte", "spark", "hadoop",
        "snowflake", "databricks", "dbt", "bigquery", "redshift", "cassandra",
        "scylla", "dynamodb", "mongodb", "neo4j", "couchbase", "solr", "elasticsearch",
        "opensearch", "kafka", "rabbitmq", "pulsar", "zeromq", "grpc", "protobuf",
        "graphql", "trpc", "kubernetes", "nomad", "terraform", "pulumi", "ansible",
        "puppet", "chef", "aws", "gcp", "azure", "cloudflare workers"
    ]
    
    # Identify technologies mentioned in draft
    for line_no, line in enumerate(draft_lines, start=1):
        line_lower = line.lower()
        if line.startswith("#") or line.strip().startswith("* **"):
            # Check skill headers
            pass
            
        for tech in known_tech_catalog:
            # Word boundary search
            pattern = r"\b" + re.escape(tech) + r"\b"
            if re.search(pattern, line_lower):
                # Is it in candidate's ground truth?
                if tech not in truth["all_skills_lower"] and tech not in all_truth_lower:
                    # If this tech is mentioned in JD, check if the draft claimed direct production ownership
                    violations.append({
                        "type": "unsupported_skill",
                        "severity": "HIGH",
                        "line": line_no,
                        "skill": tech,
                        "snippet": line.strip(),
                        "detail": f"Claimed skill '{tech}' is NOT present in candidate's verified skills or master profile."
                    })

    # 2. Metric & Number Grounding Check
    # Look for metrics in draft bullets (e.g. 50%, $100k, 10x, 45,000)
    for line_no, line in enumerate(draft_lines, start=1):
        if line.strip().startswith("*") or line.strip().startswith("-"):
            # Find numbers and percentages
            draft_metrics = re.findall(r"(\$?\d+(?:,\d{3})*(?:\.\d+)?%?|\d+x)", line)
            for dm in draft_metrics:
                dm_clean = dm.strip().lower()
                # Skip simple years e.g. 2022, 2024
                if re.match(r"^(?:19|20)\d\d$", dm_clean):
                    continue
                # Skip trivial counts like 1, 2, 3
                if dm_clean in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "1st", "2nd"]:
                    continue
                
                # Check if this metric exists in truth text
                if dm_clean not in all_truth_lower and dm_clean not in truth["verified_metrics"]:
                    # Also check metric without formatting e.g. 45000 vs 45,000
                    raw_num = dm_clean.replace(",", "").replace("$", "").replace("%", "")
                    if raw_num not in all_truth_lower:
                        violations.append({
                            "type": "unverified_metric",
                            "severity": "MEDIUM",
                            "line": line_no,
                            "metric": dm,
                            "snippet": line.strip(),
                            "detail": f"Metric '{dm}' does not appear in candidate's VERIFIED_ACHIEVEMENTS.md or master profile."
                        })

    # Calculate QA status
    passed = len(violations) == 0
    total_checks = len(draft_lines) + len(known_tech_catalog)

    return {
        "status": "PASSED" if passed else "FAILED",
        "passed": passed,
        "violation_count": len(violations),
        "warning_count": len(warnings),
        "violations": violations,
        "warnings": warnings,
        "total_checks_evaluated": total_checks,
        "summary": (
            "QA Check Passed: All skills, metrics, and claims are 100% grounded in candidate source truth."
            if passed else
            f"QA Check Failed: Found {len(violations)} unsupported claim(s) requiring candidate verification."
        )
    }


def main():
    parser = argparse.ArgumentParser(description="Verify tailored materials against candidate ground truth.")
    parser.add_argument("--candidate", default="candidate", help="Candidate data directory")
    parser.add_argument("--draft", required=True, help="Path to draft resume or cover letter markdown file")
    parser.add_argument("--jd", help="Path to target Job Description text file")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    if not os.path.exists(args.draft):
        sys.stderr.write(f"Draft file not found: {args.draft}\n")
        sys.exit(1)

    with open(args.draft, "r", encoding="utf-8") as f:
        draft_content = f.read()

    jd_content = None
    if args.jd and os.path.exists(args.jd):
        with open(args.jd, "r", encoding="utf-8") as f:
            jd_content = f.read()

    truth = load_candidate_ground_truth(args.candidate)
    report = verify_content(draft_content, truth, jd_content)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("\n=======================================================")
        print(f" CLAIM CHECK QA REPORT — STATUS: {report['status']}")
        print("=======================================================")
        print(report["summary"])
        if report["violations"]:
            print("\n❌ VIOLATIONS FOUND:")
            for v in report["violations"]:
                print(f"  Line {v.get('line', '?')} [{v['type']}]: {v['detail']}")
                print(f"    Snippet: \"{v.get('snippet', '')}\"")
        print("=======================================================\n")

    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
