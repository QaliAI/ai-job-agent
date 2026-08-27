---
name: find-jobs
description: Discover fresh job postings straight from public employer ATS feeds (Greenhouse, Lever, Ashby, SmartRecruiters, etc.) and deduplicate against the history ledger.
user-invocable: true
allowed-tools: Read, Write, RunCommand
---

# find-jobs

Searches direct employer career endpoints, normalizes postings to the canonical schema, deduplicates against `jobs/history.json`, and verifies active link status.

## Usage

```bash
# Query ATS boards for target query
python scripts/ats_engine.py --registry knowledge/ats_patterns.json --query "backend" --out jobs/found-today.json

# Deduplicate against history ledger
python scripts/jobstore.py --in jobs/found-today.json --store jobs/history.json --out jobs/fresh-today.json
```

## Schema Guarantee
Every job is guaranteed to match the canonical schema with `id`, `company`, `title`, `location`, `work_mode`, `salary_min`, `salary_max`, `description`, `apply_url`, `canonical_url`, and `is_live`.
