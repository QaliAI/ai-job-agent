# Running AI Job Agent in Claude Code

[Claude Code](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview) is Anthropic's CLI agent. AI Job Agent installs seamlessly into Claude Code via the standard Agent Skills protocol.

---

## 1. Installation
1. Clone this repository into your workspace:
   ```bash
   git clone https://github.com/QaliAI/ai-job-agent.git
   cd ai-job-agent
   python scripts/setup.py
   ```
2. Start Claude Code in this folder:
   ```bash
   claude
   ```

---

## 2. In-Session Commands
Claude Code will automatically detect all skills in `skills/`:
* `/daily-brief` — Runs the morning job search pipeline, scores opportunities, and produces the daily summary.
* `/find-jobs` — Scans direct employer ATS boards (Greenhouse, Lever, Ashby, SmartRecruiters, etc.).
* `/score-fit` — Evaluates a pasted job description against your `candidate/MASTER_PROFILE.md`.
* `/tailor-resume` — Builds an ATS-safe resume for a specific job without hallucinations.
* `/claim-check` — Performs an independent QA verification pass to verify all claims against ground truth.
* `/write-cover-letter` — Drafts an authentic cover letter drawn from your STAR story bank.
