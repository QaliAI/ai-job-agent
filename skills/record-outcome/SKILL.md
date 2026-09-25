---
name: record-outcome
description: Record what actually happened to a job, consulting lead, fractional opportunity, or buyer-signal lead.
user-invocable: true
allowed-tools: Read, Write, RunCommand
---

# record-outcome

Use this after a meaningful search or revenue event.

Examples:
- applied to a job;
- recruiter replied;
- interview scheduled;
- consulting lead contacted;
- prospect replied;
- meeting held;
- proposal sent;
- offer received;
- project won/lost;
- job rejected / withdrawn.

## Command

```bash
python scripts/outcome_ledger.py record \
  --id <opportunity-id> \
  --status interview \
  --company "Example Co" \
  --title "AI Enablement Engineer" \
  --kind employment \
  --track ai-transformation-enablement \
  --source greenhouse \
  --note "First interview scheduled"
```

Do not record invented values or outcomes.
