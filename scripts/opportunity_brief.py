#!/usr/bin/env python3
"""Generate a human-review consulting/fractional opportunity brief."""

import argparse
import json
import os
from datetime import date
from typing import Any, Dict, List


def format_opportunity_brief(opportunities: List[Dict[str, Any]]) -> str:
    today = date.today().isoformat()
    lines = [
        f"# Revenue Opportunity Brief — {today}",
        "",
        "> These are research leads, not automatic outreach instructions. Verify the evidence and the target person before contacting anyone.",
        "",
        f"**Qualified opportunities in brief:** {len(opportunities)}",
        "",
    ]

    for idx, item in enumerate(opportunities, start=1):
        track = item.get("opportunity_track") or {}
        roles = item.get("target_person_roles") or []
        evidence = item.get("evidence") or []
        source_url = item.get("source_url")

        lines.extend(
            [
                f"## {idx}. {item.get('company') or 'Unknown company'} — {item.get('title')}",
                f"- **Type:** {item.get('opportunity_type')}",
                f"- **Lane:** {track.get('label') or 'Unclassified'}",
                f"- **Signal category:** {item.get('signal_category') or 'Unclassified'}",
                f"- **Likely owner roles to research:** {', '.join(roles[:5]) if roles else 'Not determined'}",
            ]
        )

        if item.get("description"):
            lines.append(f"- **Why it may matter:** {item['description']}")
        if evidence:
            lines.append(f"- **Evidence:** {'; '.join(evidence[:4])}")
        if source_url:
            lines.append(f"- **Source:** {source_url}")

        lines.extend(
            [
                "- **Human action:** Verify the signal, identify the correct person, then decide whether to apply, request an introduction, or draft a personalized outreach.",
                "",
            ]
        )

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate consulting/fractional opportunity brief.")
    parser.add_argument("--in", dest="in_file", required=True, help="Normalized opportunities JSON")
    parser.add_argument("--out", default="output/revenue_opportunities.md")
    args = parser.parse_args()

    with open(args.in_file, "r", encoding="utf-8") as f:
        opportunities = json.load(f)

    text = format_opportunity_brief(opportunities)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    print(f"Wrote {len(opportunities)} opportunities to {args.out}")


if __name__ == "__main__":
    main()
