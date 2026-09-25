#!/usr/bin/env python3
"""Canonical model for employment, consulting, fractional, and buyer-signal opportunities.

This module deliberately separates "there is evidence of a business need" from
"we know a specific person's identity." It can recommend likely decision-maker
roles from grounded opportunity context, but it never invents names or contact
details.
"""

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from opportunity_tracks import best_track_for_job


OPPORTUNITY_TYPES = {
    "employment",
    "fractional",
    "consulting_project",
    "buyer_signal",
    "referral",
}

TRACK_TARGET_ROLES = {
    "ai-transformation-enablement": [
        "Chief AI Officer",
        "Chief Information Officer",
        "Chief Technology Officer",
        "Chief Operating Officer",
        "VP / Head of AI",
        "VP / Head of Transformation",
        "CEO / Founder",
    ],
    "ai-transformation": [
        "Chief AI Officer",
        "Chief Information Officer",
        "Chief Technology Officer",
        "Chief Operating Officer",
        "VP / Head of AI",
        "VP / Head of Transformation",
        "CEO / Founder",
    ],
    "ai-product-solutions-builder": [
        "Chief Technology Officer",
        "VP Engineering",
        "Head of Product",
        "VP Product",
        "Founder / CEO",
        "Head of AI",
    ],
    "ai-product-builder": [
        "Chief Technology Officer",
        "VP Engineering",
        "Head of Product",
        "VP Product",
        "Founder / CEO",
        "Head of AI",
    ],
    "growth-ai-systems": [
        "Chief Marketing Officer",
        "Chief Revenue Officer",
        "VP Growth",
        "VP Marketing",
        "Head of Revenue Operations",
        "Head of Marketing Operations",
        "CEO / Founder",
    ],
    "growth-ai-automation": [
        "Chief Marketing Officer",
        "Chief Revenue Officer",
        "VP Growth",
        "VP Marketing",
        "Head of Revenue Operations",
        "Head of Marketing Operations",
        "CEO / Founder",
    ],
    "fractional-ai-advisory": [
        "CEO / Founder",
        "President",
        "Chief Operating Officer",
        "Operating Partner",
        "Chief Technology Officer",
        "Chief AI Officer",
    ],
    "full-stack-ai-builder": [
        "Chief Technology Officer",
        "VP Engineering",
        "Head of Product",
        "Founder / CEO",
    ],
    "coworking-proptech": [
        "Owner / Founder",
        "Chief Executive Officer",
        "Chief Operating Officer",
        "Chief Marketing Officer",
        "VP Sales",
        "Head of Growth",
        "Director of Coworking / Flexible Workspace",
    ],
}

SIGNAL_TARGET_ROLES = {
    "ai_adoption": [
        "Chief AI Officer",
        "Chief Information Officer",
        "Chief Technology Officer",
        "Chief Operating Officer",
        "VP / Head of Transformation",
    ],
    "workflow_automation": [
        "Chief Operating Officer",
        "VP Operations",
        "Chief Technology Officer",
        "Head of Automation",
        "CEO / Founder",
    ],
    "growth_or_pipeline": [
        "Chief Marketing Officer",
        "Chief Revenue Officer",
        "VP Growth",
        "Head of Revenue Operations",
        "CEO / Founder",
    ],
    "crm_or_lead_response": [
        "Chief Revenue Officer",
        "Chief Marketing Officer",
        "Head of Revenue Operations",
        "VP Sales",
        "VP Marketing",
    ],
    "product_prototype": [
        "Chief Technology Officer",
        "Head of Product",
        "VP Engineering",
        "Founder / CEO",
    ],
    "coworking_demand": [
        "Owner / Founder",
        "Chief Executive Officer",
        "Chief Operating Officer",
        "Chief Marketing Officer",
        "VP Sales",
    ],
}


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _dedupe(values: List[str]) -> List[str]:
    result: List[str] = []
    seen = set()
    for value in values:
        cleaned = _clean(value)
        key = cleaned.lower()
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result


def generate_opportunity_id(
    opportunity_type: str,
    company: str,
    title: str,
    source_url: str = "",
) -> str:
    seed = "|".join(
        [
            _clean(opportunity_type).lower(),
            _clean(company).lower(),
            _clean(title).lower(),
            _clean(source_url).lower(),
        ]
    )
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]


def infer_signal_category(raw: Dict[str, Any]) -> Optional[str]:
    """Infer a broad business-need category from evidence without guessing intent."""
    text = " ".join(
        [
            _clean(raw.get("title")),
            _clean(raw.get("description")),
            " ".join(str(x) for x in raw.get("signals", []) or []),
            " ".join(str(x) for x in raw.get("evidence", []) or []),
        ]
    ).lower()

    rules = [
        (
            "crm_or_lead_response",
            ["crm", "lead response", "speed to lead", "lead routing", "hubspot", "salesforce"],
        ),
        (
            "growth_or_pipeline",
            ["pipeline", "lead generation", "demand generation", "growth", "conversion", "revops"],
        ),
        (
            "workflow_automation",
            ["workflow", "automation", "manual process", "operational efficiency", "make.com", "n8n", "zapier"],
        ),
        (
            "product_prototype",
            ["prototype", "mvp", "proof of concept", "product build", "full stack", "application"],
        ),
        (
            "coworking_demand",
            ["coworking", "flexible workspace", "flex space", "office occupancy", "meeting rooms"],
        ),
        (
            "ai_adoption",
            ["ai adoption", "generative ai", "genai", "ai strategy", "ai transformation", "agentic ai"],
        ),
    ]

    for category, keywords in rules:
        if any(keyword in text for keyword in keywords):
            return category
    return None


def infer_target_person_roles(
    opportunity: Dict[str, Any],
    tracks: Optional[List[Dict[str, Any]]] = None,
) -> List[str]:
    """Recommend role categories to research, never specific people."""
    roles: List[str] = []

    track = opportunity.get("opportunity_track") or {}
    track_id = track.get("id") if isinstance(track, dict) else None
    if track_id:
        roles.extend(TRACK_TARGET_ROLES.get(track_id, []))

    signal_category = opportunity.get("signal_category")
    if signal_category:
        roles.extend(SIGNAL_TARGET_ROLES.get(signal_category, []))

    if not roles and tracks:
        pseudo_job = {
            "title": opportunity.get("title", ""),
            "description": opportunity.get("description", ""),
            "employment_type": opportunity.get("engagement_type", ""),
        }
        best_track, track_score = best_track_for_job(pseudo_job, tracks)
        if best_track and track_score > 0:
            opportunity["opportunity_track"] = {
                "id": best_track.get("id"),
                "label": best_track.get("label"),
                "score": track_score,
            }
            roles.extend(TRACK_TARGET_ROLES.get(best_track.get("id"), []))

    # Generic fallback is intentionally broad and role-based.
    if not roles:
        roles = [
            "CEO / Founder",
            "Chief Operating Officer",
            "Chief Technology Officer",
        ]

    return _dedupe(roles)


def normalize_opportunity(
    raw: Dict[str, Any],
    tracks: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Normalize a discovered opportunity into a grounded, auditable schema."""
    opportunity_type = _clean(raw.get("opportunity_type") or "buyer_signal").lower()
    if opportunity_type not in OPPORTUNITY_TYPES:
        raise ValueError(
            f"Unsupported opportunity_type '{opportunity_type}'. "
            f"Expected one of: {sorted(OPPORTUNITY_TYPES)}"
        )

    company = _clean(raw.get("company"))
    title = _clean(raw.get("title") or raw.get("summary") or "Untitled opportunity")
    source_url = _clean(raw.get("source_url"))
    evidence = raw.get("evidence") or []
    if isinstance(evidence, str):
        evidence = [evidence]

    normalized: Dict[str, Any] = {
        "id": raw.get("id") or generate_opportunity_id(
            opportunity_type, company, title, source_url
        ),
        "opportunity_type": opportunity_type,
        "source": _clean(raw.get("source") or "manual_research"),
        "source_url": source_url or None,
        "company": company or None,
        "title": title,
        "description": _clean(raw.get("description")),
        "location": _clean(raw.get("location")) or None,
        "engagement_type": _clean(raw.get("engagement_type")) or None,
        "compensation": raw.get("compensation"),
        "signals": _dedupe([str(x) for x in (raw.get("signals") or [])]),
        "evidence": _dedupe([str(x) for x in evidence]),
        "discovered_at": raw.get("discovered_at")
        or datetime.now(timezone.utc).isoformat(),
        "status": _clean(raw.get("status") or "found").lower(),
        "contact": raw.get("contact"),
    }

    normalized["signal_category"] = (
        raw.get("signal_category") or infer_signal_category(normalized)
    )

    if raw.get("opportunity_track"):
        normalized["opportunity_track"] = raw["opportunity_track"]
    elif tracks:
        pseudo_job = {
            "title": normalized["title"],
            "description": normalized["description"],
            "employment_type": normalized["engagement_type"] or "",
        }
        best_track, track_score = best_track_for_job(pseudo_job, tracks)
        normalized["opportunity_track"] = (
            {
                "id": best_track.get("id"),
                "label": best_track.get("label"),
                "score": track_score,
            }
            if best_track
            else None
        )
    else:
        normalized["opportunity_track"] = None

    normalized["target_person_roles"] = infer_target_person_roles(
        normalized, tracks=tracks
    )

    return normalized


def normalize_file(
    input_path: str,
    output_path: str,
    tracks: Optional[List[Dict[str, Any]]] = None,
) -> int:
    with open(input_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    raw_items = payload if isinstance(payload, list) else payload.get("opportunities", [])
    normalized = [normalize_opportunity(item, tracks=tracks) for item in raw_items]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(normalized, f, indent=2, ensure_ascii=False)

    return len(normalized)
