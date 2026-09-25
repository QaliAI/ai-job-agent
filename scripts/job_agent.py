#!/usr/bin/env python3
"""Canonical personal job-agent commands.

    job-agent run --profile lucy
    job-agent digest --profile lucy
    job-agent report --profile lucy
    job-agent status --profile lucy
    job-agent preflight --profile lucy

One implementation. Agent runtimes call this script. There is no auto-apply.
"""

import argparse
import json
import os
import sys
from datetime import date
from typing import Any, Dict, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from daily_workflow import run_daily_pipeline
from digest_report import format_digest, format_status
from email_notifier import render_html_brief
from jobstore import load_store, set_lifecycle
from notify import deliver_digest
from profile_config import (
    fixture_path,
    format_preflight,
    init_profile,
    jobs_per_digest,
    load_user_profile,
    notification_preferences,
    offline_search,
    portals_enabled,
    preflight,
    prefs_from_profile,
    profile_dirs,
    repo_root_from_here,
    resolve_profile_dir,
    scoring_overlay,
    validate_profile_name,
    weights_from_priorities,
    assert_isolated_write,
)


def _tracker_counts(store: Dict[str, Any]) -> Dict[str, int]:
    counts = {"new": 0, "applied": 0, "interview": 0, "rejected": 0, "archived": 0}
    for record in (store.get("jobs") or {}).values():
        status = (record.get("status") or "new").lower()
        if status in counts:
            counts[status] += 1
    return counts


def _write(path: str, profile_dir: str, text: str) -> None:
    assert_isolated_write(path, profile_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def _digest_profile(user: Dict[str, Any], scored_profile: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(scored_profile)
    merged["name"] = user.get("name") or scored_profile.get("name") or "Candidate"
    if user.get("sample"):
        merged["sample"] = True
    if user.get("label"):
        merged["label"] = user["label"]
    return merged


def run_profile(
    profile_dir: str,
    repo_root: Optional[str] = None,
    fixture: Optional[str] = None,
    tailor_top: int = 3,
) -> Dict[str, Any]:
    """Search, score, track, digest, and tailor inside one profile directory."""
    root = os.path.abspath(repo_root or repo_root_from_here())
    profile_dir = os.path.abspath(profile_dir)
    user = load_user_profile(profile_dir)
    dirs = profile_dirs(profile_dir)
    os.makedirs(dirs["jobs"], exist_ok=True)
    os.makedirs(dirs["output"], exist_ok=True)

    chosen = fixture or fixture_path(user, profile_dir, root)
    if chosen and not os.path.exists(chosen):
        chosen = None
    portals_on = portals_enabled(user)
    use_fixture = bool(chosen)
    skip_live = (not portals_on) and not use_fixture

    previous = os.getcwd()
    os.chdir(root)
    try:
        result = run_daily_pipeline(
            candidate_dir=profile_dir,
            output_dir=dirs["output"],
            jobs_dir=dirs["jobs"],
            tailor_top=tailor_top if os.path.exists(os.path.join(profile_dir, "MASTER_PROFILE.md")) else 0,
            mock_input_file=chosen if use_fixture else None,
            skip_live_search=skip_live,
            profile_overlay=scoring_overlay(user),
            prefs_overlay=prefs_from_profile(user),
            weights_overlay=weights_from_priorities(user),
            digest_limit=jobs_per_digest(user),
            verify_live=not offline_search(user),
            prep_applications=True,
            notify_email=False,
        )
    finally:
        os.chdir(previous)

    note = ""
    if result.get("skipped_live_search"):
        note = "Job portals are disabled. No live search was performed. Nothing failed."
    elif use_fixture and not portals_on:
        note = "Job portals are disabled. This run used the configured fixture instead of live boards."

    digest_profile = _digest_profile(user, result.get("profile") or {})
    digest_text = format_digest(
        result.get("top_jobs") or [],
        digest_profile,
        total_scanned=result.get("total_scanned") or 0,
        total_filtered=result.get("total_filtered") or 0,
        note=note,
        today=result.get("date"),
    )
    today = result.get("date") or date.today().isoformat()
    digest_path = os.path.join(dirs["output"], f"digest_{today}.md")
    latest_digest = os.path.join(dirs["output"], "latest_digest.md")
    _write(digest_path, profile_dir, digest_text)
    _write(latest_digest, profile_dir, digest_text)

    store = load_store(dirs["history"])
    html = render_html_brief(
        result.get("top_jobs") or [],
        digest_profile,
        total_scanned=result.get("total_scanned") or 0,
        total_filtered=result.get("total_filtered") or 0,
        tailored_files={},
        tracker_summary=_tracker_counts(store),
    )
    dashboard_path = os.path.join(dirs["output"], "dashboard.html")
    html_path = os.path.join(dirs["output"], "latest_brief.html")
    _write(dashboard_path, profile_dir, html)
    _write(html_path, profile_dir, html)

    subject = f"Job digest — {digest_profile.get('name')} — {today}"
    delivery = deliver_digest(user, html, html_path, subject)

    last_run = {
        "date": today,
        "profile_dir": profile_dir,
        "total_scanned": result.get("total_scanned"),
        "total_filtered": result.get("total_filtered"),
        "note": note,
        "top_jobs": result.get("top_jobs") or [],
        "digest_profile": {
            "name": digest_profile.get("name"),
            "sample": digest_profile.get("sample", False),
            "label": digest_profile.get("label"),
            "title": digest_profile.get("title"),
            "location": digest_profile.get("location"),
            "work_mode_pref": digest_profile.get("work_mode_pref"),
        },
        "digest_path": digest_path,
        "dashboard_path": dashboard_path,
        "notification": delivery,
    }
    last_run_path = os.path.join(dirs["output"], "last_run.json")
    _write(last_run_path, profile_dir, json.dumps(last_run, indent=2, ensure_ascii=False))

    result.update({
        "digest_path": digest_path,
        "dashboard_path": dashboard_path,
        "notification": delivery,
        "profile_dir": profile_dir,
        "note": note,
    })
    return result


def _require_profile(name: str, repo_root: str) -> str:
    try:
        validate_profile_name(name)
    except ValueError as exc:
        raise SystemExit(str(exc))
    path = resolve_profile_dir(name, repo_root)
    if not os.path.isdir(path):
        raise SystemExit(
            f"Profile '{name}' was not found. Create it with: job-agent init --profile {name}"
        )
    has_truth = os.path.exists(os.path.join(path, "profile.json")) or os.path.exists(
        os.path.join(path, "MASTER_PROFILE.md")
    )
    if not has_truth:
        raise SystemExit(f"Profile directory has no profile.json or MASTER_PROFILE.md: {path}")
    return path


def _load_last_run(profile_dir: str) -> Dict[str, Any]:
    path = os.path.join(profile_dir, "output", "last_run.json")
    if not os.path.exists(path):
        raise SystemExit("No digest yet. Run: job-agent run --profile <name>")
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def cmd_init(args: argparse.Namespace, repo_root: str) -> int:
    dest = init_profile(args.profile, repo_root, args.source)
    print(f"Profile ready at {dest}")
    print("Next: add the resume if it is not there, then job-agent preflight --profile " + args.profile)
    return 0


def cmd_preflight(args: argparse.Namespace, repo_root: str) -> int:
    path = resolve_profile_dir(args.profile, repo_root)
    report = preflight(path, repo_root)
    print(format_preflight(report))
    return 0 if report["ok"] else 1


def cmd_run(args: argparse.Namespace, repo_root: str) -> int:
    path = _require_profile(args.profile, repo_root)
    result = run_profile(path, repo_root, fixture=args.fixture, tailor_top=args.tailor_top)
    print(f"Digest: {result.get('digest_path')}")
    print(f"Dashboard: {result.get('dashboard_path')}")
    note = (result.get("notification") or {}).get("message") or (result.get("notification") or {}).get("status")
    print(f"Notification: {note}")
    if result.get("note"):
        print(result["note"])
    return 0


def cmd_digest(args: argparse.Namespace, repo_root: str) -> int:
    path = _require_profile(args.profile, repo_root)
    last = _load_last_run(path)
    user = load_user_profile(path)
    text = format_digest(
        last.get("top_jobs") or [],
        _digest_profile(user, last.get("digest_profile") or {}),
        total_scanned=last.get("total_scanned") or 0,
        total_filtered=last.get("total_filtered") or 0,
        note=last.get("note") or "",
        today=last.get("date"),
    )
    print(text)
    return 0


def cmd_report(args: argparse.Namespace, repo_root: str) -> int:
    path = _require_profile(args.profile, repo_root)
    last = _load_last_run(path)
    user = load_user_profile(path)
    dirs = profile_dirs(path)
    store = load_store(dirs["history"])
    html = render_html_brief(
        last.get("top_jobs") or [],
        _digest_profile(user, last.get("digest_profile") or {}),
        total_scanned=last.get("total_scanned") or 0,
        total_filtered=last.get("total_filtered") or 0,
        tracker_summary=_tracker_counts(store),
    )
    dashboard = os.path.join(dirs["output"], "dashboard.html")
    _write(dashboard, path, html)
    print(dashboard)
    return 0


def cmd_status(args: argparse.Namespace, repo_root: str) -> int:
    path = _require_profile(args.profile, repo_root)
    user = load_user_profile(path)
    store = load_store(profile_dirs(path)["history"])
    print(format_status(store, user))
    channel = notification_preferences(user)["channel"]
    print(f"Notification channel: {channel}")
    print(f"Portals enabled: {portals_enabled(user)}")
    return 0


def cmd_track(args: argparse.Namespace, repo_root: str) -> int:
    path = _require_profile(args.profile, repo_root)
    history = profile_dirs(path)["history"]
    ok = set_lifecycle(args.job, args.status, history, notes=args.notes)
    if not ok:
        print(f"Job '{args.job}' is not in this profile's tracker.")
        return 1
    print(f"Updated {args.job} to {args.status}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="job-agent", description="Personal job agent. No auto-apply.")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Create an empty profile directory")
    init.add_argument("--profile", required=True)
    init.add_argument("--from", dest="source", help="Copy a sample or starter directory")

    pre = sub.add_parser("preflight", help="Show missing requirements for a profile")
    pre.add_argument("--profile", required=True)

    run = sub.add_parser("run", help="Search, score, track, digest, and tailor")
    run.add_argument("--profile", required=True)
    run.add_argument("--fixture", help="Offline jobs JSON. Overrides the profile fixture.")
    run.add_argument("--tailor-top", type=int, default=3)

    digest = sub.add_parser("digest", help="Print the latest digest")
    digest.add_argument("--profile", required=True)

    report = sub.add_parser("report", help="Regenerate the HTML dashboard")
    report.add_argument("--profile", required=True)

    status = sub.add_parser("status", help="Show tracker counts for one profile")
    status.add_argument("--profile", required=True)

    track = sub.add_parser("track", help="Update lifecycle for one job in one profile")
    track.add_argument("--profile", required=True)
    track.add_argument("--job", required=True)
    track.add_argument("--status", required=True, choices=["new", "saved", "applied", "interview", "rejected", "archived"])
    track.add_argument("--notes", default=None)

    return parser


def main(argv: Optional[list] = None) -> int:
    repo_root = repo_root_from_here()
    args = build_parser().parse_args(argv)
    commands = {
        "init": cmd_init,
        "preflight": cmd_preflight,
        "run": cmd_run,
        "digest": cmd_digest,
        "report": cmd_report,
        "status": cmd_status,
        "track": cmd_track,
    }
    return commands[args.command](args, repo_root)


if __name__ == "__main__":
    sys.exit(main())
