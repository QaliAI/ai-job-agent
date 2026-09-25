#!/usr/bin/env python3
"""Scannable daily digest for one profile. No auto-apply."""

from datetime import date
from typing import Any, Dict, List, Optional


def _money(job: Dict[str, Any], explanation: Dict[str, Any]) -> str:
    salary = explanation.get("salary") or {}
    if salary.get("note"):
        return salary["note"]
    if job.get("salary_min") or job.get("salary_max"):
        return "Compensation listed on the posting."
    return "Salary is not listed on this posting."


def _why(explanation: Dict[str, Any], key: str, fallback: str) -> str:
    values = explanation.get(key) or []
    if not values:
        return fallback
    parts = []
    for item in values:
        text = str(item).strip()
        if text and text[-1] not in ".!?":
            text += "."
        parts.append(text)
    return " ".join(parts)


def format_digest(
    jobs: List[Dict[str, Any]],
    profile: Dict[str, Any],
    total_scanned: int = 0,
    total_filtered: int = 0,
    note: str = "",
    today: Optional[str] = None,
) -> str:
    today_str = today or date.today().isoformat()
    name = profile.get("name") or "Candidate"
    limit = len(jobs)
    sample_banner = ""
    if profile.get("sample"):
        label = profile.get("label") or "SAMPLE CLIENT. Synthetic data. Not a real person."
        sample_banner = f"> {label}\n\n"

    lines = [
        f"# Daily digest — {name} — {today_str}",
        "",
        sample_banner + "No auto-apply. Review each role and submit it yourself.",
        "",
        f"Scanned: {total_scanned} · Passed filters: {total_filtered} · Showing: {limit}",
    ]
    if note:
        lines.append("")
        lines.append(note)
    lines.append("")

    if not jobs:
        lines.append("No roles to show.")
        lines.append("")
        return "\n".join(lines)

    lines.append("| # | Score | Priority | Company | Role | Location | Compensation |")
    lines.append("| ---: | ---: | --- | --- | --- | --- | --- |")
    for index, job in enumerate(jobs, start=1):
        evaluation = job.get("fit_evaluation") or {}
        explanation = evaluation.get("explanation") or {}
        priority = explanation.get("application_priority") or evaluation.get("recommendation") or ""
        company = str(job.get("company") or "").replace("|", "/")
        title = str(job.get("title") or "").replace("|", "/")
        location = str(job.get("location") or "Not listed").replace("|", "/")
        pay = _money(job, explanation).replace("|", "/")
        score = job.get("fit_score", evaluation.get("score", ""))
        lines.append(
            f"| {index} | {score} | {priority} | {company} | {title} | {location} | {pay} |"
        )
    lines.append("")

    for index, job in enumerate(jobs, start=1):
        evaluation = job.get("fit_evaluation") or {}
        explanation = evaluation.get("explanation") or {}
        priority = explanation.get("application_priority") or evaluation.get("recommendation") or "UNSCORED"
        found = job.get("first_seen") or job.get("first_seen_at") or today_str
        if isinstance(found, str) and "T" in found:
            found = found.split("T", 1)[0]
        url = job.get("apply_url") or job.get("canonical_url") or ""
        source = job.get("source") or "unknown"
        gap = _why(explanation, "why_not", "Gap assessment was not produced.")
        fit = _why(explanation, "why_fit", "Fit assessment was not produced.")
        lines.extend([
            f"## {index}. {job.get('company', 'Company')} — {job.get('title', 'Role')}",
            "",
            f"- **Score:** {job.get('fit_score', evaluation.get('score', 'n/a'))}",
            f"- **Priority:** {priority}",
            f"- **Location:** {explanation.get('location', {}).get('note') or job.get('location') or 'Not listed'}",
            f"- **Compensation:** {_money(job, explanation)}",
            f"- **Seniority:** {explanation.get('seniority', {}).get('note') or 'Not assessed'}",
            f"- **Why it fits:** {fit}",
            f"- **Notable gap:** {gap}",
            f"- **Required skills checked:** {', '.join(explanation.get('required_skills') or []) or 'None recognized in the posting'}",
            f"- **Source:** {source}",
            f"- **Apply:** {url or 'No URL on the posting'}",
            f"- **Date found:** {found}",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def format_status(store: Dict[str, Any], profile: Dict[str, Any]) -> str:
    jobs = (store or {}).get("jobs") or {}
    name = profile.get("name") or "Candidate"
    counts = {"new": 0, "saved": 0, "applied": 0, "interview": 0, "rejected": 0, "archived": 0, "other": 0}
    for record in jobs.values():
        status = (record.get("status") or "new").lower()
        if status in counts:
            counts[status] += 1
        else:
            counts["other"] += 1
    lines = [
        f"# Status — {name}",
        "",
        f"Tracked roles: {len(jobs)}",
        f"New: {counts['new']} · Saved: {counts['saved']} · Applied: {counts['applied']} · "
        f"Interview: {counts['interview']} · Rejected: {counts['rejected']} · Archived: {counts['archived']}",
        "",
    ]
    if not jobs:
        lines.append("Tracker is empty.")
        return "\n".join(lines) + "\n"
    lines.append("| Company | Role | Score | Status | First seen | Last seen |")
    lines.append("| --- | --- | ---: | --- | --- | --- |")
    records = sorted(jobs.values(), key=lambda item: (item.get("score") is None, -(item.get("score") or 0)))
    for record in records[:30]:
        first = str(record.get("first_seen") or record.get("first_seen_at") or "")[:10]
        last = str(record.get("last_seen") or record.get("last_verified_at") or "")[:10]
        score = record.get("score")
        score_text = "" if score is None else str(score)
        lines.append(
            f"| {record.get('company') or ''} | {record.get('title') or ''} | {score_text} | "
            f"{record.get('status') or ''} | {first} | {last} |"
        )
    lines.append("")
    return "\n".join(lines)
