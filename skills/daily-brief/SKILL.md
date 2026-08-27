---
name: daily-brief
description: Run the complete daily job search cycle, score opportunities, auto-tailor resumes for top roles, and generate the signature Morning Brief.
user-invocable: true
allowed-tools: Read, Write, RunCommand
---

# daily-brief

Orchestrates the entire daily cycle of the AI Job Agent.

## Daily Workflow
1. Load candidate profile and search preferences.
2. Query direct employer ATS boards (Greenhouse, Lever, Ashby, SmartRecruiters, etc.).
3. Deduplicate against `jobs/history.json`.
4. Verify active liveness of postings.
5. Filter hard exclusions (salary, company blacklist, remote mode).
6. Explainable rubric fit scoring and ranking.
7. Select Top 10 opportunities.
8. Auto-tailor resumes for Top 1–3 opportunities with Claim Check QA.
9. Format & save signature Daily Morning Brief (`output/morning_brief_YYYY-MM-DD.md`).
10. Update persistent history ledger.

## Command
```bash
python scripts/daily_workflow.py
```
Outputs the brief in `output/latest_brief.md` and displays action items.
