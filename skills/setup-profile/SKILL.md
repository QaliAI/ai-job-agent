---
name: setup-profile
description: Create or update the candidate's canonical factual career profile from their resume and answers.
user-invocable: true
allowed-tools: Read, Write, RunCommand
---

# setup-profile

Transform the candidate's raw résumé and search preferences into a durable, local-first source of truth.

## Workflow

1. **Ingest Existing Résumé**:
   - Read user's pasted resume text or file in `candidate/`.
   - Extract strictly verified facts: work history, company names, titles, dates, education, and technical competencies.
   - Do NOT invent metrics or embellish scope.

2. **Establish Files in `candidate/`**:
   - `MASTER_PROFILE.md`: Complete chronological career history, contact info, summary, and honest framing notes.
   - `SEARCH_PREFERENCES.md`: Target roles, work mode (remote/hybrid/onsite), locations, compensation minimum, and company exclusions.
   - `VERIFIED_ACHIEVEMENTS.md`: Bullet points with verified metrics and outcomes.
   - `CAREER_STORIES.md`: STAR-format narratives of key technical challenges.
   - `skills.json`: Categorized JSON taxonomy of proven vs transferable skills.
   - `OPPORTUNITY_TRACKS.json` (optional): Multiple legitimate career/revenue lanes, each with its own search queries and fit signals. Start from `templates/OPPORTUNITY_TRACKS_TEMPLATE.json`.

3. **Configure Multi-Track Search When Needed**:
   - Use opportunity tracks when the candidate plausibly spans distinct role families (for example AI consulting + product building + growth).
   - Keep every track grounded in actual evidence from the profile.
   - Do not create a track merely to chase a posting the candidate cannot support.

4. **Verify Integrity**:
   - Run `python scripts/doctor.py` to confirm profile files are valid and protected by `.gitignore`.
