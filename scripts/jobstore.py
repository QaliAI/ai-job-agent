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
            job["first_seen_at"] = existing_record.get("first_seen_at", now_iso)
            job["last_verified_at"] = now_iso
            job["is_new"] = False
            job["user_status"] = existing_record.get("user_status", "unseen")
            
            # Update store record
            existing_record["last_verified_at"] = now_iso
            existing_record["is_live"] = job.get("is_live", True)
        else:
            job["first_seen_at"] = now_iso
            job["last_verified_at"] = now_iso
            job["is_new"] = True
            job["user_status"] = "unseen"
            
            # Add to store
            stored_jobs[job_id] = {
                "id": job_id,
                "company": job.get("company"),
                "title": job.get("title"),
                "location": job.get("location"),
                "apply_url": job.get("apply_url"),
                "first_seen_at": now_iso,
                "last_verified_at": now_iso,
                "user_status": "unseen",
                "is_live": job.get("is_live", True)
            }
            new_list.append(job)
            
        enriched_list.append(job)
        
    store["jobs"] = stored_jobs
    save_store(store, store_path)
    return enriched_list, new_list, dupes_count


Tuple_Merged = tuple[List[Dict[str, Any]], List[Dict[str, Any]], int]


def update_job_status(job_id: str, status: str, store_path: str = DEFAULT_STORE_PATH) -> bool:
    """Updates a job's user_status (e.g. 'applied', 'skipped', 'interviewing')."""
    store = load_store(store_path)
    if job_id in store.get("jobs", {}):
        store["jobs"][job_id]["user_status"] = status
        store["jobs"][job_id]["status_updated_at"] = datetime.now(timezone.utc).isoformat()
        save_store(store, store_path)
        return True
    return False


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
