# Step-by-Step Setup Wizard Guide

This guide walks you through setting up your **AI Job Agent** profile step by step.

---

## 1. Initializing Your Profile

Run the setup wizard in your terminal:
```bash
python scripts/setup.py
```

This creates 5 core files in your private `candidate/` directory:

| File | What goes in it |
| :--- | :--- |
| **`candidate/MASTER_PROFILE.md`** | Your complete career history, titles, dates, contact details, and honest context notes. |
| **`candidate/SEARCH_PREFERENCES.md`** | Target roles, locations (remote/hybrid/onsite), minimum compensation, and company exclusions. |
| **`candidate/VERIFIED_ACHIEVEMENTS.md`** | Bullet points containing real metrics and outcomes you have achieved. |
| **`candidate/CAREER_STORIES.md`** | STAR-method narratives (Situation, Task, Action, Result) for cover letters and interview prep. |
| **`candidate/skills.json`** | Structured list of your proven and transferable skills. |

---

## 2. Filling Out Your Master Profile

Open `candidate/MASTER_PROFILE.md` in any text editor (Notepad, VS Code, TextEdit) and update:
1. **Contact Information**: Full name, email, phone number, location, and LinkedIn/GitHub links.
2. **Work Experience**: Your actual employers, job titles, start/end dates, and project descriptions.
3. **Honest Framings**: Notes on partial fits (e.g. tools you've experimented with vs primary production tools).

---

## 3. Running System Diagnostics

Verify that your environment is properly configured:
```bash
python scripts/doctor.py
```
You should see all green checkmarks (`✓`) confirming Python version, `.gitignore` privacy boundaries, candidate files, and ATS network connectivity.

---

## 4. Running Your Daily Job Search

Execute the autonomous daily workflow:
```bash
python scripts/daily_workflow.py
```
This will:
1. Fetch fresh postings directly from Greenhouse, Lever, Ashby, and SmartRecruiters.
2. Deduplicate against your history ledger (`jobs/history.json`).
3. Verify that links are live and filter out hard exclusions.
4. Score and rank opportunities against your profile.
5. Auto-tailor resumes for your top opportunities in `output/resumes/`.
6. Write your daily report to `output/latest_brief.md`.

---

## 5. Setting Up Daily Automation

* **Windows**: Run `powershell -ExecutionPolicy Bypass -File .\runtime\scheduling\windows_schedule.ps1`
* **macOS**: Follow the instructions in [`docs/MACOS.md`](docs/MACOS.md) to enable native `launchd` daily execution at 8:00 AM.
