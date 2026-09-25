#!/usr/bin/env python3
"""Explicit truthfulness guardrails for tailored career documents.

The tailor may reorder, emphasize, rephrase, select experience, and retarget
a summary. It must not introduce employers, titles, dates, degrees,
certifications, skills, accomplishments, revenue, metrics, or team size.

Factual checks look for structured claims. Experience bullets copied from the
source, or light rephrases whose facts already appear in the source, pass.
"""

import re
from typing import Any, Dict, List, Optional


MONTH = (
    r"January|February|March|April|May|June|July|August|September|October|"
    r"November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec"
)
DATE_RANGE_RE = re.compile(
    rf"((?:{MONTH}|\b(?:19|20)\d{{2}})\b[^|\n]{{0,40}}?(?:–|—|-)\s*(?:Present|Current|{MONTH}|\b(?:19|20)\d{{2}}\b))",
    re.IGNORECASE,
)
EMPLOYMENT_HEADER_RE = re.compile(
    r"^###\s+\*{0,2}(.+?)\*{0,2}\s*\|\s*(.+?)\s*$"
)
DEGREE_RE = re.compile(
    r"((?:B\.S\.|B\.A\.|M\.S\.|M\.A\.|Ph\.D\.|MBA|Bachelor|Master of|Associate of)[^|\n]{0,80})",
    re.IGNORECASE,
)
CERT_RE = re.compile(
    r"\b(AWS Certified[^\n|(]{0,40}|PMP|CISSP|CPA|CFA|BLS Certification|ACLS|RN License)\b",
    re.IGNORECASE,
)
REVENUE_RE = re.compile(
    r"\$\s?\d[\d,]*(?:\.\d+)?\s*(?:million|billion|k|m)?",
    re.IGNORECASE,
)
TEAM_RE = re.compile(
    r"\b(?:team of|managed|mentored|leading|led a team of)\s+\d{1,4}\b",
    re.IGNORECASE,
)
BULLET_RE = re.compile(r"^\s*[-*•]\s+(.+)$")


def _norm(text: str) -> str:
    text = text.lower().replace("–", "-").replace("—", "-")
    text = re.sub(r"[*_`>#]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _raw(truth: Dict[str, Any]) -> str:
    return truth.get("raw_text") or ""


def _section(text: str, start: str, end: str) -> str:
    bounded = re.search(start + r"([\s\S]*?)" + end, text, re.IGNORECASE)
    if bounded:
        return bounded.group(1)
    rest = re.search(start + r"([\s\S]*)", text, re.IGNORECASE)
    return rest.group(1) if rest else ""


def experience_section(draft: str) -> str:
    for start in (
        r"##\s*PROFESSIONAL EXPERIENCE",
        r"##\s*(?:4\.\s*)?Professional Experience",
        r"##\s*Experience\b",
    ):
        if re.search(start, draft, re.IGNORECASE):
            return _section(draft, start, r"\n##\s")
    return ""


def _violation(kind: str, detail: str, snippet: str) -> Dict[str, Any]:
    return {
        "type": kind,
        "severity": "HIGH",
        "line": None,
        "snippet": snippet.strip()[:240],
        "detail": detail,
    }


def factual_invention_violations(draft: str, truth: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flag structured facts that do not appear in candidate ground truth."""
    raw = _raw(truth)
    raw_n = _norm(raw)
    violations: List[Dict[str, Any]] = []
    if not draft:
        return violations

    exp = experience_section(draft)
    header_scope = exp or ""
    for line in header_scope.splitlines():
        header = EMPLOYMENT_HEADER_RE.match(line.strip())
        if not header:
            continue
        title = header.group(1).strip().strip("*").strip()
        company = header.group(2).strip().strip("*").strip()
        if title and _norm(title) not in raw_n:
            violations.append(_violation(
                "invented_title",
                f"Employment title '{title}' is not in the candidate profile.",
                line,
            ))
        if company and _norm(company) not in raw_n:
            violations.append(_violation(
                "invented_employer",
                f"Employer '{company}' is not in the candidate profile.",
                line,
            ))
        date_match = DATE_RANGE_RE.search(line)
        if date_match and _norm(date_match.group(1)) not in raw_n:
            violations.append(_violation(
                "invented_employment_dates",
                f"Employment dates '{date_match.group(1).strip()}' are not in the candidate profile.",
                line,
            ))

    # Dates that sit on the location line under a header.
    for line in header_scope.splitlines():
        if EMPLOYMENT_HEADER_RE.match(line.strip()):
            continue
        date_match = DATE_RANGE_RE.search(line)
        if date_match and _norm(date_match.group(1)) not in raw_n:
            violations.append(_violation(
                "invented_employment_dates",
                f"Employment dates '{date_match.group(1).strip()}' are not in the candidate profile.",
                line,
            ))

    for line in draft.splitlines():
        degree = DEGREE_RE.search(line)
        if degree and _norm(degree.group(1)) not in raw_n:
            violations.append(_violation(
                "invented_degree",
                f"Degree '{degree.group(1).strip(' *|')}' is not in the candidate profile.",
                line,
            ))
        cert = CERT_RE.search(line)
        if cert and _norm(cert.group(1)) not in raw_n:
            violations.append(_violation(
                "invented_certification",
                f"Certification '{cert.group(1).strip()}' is not in the candidate profile.",
                line,
            ))
        for money in REVENUE_RE.findall(line):
            if _norm(money) not in raw_n and re.sub(r"[^\d]", "", money) not in raw_n:
                violations.append(_violation(
                    "invented_revenue",
                    f"Revenue figure '{money.strip()}' is not in the candidate profile.",
                    line,
                ))
        team = TEAM_RE.search(line)
        if team and _norm(team.group(0)) not in raw_n:
            violations.append(_violation(
                "invented_team_size",
                f"Team-size claim '{team.group(0)}' is not in the candidate profile.",
                line,
            ))

    return _dedupe(violations)


def experience_bullet_violations(draft: str, truth: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flag experience bullets that are not copied or lightly rephrased from source."""
    raw_n = _norm(_raw(truth))
    violations = []
    for line in experience_section(draft).splitlines():
        match = BULLET_RE.match(line.strip())
        if not match:
            continue
        bullet = match.group(1).strip()
        if len(_norm(bullet)) < 25:
            continue
        if _bullet_supported(bullet, raw_n):
            continue
        violations.append(_violation(
            "invented_accomplishment",
            "Experience bullet is not present in, or clearly rephrased from, the candidate profile.",
            bullet,
        ))
    return violations


def _bullet_supported(bullet: str, raw_n: str) -> bool:
    norm_bullet = _norm(bullet)
    if norm_bullet and norm_bullet in raw_n:
        return True
    words = [word for word in re.findall(r"[a-z0-9+]{4,}", norm_bullet)]
    if not words:
        return True
    overlap = sum(1 for word in words if word in raw_n)
    numbers = re.findall(r"\d[\d,]*%?", bullet)
    numbers_ok = all(_norm(number) in raw_n or number.replace(",", "") in raw_n for number in numbers)
    return numbers_ok and (overlap / len(words)) >= 0.45


def check_truthfulness(draft: str, truth: Dict[str, Any], strict_bullets: bool = False) -> List[Dict[str, Any]]:
    violations = factual_invention_violations(draft, truth)
    if strict_bullets:
        violations.extend(experience_bullet_violations(draft, truth))
    return _dedupe(violations)


def _dedupe(violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    unique = []
    for item in violations:
        key = (item.get("type"), item.get("detail"))
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique
