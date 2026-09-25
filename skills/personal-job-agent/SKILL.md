---
name: personal-job-agent
description: Run the personal job agent for one profile. Search, score, track, digest, and tailor without auto-apply.
user-invocable: true
allowed-tools: Read, Write, RunCommand
---

# personal-job-agent

This is the canonical workflow. Call the script. Do not reimplement search, scoring, or tailoring in the chat.

## Commands

```bash
python scripts/job_agent.py preflight --profile PROFILE
python scripts/job_agent.py run --profile PROFILE
python scripts/job_agent.py digest --profile PROFILE
python scripts/job_agent.py report --profile PROFILE
python scripts/job_agent.py status --profile PROFILE
python scripts/job_agent.py track --profile PROFILE --job JOB_ID --status applied
```

Windows: `job-agent.cmd`. macOS and Linux: `./job-agent`.

## Rules

- One profile directory per person. Never read or write another profile's `jobs/` or `output/`.
- Do not invent employers, titles, dates, degrees, certifications, skills, accomplishments, revenue, metrics, or team size.
- Do not enable live portals unless `profile.json` sets `portals.enabled` to true.
- If email credentials are missing, leave the saved digest in place. Do not fail the run.
- There is no auto-apply.
