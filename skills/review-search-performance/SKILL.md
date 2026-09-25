---
name: review-search-performance
description: Analyze accumulated job and revenue outcomes by opportunity lane and source to decide where future search effort should go.
user-invocable: true
allowed-tools: Read, Write, RunCommand
---

# review-search-performance

Generate a factual funnel summary from the persistent outcome ledger.

```bash
python scripts/outcome_ledger.py summary --out output/outcome_summary.md
```

Use the report to answer:
- Which opportunity tracks are producing replies, interviews, meetings, proposals, offers, hires, or wins?
- Which sources produce useful opportunities versus noise?
- Are consulting/fractional lanes converting better than W-2 lanes?
- Which searches should receive more or less attention?

## Guardrail

Outcome data may change **where the agent searches** and **which opportunities it prioritizes**. It must never cause the agent to fabricate candidate experience or rewrite historical facts to fit the market.
