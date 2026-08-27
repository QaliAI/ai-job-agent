# Agent Runtime Compatibility Matrix

AI Job Agent is built on the open **Agent Skills specification** (`skills/*/SKILL.md`) and standard CLI scripts.

---

## Compatibility Matrix

| Runtime / Agent | Support Level | Discovery Method | Native Scheduling | Notes / Status |
| :--- | :--- | :--- | :--- | :--- |
| **Standalone Python CLI** | **Tier 1 (Full)** | CLI scripts | OS Task Scheduler / launchd / cron | Zero external dependencies; runs on pure Python 3.10+. |
| **Hermes** | **Tier 1 (Full)** | `skills/*/SKILL.md` + `hermes_skills.json` | Native Hermes Cron | First-class agent support with local-first tool calling. |
| **Claude Code** | **Tier 1 (Full)** | `.claude-plugin/plugin.json` + `skills/` | Via external cron / terminal | Automatic slash commands (`/find-jobs`, `/daily-brief`). |
| **Cursor** | **Tier 1 (Full)** | `.cursor/rules/job-agent.mdc` | Via Task Scheduler / terminal | In-editor Composer & Chat integration. |
| **Codex / OpenCode** | **Tier 1 (Full)** | `.codex-plugin/plugin.json` + CLI | Via Task Scheduler / terminal | Full tool invocation and Python script execution. |
| **ChatGPT Desktop / Web** | **Tier 2 (Guided)** | File attachments in Projects / Custom GPT | Manual prompt / CLI | Full support via knowledge file uploads; automated scraping requires local Python helper. |
| **Gemini / Claude Web** | **Tier 2 (Guided)** | File uploads in Projects | Manual prompt | Grounded scoring and resume tailoring using uploaded profile documents. |

---

## Agent Invocation Standard
All skills follow the standard YAML frontmatter contract:
```yaml
---
name: skill-name
description: Clear, action-oriented description of capability
user-invocable: true
allowed-tools: Read, Write, RunCommand
---
```
When invoked by an AI agent, skills read candidate truth from `candidate/`, execute deterministic Python helpers in `scripts/`, run Claim Check QA verification, and write results to `output/`.
