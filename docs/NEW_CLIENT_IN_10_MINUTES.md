# New client in 10–15 minutes

One command runs the workflow: `job-agent run --profile <name>`. There is no auto-apply. The person reviews the digest and submits applications themselves.

Claude Code is the reference runtime. The same `scripts/job_agent.py` commands are what Hermes, Cursor, Codex, and a plain terminal call. Do not keep a second copy of the workflow in each runtime.

## 1. Clone and check Python

```bash
git clone https://github.com/QaliAI/ai-job-agent.git
cd ai-job-agent
python --version
```

Python 3.10 or newer is enough. There is no package install.

On Windows you can run `job-agent.cmd`. On macOS or Linux, `./job-agent`. Both call `python scripts/job_agent.py`.

## 2. Pick the runtime

| If they will... | Use |
| --- | --- |
| Run a terminal themselves | `job-agent.cmd` or `./job-agent` |
| Work inside Claude Code | Open this repo and use the `personal-job-agent` skill, which shells out to the same script |
| Use Hermes, Cursor, or Codex | The skill files in `skills/` point at the same script |

## 3. Create the profile

Real profiles live in `profiles/<name>/`. That directory is gitignored.

```bash
job-agent init --profile lucy
```

`profiles/lucy/profile.json` lists every optional field. Leave a field empty when you do not have it. Do not invent work authorization, salary, or skills.

Put their resume at the path in `source_resume` (default `profiles/lucy/resume.md`). If you already have a structured profile, also add `MASTER_PROFILE.md` and `skills.json` in that same directory. The sample in `examples/sample-client/` shows the shape. It is fiction.

Minimum that must exist before a run:

- the profile directory
- a resume or `MASTER_PROFILE.md`

## 4. Configure job portals

In `profile.json`:

```json
"portals": { "enabled": false }
```

Leave portals off until the client wants live employer boards. A disabled portal does not fail the run. The digest says search was skipped.

To search a saved JSON file instead:

```json
"search": { "fixture": "fixtures/jobs.json", "offline": true }
```

When they are ready for live boards, set `"portals": { "enabled": true }` and set `"offline"` to false. Live search uses the existing ATS connectors. This package does not add a new scraper.

## 5. Preflight

```bash
job-agent preflight --profile lucy
```

`NOT READY` means a required file is missing. Warnings (no salary, no email credentials, portals off) are allowed. Fix blockers only, then continue.

## 6. First search

```bash
job-agent run --profile lucy
```

This writes, inside that profile only:

- `output/digest_YYYY-MM-DD.md` and `output/latest_digest.md`
- `output/dashboard.html`
- `output/resumes/` and `output/applications/<job>/` for the top matches
- `jobs/history.json` with first seen, last seen, score, and status

Other commands:

```bash
job-agent digest --profile lucy
job-agent report --profile lucy
job-agent status --profile lucy
job-agent track --profile lucy --job JOB_ID --status applied --notes "Submitted on the company site"
```

Statuses: `new`, `saved`, `applied`, `interview`, `rejected`, `archived`.

## 7. Schedule the weekday run

Windows, from the repo root:

```powershell
powershell -ExecutionPolicy Bypass -File .\runtime\scheduling\windows_schedule.ps1 -Profile lucy
```

macOS and Linux: use the launchd or cron examples in `runtime/scheduling/`, with this command instead of the older script:

```text
python3 scripts/job_agent.py run --profile lucy
```

## 8. Mail, if they want it

Set the recipient on the profile, not in the repo:

```json
"notification": { "channel": "email", "to": "lucy@example.com" }
```

Provide `SMTP_HOST`, `SMTP_USER`, `SMTP_PASS`, and `SMTP_FROM`, or `RESEND_API_KEY`, in the environment on the machine that runs the job. If those are missing, the run still saves the digest and the HTML dashboard.

## What the tailored packet will and will not do

For the top matches the run writes a resume, a cover-letter draft, a fit summary, and interview notes. It may reorder and rephrase what is already in the profile. It will not add employers, titles, dates, degrees, certifications, skills, accomplishments, revenue, metrics, or team size. Gaps stay visible in the digest.

## Prove the path with the sample

```bash
job-agent preflight --profile sample-client
job-agent run --profile sample-client
```

`sample-client` is Avery Quinn, a synthetic person under `examples/sample-client/`. The run uses a local fixture and does not query live boards. Read `examples/sample-client/output/latest_digest.md` after the run, then delete that output if you do not want it on disk. Do not turn the sample into a real client. Start a new profile name.
