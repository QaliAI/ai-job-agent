# Running AI Job Agent on Hermes

[Hermes](https://github.com/nousresearch/hermes-agent) is an open-source, autonomous AI agent with local-first tool calling and native cron scheduling.

---

## 1. Quick Setup
1. Clone or link this repository into your Hermes workspace directory:
   ```bash
   git clone https://github.com/QaliAI/ai-job-agent.git
   cd ai-job-agent
   python scripts/setup.py
   ```
2. Hermes will automatically discover the skills in `skills/*/SKILL.md` or via `runtime/hermes/hermes_skills.json`.

---

## 2. Using Hermes Commands
Once in Hermes, you can interact naturally or invoke specific skills:
* `"Run my daily job search and give me the morning brief."` → executes `skills/daily-brief`
* `"Find fresh backend engineering jobs at Stripe, Ramp, and Linear."` → executes `skills/find-jobs`
* `"Score this job description against my master profile: <paste JD>"` → executes `skills/score-fit`
* `"Tailor my resume for this role and run a claim check on it."` → executes `skills/tailor-resume` & `skills/claim-check`
* `"Find consulting and fractional opportunities based on my AI, growth, and automation tracks."` → executes `skills/find-consulting-opportunities`
* `"Research the correct decision-maker for opportunity <id> and show me the evidence."` → executes `skills/research-target-person`

---

## 3. Native Hermes Daily Scheduling
Hermes supports autonomous periodic execution. Add this task to your Hermes schedule config:
```json
{
  "name": "Daily Job Agent Brief",
  "cron": "0 8 * * 1-5",
  "instruction": "Run python scripts/daily_workflow.py and summarize the top opportunities from output/latest_brief.md"
}
```
Hermes will run your job search every weekday morning at 8:00 AM local time and present your morning report.


## 4. Optional Revenue Opportunity Schedule

The deterministic ATS job scan and web-research consulting scan are intentionally separate.
A useful Hermes pattern is to run the consulting/fractional research once each weekday and
only surface evidence-backed changes:

```json
{
  "name": "Revenue Opportunity Brief",
  "cron": "30 8 * * 1-5",
  "instruction": "Use the find-consulting-opportunities skill to look for fresh evidence-backed consulting, fractional, advisory, coaching, AI implementation, growth-systems, and buyer-signal opportunities that match candidate/OPPORTUNITY_TRACKS.json. Deduplicate against prior results, research likely owner roles, and write only new qualified items to output/revenue_opportunities.md. Do not send outreach."
}
```

Keep contact and outreach actions human-reviewed.
