---
name: find-broad-jobs
description: Search a broader multi-company tech job corpus using FreeHire's public API, then normalize results into the AI Job Agent schema.
user-invocable: true
allowed-tools: Read, Write, RunCommand
---

# find-broad-jobs

Use this when the direct employer registry is too narrow.

## Source boundary

This skill queries the public, unauthenticated freehire.dev API. FreeHire is a third-party aggregator / hosted service, not a first-party employer ATS. Treat it as a **supplemental discovery source**, not as proof that a posting is still live.

The direct application URL remains in each result. Before prioritizing a role, run normal liveness verification and prefer the original employer posting when available.

## Command

```bash
python scripts/freehire_source.py --query "AI Enablement Engineer" --days 30 --country US --limit 50
```

Set `FREEHIRE_API_URL` to point at a compatible self-hosted backend.

## Rules

- Keep this source optional and gracefully degradable.
- Do not require an API key.
- Deduplicate against direct ATS results.
- Preserve `source_type=aggregator_public_api`.
- Do not present FreeHire results as direct-employer discovery.
