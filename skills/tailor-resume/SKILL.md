---
name: tailor-resume
description: Tailor candidate resume emphasis and structure to a specific job posting without fabricating any skills, dates, or metrics.
user-invocable: true
allowed-tools: Read, Write, RunCommand
---

# tailor-resume

Creates an ATS-safe tailored resume for a specific job posting, grounded 100% in candidate profile truth.

## Grounded Tailoring Rules

### Permitted:
* Reordering skill categories to lead with the target job's primary technologies.
* Selecting relevant achievements from `VERIFIED_ACHIEVEMENTS.md` that address the job's core technical challenges.
* Aligning phrasing to industry-standard action verbs (`knowledge/action_verbs.json`).
* Tailoring the Professional Summary statement to highlight relevant proven years and domain experience.

### Strictly Forbidden:
* ❌ Fabricating skills candidate never verified in `skills.json` or `MASTER_PROFILE.md`.
* ❌ Inventing metrics, dollar values, or percentages.
* ❌ Modifying official employer names, employment dates, or educational credentials.
* ❌ Inflating ownership scope or authority.

Every tailored resume is automatically validated by `scripts/claim_check.py` before release.
