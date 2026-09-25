#!/usr/bin/env python3
"""Persistent outcome ledger for jobs, consulting leads, and revenue opportunities."""

import argparse
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


VALID_STATUSES = {
    "found",
    "qualified",
    "applied",
    "contacted",
    "replied",
    "interview",
    "meeting",
    "proposal",
    "offer",
    "won",
    "hired",
    "rejected",
    "lost",
    "no_response",
    "withdrawn",
}

POSITIVE_STATUSES = {"replied", "interview", "meeting", "proposal", "offer", "won", "hired"}


def _load(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {"version": 1, "items": {}, "events": []}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Outcome ledger must be a JSON object.")
    data.setdefault("version", 1)
    data.setdefault("items", {})
    data.setdefault("events", [])
    return data


def _save(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def record_outcome(
    path: str,
    item_id: str,
    status: str,
    *,
    company: str = "",
    title: str = "",
    kind: str = "employment",
    track_id: str = "",
    source: str = "",
    value: Optional[float] = None,
    note: str = "",
    occurred_at: str = "",
) -> Dict[str, Any]:
    status = status.strip().lower()
    if status not in VALID_STATUSES:
        raise ValueError(f"Unsupported status '{status}'. Expected one of {sorted(VALID_STATUSES)}")
    if not item_id.strip():
        raise ValueError("item_id is required")

    data = _load(path)
    ts = occurred_at or datetime.now(timezone.utc).isoformat()
    existing = data["items"].get(item_id, {})

    item = {
        "id": item_id,
        "company": company or existing.get("company", ""),
        "title": title or existing.get("title", ""),
        "kind": kind or existing.get("kind", "employment"),
        "track_id": track_id or existing.get("track_id", ""),
        "source": source or existing.get("source", ""),
        "status": status,
        "value": value if value is not None else existing.get("value"),
        "updated_at": ts,
    }
    data["items"][item_id] = item
    data["events"].append(
        {
            "item_id": item_id,
            "status": status,
            "occurred_at": ts,
            "note": note or None,
            "value": value,
        }
    )
    _save(path, data)
    return item


def summarize_outcomes(path: str) -> Dict[str, Any]:
    data = _load(path)
    items = list(data.get("items", {}).values())
    status_counts = Counter(str(i.get("status") or "unknown") for i in items)
    by_track: Dict[str, Counter] = defaultdict(Counter)
    by_source: Dict[str, Counter] = defaultdict(Counter)

    for item in items:
        track = str(item.get("track_id") or "unclassified")
        source = str(item.get("source") or "unknown")
        status = str(item.get("status") or "unknown")
        by_track[track][status] += 1
        by_source[source][status] += 1

    positive = sum(1 for item in items if item.get("status") in POSITIVE_STATUSES)
    terminal_wins = sum(1 for item in items if item.get("status") in {"won", "hired"})
    known_value = sum(
        float(item.get("value") or 0)
        for item in items
        if item.get("status") in {"won", "hired"} and item.get("value") is not None
    )

    return {
        "total_items": len(items),
        "status_counts": dict(status_counts),
        "positive_progress_count": positive,
        "wins_or_hires": terminal_wins,
        "known_won_value": known_value,
        "by_track": {k: dict(v) for k, v in by_track.items()},
        "by_source": {k: dict(v) for k, v in by_source.items()},
    }


def format_summary_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# Search & Revenue Outcome Summary",
        "",
        f"- **Tracked opportunities:** {summary['total_items']}",
        f"- **Reached reply / interview / meeting / proposal / offer / win:** {summary['positive_progress_count']}",
        f"- **Wins / hires:** {summary['wins_or_hires']}",
        f"- **Known won value:** ${summary['known_won_value']:,.0f}",
        "",
        "## Current status counts",
    ]
    for status, count in sorted(summary["status_counts"].items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"- {status}: {count}")

    lines += ["", "## By opportunity track"]
    for track, counts in sorted(summary["by_track"].items()):
        rendered = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
        lines.append(f"- **{track}**: {rendered}")

    lines += ["", "## By source"]
    for source, counts in sorted(summary["by_source"].items()):
        rendered = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
        lines.append(f"- **{source}**: {rendered}")

    lines += [
        "",
        "> Use this report to tune search lanes and source effort. Do not rewrite candidate history or fabricate fit to improve conversion.",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Record and summarize job/revenue outcomes.")
    sub = parser.add_subparsers(dest="command", required=True)

    rec = sub.add_parser("record")
    rec.add_argument("--ledger", default="jobs/outcomes.json")
    rec.add_argument("--id", required=True)
    rec.add_argument("--status", required=True, choices=sorted(VALID_STATUSES))
    rec.add_argument("--company", default="")
    rec.add_argument("--title", default="")
    rec.add_argument("--kind", default="employment")
    rec.add_argument("--track", default="")
    rec.add_argument("--source", default="")
    rec.add_argument("--value", type=float)
    rec.add_argument("--note", default="")

    summ = sub.add_parser("summary")
    summ.add_argument("--ledger", default="jobs/outcomes.json")
    summ.add_argument("--out")

    args = parser.parse_args()
    if args.command == "record":
        item = record_outcome(
            args.ledger,
            args.id,
            args.status,
            company=args.company,
            title=args.title,
            kind=args.kind,
            track_id=args.track,
            source=args.source,
            value=args.value,
            note=args.note,
        )
        print(json.dumps(item, indent=2))
    else:
        summary = summarize_outcomes(args.ledger)
        text = format_summary_markdown(summary)
        if args.out:
            os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(text + "\n")
            print(f"Wrote outcome summary to {args.out}")
        else:
            print(text)


if __name__ == "__main__":
    main()
