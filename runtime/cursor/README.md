# Running AI Job Agent in Cursor

[Cursor](https://www.cursor.com) is an AI-powered code editor that seamlessly interprets project rules and scripts.

---

## 1. Setup
1. Open this repository folder in Cursor:
   ```bash
   cursor .
   ```
2. Cursor automatically loads the rules defined in `.cursor/rules/job-agent.mdc`.

---

## 2. Using in Cursor Composer / Chat (`Ctrl+I` / `Cmd+I`)
You can ask Cursor:
* `"Run my daily job search workflow."` → executes `python scripts/daily_workflow.py`
* `"Look at this job description and score it against my master profile: <URL or Text>"`
* `"Tailor my resume for this role and ensure no metrics are fabricated."`
* `"Run claim check QA on output/resumes/draft.md."`
