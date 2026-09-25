#!/usr/bin/env python3
"""Multi-track opportunity configuration and matching helpers.

Candidate-specific track configuration lives in candidate/OPPORTUNITY_TRACKS.json,
which is intentionally ignored by git with the rest of candidate data. The
committed template under templates/ documents the supported schema.
"""

import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _tokens(value: Any) -> List[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9+#.]+", _clean(value))
        if len(token) >= 2
    ]


def load_opportunity_tracks(candidate_dir: str = "candidate") -> List[Dict[str, Any]]:
    """Load and minimally validate candidate opportunity tracks."""
    path = os.path.join(candidate_dir, "OPPORTUNITY_TRACKS.json")
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    raw_tracks = payload.get("tracks", []) if isinstance(payload, dict) else []
    tracks: List[Dict[str, Any]] = []
    seen_ids = set()

    for idx, raw in enumerate(raw_tracks):
        if not isinstance(raw, dict):
            continue

        track_id = _clean(raw.get("id")).replace(" ", "-")
        if not track_id or track_id in seen_ids:
            continue
        seen_ids.add(track_id)

        tracks.append(
            {
                "id": track_id,
                "label": str(raw.get("label") or track_id).strip(),
                "priority": int(raw.get("priority", idx + 1)),
                "search_queries": [
                    str(x).strip()
                    for x in raw.get("search_queries", [])
                    if str(x).strip()
                ],
                "title_keywords": [
                    _clean(x)
                    for x in raw.get("title_keywords", [])
                    if _clean(x)
                ],
                "positive_signals": [
                    _clean(x)
                    for x in raw.get("positive_signals", [])
                    if _clean(x)
                ],
                "negative_signals": [
                    _clean(x)
                    for x in raw.get("negative_signals", [])
                    if _clean(x)
                ],
                "preferred_engagements": [
                    _clean(x)
                    for x in raw.get("preferred_engagements", [])
                    if _clean(x)
                ],
            }
        )

    return sorted(tracks, key=lambda t: (t.get("priority", 999), t["id"]))


def search_queries_from_tracks(
    tracks: List[Dict[str, Any]],
    limit: int = 8,
) -> List[str]:
    """Return a balanced, deduplicated query set using round-robin by track.

    Round-robin matters for candidates with several professional identities:
    one track cannot consume the entire query budget before other tracks are
    represented.
    """
    if limit <= 0 or not tracks:
        return []

    query_lists = [list(t.get("search_queries", [])) for t in tracks]
    max_len = max((len(items) for items in query_lists), default=0)
    result: List[str] = []
    seen = set()

    for query_index in range(max_len):
        for items in query_lists:
            if query_index >= len(items):
                continue
            query = str(items[query_index]).strip()
            key = _clean(query)
            if not key or key in seen:
                continue
            seen.add(key)
            result.append(query)
            if len(result) >= limit:
                return result

    return result


GENERIC_QUERY_TOKENS = {
    "senior", "sr", "lead", "manager", "director", "head", "engineer",
    "developer", "consultant", "specialist", "principal", "staff", "the", "of"
}


def matching_queries_for_job(
    job: Dict[str, Any],
    queries: List[str],
) -> List[str]:
    """Return configured queries plausibly represented by a posting.

    ATS boards are fetched once per company. Query matching then happens locally,
    which makes broad multi-track discovery much cheaper than re-fetching every
    company board once per search phrase.
    """
    if not queries:
        return []

    title = _clean(job.get("title"))
    description = _clean(job.get("description"))
    combined = f"{title} {description}"
    title_tokens = set(_tokens(title))
    combined_tokens = set(_tokens(combined))
    matches: List[str] = []

    for query in queries:
        query_clean = _clean(query)
        if not query_clean:
            continue
        if query_clean in combined:
            matches.append(query)
            continue

        query_tokens = [
            token for token in _tokens(query)
            if token not in GENERIC_QUERY_TOKENS
        ]
        if not query_tokens:
            query_tokens = _tokens(query)
        if not query_tokens:
            continue

        title_hits = sum(1 for token in query_tokens if token in title_tokens)
        combined_hits = sum(1 for token in query_tokens if token in combined_tokens)

        # Prefer title evidence. Description-only matching must cover nearly all
        # of the meaningful query tokens to avoid flooding the shortlist.
        title_threshold = max(1, (len(query_tokens) + 1) // 2)
        desc_threshold = max(2, len(query_tokens) - 1)

        if title_hits >= title_threshold or combined_hits >= desc_threshold:
            matches.append(query)

    return matches


def best_track_for_job(
    job: Dict[str, Any],
    tracks: List[Dict[str, Any]],
) -> Tuple[Optional[Dict[str, Any]], int]:
    """Return the best matching track plus a transparent 0-100 track score."""
    if not tracks:
        return None, 0

    title = _clean(job.get("title"))
    description = _clean(job.get("description"))
    employment_type = _clean(job.get("employment_type"))
    title_tokens = set(_tokens(title))

    best_track: Optional[Dict[str, Any]] = None
    best_score = 0

    for track in tracks:
        score = 0

        # Explicit title phrases are the strongest evidence.
        title_hits = 0
        for phrase in track.get("title_keywords", []):
            if phrase and phrase in title:
                title_hits += 1
                score += 25
            elif phrase and phrase in description:
                score += 5
        score = min(score, 55)

        # Search-query language adds fuzzy coverage without requiring exact titles.
        query_coverage = 0.0
        for query in track.get("search_queries", []):
            q_tokens = set(_tokens(query))
            if not q_tokens:
                continue
            overlap = len(q_tokens & title_tokens) / len(q_tokens)
            query_coverage = max(query_coverage, overlap)
        score += int(round(query_coverage * 30))

        positive_hits = sum(
            1 for signal in track.get("positive_signals", [])
            if signal and (signal in title or signal in description)
        )
        score += min(positive_hits * 5, 20)

        negative_hits = sum(
            1 for signal in track.get("negative_signals", [])
            if signal and (signal in title or signal in description)
        )
        score -= min(negative_hits * 8, 24)

        preferred = track.get("preferred_engagements", [])
        if preferred and any(value in employment_type for value in preferred):
            score += 10

        score = max(0, min(100, score))

        if score > best_score or (
            score == best_score
            and best_track is not None
            and track.get("priority", 999) < best_track.get("priority", 999)
        ):
            best_track = track
            best_score = score

    return best_track, best_score
