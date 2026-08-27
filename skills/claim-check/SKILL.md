---
name: claim-check
description: Run an independent factual verification pass comparing tailored materials against candidate ground truth to catch hallucinations and unsupported claims.
user-invocable: true
allowed-tools: Read, Write, RunCommand
---

# claim-check

Performs an independent verification QA pass comparing draft materials against candidate ground truth (`MASTER_PROFILE.md`, `VERIFIED_ACHIEVEMENTS.md`, `skills.json`).

## Verification Scope
1. **Tool & Skill Check**: Ensures every technical tool mentioned in the draft is present in candidate's verified skills list.
2. **Metric Verification**: Verifies numbers, percentages, and dollar amounts against the achievement bank.
3. **Employer & Date Integrity**: Ensures no employer name or employment timeline has been altered.
4. **Scope Sanity**: Catches unverified executive or leadership claims.

## Running QA Check
```bash
python scripts/claim_check.py --candidate candidate --draft output/resumes/draft_resume.md
```
Outputs `STATUS: PASSED` or flags itemized line violations.
