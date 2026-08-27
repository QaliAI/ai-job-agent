# Running AI Job Agent with ChatGPT Desktop & Web

If you use **ChatGPT Plus / Team / Pro** (Desktop App or Web), you can use AI Job Agent directly without writing code or using the command line.

---

## Option 1: ChatGPT Projects / Custom GPT (Recommended)

1. **Create a Private Project / Custom GPT**:
   - In ChatGPT, click **Projects** or **Explore GPTs** → **Create a GPT**.
   - Name: `My Personal Job Agent`.

2. **Upload Your Ground Truth Knowledge Files**:
   - Attach your local files from this repository:
     - `candidate/MASTER_PROFILE.md` (your career history)
     - `candidate/SEARCH_PREFERENCES.md` (what you're looking for)
     - `candidate/VERIFIED_ACHIEVEMENTS.md` (your approved metrics)
     - `candidate/skills.json` (your verified skills)
     - `knowledge/rubric_weights.json` (the scoring rubric)

3. **Paste the System Instructions**:
   - Copy the contents of [`skills/tailor-resume/SKILL.md`](../../skills/tailor-resume/SKILL.md) and [`skills/claim-check/SKILL.md`](../../skills/claim-check/SKILL.md) into the GPT Instructions box.
   - Core prompt instruction:
     > *"You are my personal job search staff. When evaluating jobs or tailoring resumes, you must strictly ground all claims in my uploaded MASTER_PROFILE.md and VERIFIED_ACHIEVEMENTS.md. NEVER invent metrics, tools, or employment dates. Always highlight proven strengths and identify legitimate gaps."*

4. **Daily Use**:
   - Paste any job posting URL or job text into ChatGPT.
   - Say: *"Score this job against my profile and prepare a tailored resume draft."*
   - ChatGPT will output your tailored resume and gap analysis instantly.

---

## Option 2: Running Automated Discovery via Python
If you want automated ATS discovery, run the local Python script once a day:
```bash
python scripts/daily_workflow.py
```
Then upload the generated `output/latest_brief.md` into ChatGPT for deep discussion!
