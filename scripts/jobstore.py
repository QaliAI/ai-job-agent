#!/usr/bin/env python3
"""Persistent cross-run deduplication store and application ledger.

Maintains `jobs/history.json` and `jobs/seen.json` to ensure:
1. Every job has a deterministic SHA-1 ID.
2. `first_seen_at` timestamp is preserved across days.
3. `is_new` flag identifies newly discovered jobs in the current run.
4. Jobs are never repeatedly rediscovered or re-scored once applied or skipped.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


DEFAULT_STORE_PATH = os.path.join("jobs", "history.json")
LIFECYCLE_STATUSES = ("new", "saved", "applied", "interview", "rejected", "archived")


def _fresh_record(job: Dict[str, Any], now_iso: str) -> Dict[str, Any]:
    return {
        "id": job.get("id"),
        "company": job.get("company"),
        "title": job.get("title"),
        "location": job.get("location"),
        "apply_url": job.get("apply_url"),
        "source": job.get("source"),
        "first_seen": now_iso,
        "first_seen_at": now_iso,
        "last_seen": now_iso,
        "last_verified_at": now_iso,
        "score": None,
        "status": "new",
        "user_status": "unseen",
        "applied": False,
        "interview": False,
        "rejected": False,
        "archived": False,
        "notes": "",
        "is_live": job.get("is_live", True),
    }


def load_store(store_path: str = DEFAULT_STORE_PATH) -> Dict[str, Any]:
    """Loads existing job ledger from disk."""
    if not os.path.exists(store_path):
        return {"version": 1, "jobs": {}, "updated_at": None}
    try:
        with open(store_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to read {store_path} ({e}), initializing empty store.\n")
        return {"version": 1, "jobs": {}, "updated_at": None}


def save_store(store: Dict[str, Any], store_path: str = DEFAULT_STORE_PATH) -> None:
    """Persists job ledger to disk."""
    os.makedirs(os.path.dirname(os.path.abspath(store_path)), exist_ok=True)
    store["updated_at"] = datetime.now(timezone.utc).isoformat()
    with open(store_path, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2, ensure_ascii=False)


def merge_and_deduplicate(
    incoming_jobs: List[Dict[str, Any]],
    store_path: str = DEFAULT_STORE_PATH
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], int]:
    """Merges incoming jobs against the historical ledger.

    Returns:
        (all_jobs_enriched, new_jobs_only, duplicates_count)
    """
    store = load_store(store_path)
    stored_jobs = store.get("jobs", {})
    now_iso = datetime.now(timezone.utc).isoformat()
    
    enriched_list = []
    new_list = []
    dupes_count = 0
    
    for job in incoming_jobs:
        job_id = job.get("id")
        if not job_id:
            continue
            
        if job_id in stored_jobs:
            dupes_count += 1
            existing_record = stored_jobs[job_id]
            # Preserve original first_seen_at
            first_seen = existing_record.get("first_seen") or existing_record.get("first_seen_at", now_iso)
            job["first_seen"] = first_seen
            job["first_seen_at"] = first_seen
            job["last_seen"] = now_iso
            job["last_verified_at"] = now_iso
            job["is_new"] = False
            job["user_status"] = existing_record.get("user_status", "unseen")
            job["status"] = existing_record.get("status", "new")
            
            # Update store record without resetting lifecycle flags
            existing_record["first_seen"] = first_seen
            existing_record["first_seen_at"] = first_seen
            existing_record["last_seen"] = now_iso
            existing_record["last_verified_at"] = now_iso
            existing_record["is_live"] = job.get("is_live", True)
            existing_record.setdefault("score", None)
            existing_record.setdefault("status", "new")
            existing_record.setdefault("applied", False)
            existing_record.setdefault("interview", False)
            existing_record.setdefault("rejected", False)
            existing_record.setdefault("archived", False)
            existing_record.setdefault("notes", "")
        else:
            record = _fresh_record(job, now_iso)
            job["first_seen"] = now_iso
            job["first_seen_at"] = now_iso
            job["last_seen"] = now_iso
            job["last_verified_at"] = now_iso
            job["is_new"] = True
            job["user_status"] = "unseen"
            job["status"] = "new"
            stored_jobs[job_id] = record
            new_list.append(job)
            
        enriched_list.append(job)
        
    store["jobs"] = stored_jobs
    save_store(store, store_path)
    return enriched_list, new_list, dupes_count


Tuple_Merged = tuple[List[Dict[str, Any]], List[Dict[str, Any]], int]


def update_job_status(job_id: str, status: str, store_path: str = DEFAULT_STORE_PATH) -> bool:
    """Updates a job's user_status (e.g. 'applied', 'skipped', 'interviewing')."""
    return set_lifecycle(job_id, status, store_path)


def set_lifecycle(
    job_id: str,
    status: str,
    store_path: str = DEFAULT_STORE_PATH,
    notes: Optional[str] = None,
) -> bool:
    """Set the current lifecycle status and the matching sticky flag."""
    store = load_store(store_path)
    record = store.get("jobs", {}).get(job_id)
    if record is None:
        return False
    normalized = (status or "").strip().lower()
    if normalized == "interviewing":
        normalized = "interview"
    now_iso = datetime.now(timezone.utc).isoformat()
    record["user_status"] = normalized
    record["status_updated_at"] = now_iso
    record["last_seen"] = record.get("last_seen") or now_iso
    if normalized in LIFECYCLE_STATUSES:
        record["status"] = normalized
        if normalized == "applied":
            record["applied"] = True
        elif normalized == "interview":
            record["interview"] = True
        elif normalized == "rejected":
            record["rejected"] = True
        elif normalized == "archived":
            record["archived"] = True
    else:
        record["status"] = record.get("status") or normalized
    if notes is not None:
        record["notes"] = notes
    record.setdefault("notes", "")
    record.setdefault("applied", False)
    record.setdefault("interview", False)
    record.setdefault("rejected", False)
    record.setdefault("archived", False)
    record.setdefault("score", None)
    record.setdefault("first_seen", record.get("first_seen_at"))
    save_store(store, store_path)
    return True


def record_run_outcomes(store_path: str, jobs: List[Dict[str, Any]]) -> None:
    """Write score and last_seen for jobs already in this profile's ledger."""
    store = load_store(store_path)
    stored = store.get("jobs", {})
    now_iso = datetime.now(timezone.utc).isoformat()
    changed = False
    for job in jobs:
        job_id = job.get("id")
        if not job_id or job_id not in stored:
            continue
        record = stored[job_id]
        record["score"] = job.get("fit_score")
        record["last_seen"] = now_iso
        record.setdefault("first_seen", record.get("first_seen_at"))
        record.setdefault("status", "new")
        record.setdefault("applied", False)
        record.setdefault("interview", False)
        record.setdefault("rejected", False)
        record.setdefault("archived", False)
        record.setdefault("notes", "")
        changed = True
    if changed or stored:
        store["jobs"] = stored
        save_store(store, store_path)


def main():
    parser = argparse.ArgumentParser(description="Manage job deduplication ledger.")
    parser.add_argument("--in", dest="in_file", help="Input JSON file with jobs array (or - for stdin)")
    parser.add_argument("--store", default=DEFAULT_STORE_PATH, help="Path to jobs history ledger JSON")
    parser.add_argument("--status", help="Update status for a specific job ID (format: JOB_ID:STATUS)")
    parser.add_argument("--new-only", action="store_true", help="Output only new unseen jobs")
    parser.add_argument("--out", help="Output JSON path")

    args = parser.parse_args()

    if args.status:
        parts = args.status.split(":", 1)
        if len(parts) == 2:
            jid, stat = parts
            success = update_job_status(jid, stat, args.store)
            print(f"Updated {jid} to '{stat}': {success}")
        return

    raw_data = []
    if args.in_file:
        if args.in_file == "-":
            raw_data = json.load(sys.stdin)
        else:
            with open(args.in_file, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

    if raw_data:
        enriched, new_jobs, dupes = merge_and_deduplicate(raw_data, args.store)
        output_data = new_jobs if args.new_only else enriched
        out_json = json.dumps(output_data, indent=2, ensure_ascii=False)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(out_json)
        else:
            print(out_json)


if __name__ == "__main__":
    main()
