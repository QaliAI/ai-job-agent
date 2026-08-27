---
name: write-cover-letter
description: Generate a concise, high-signal cover letter grounded in candidate verified achievements and career stories.
user-invocable: true
allowed-tools: Read, Write, RunCommand
---

# write-cover-letter

Generates an authentic, evidence-backed cover letter for a specific job posting.

## Guidelines
* Lead with candidate's actual proven technical foundation and admiration for employer's specific engineering domain.
* Provide 2 concrete examples drawn from `VERIFIED_ACHIEVEMENTS.md` demonstrating relevant problem-solving.
* Keep format concise (3-4 paragraphs) with zero AI filler words or generic fluff.
* Run `scripts/claim_check.py` to ensure all claims are 100% grounded in truth.
