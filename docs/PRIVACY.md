# Privacy & Data Sovereignty Architecture

> **Core Commitment**: Your career data belongs exclusively to you. AI Job Agent is 100% local-first and privacy-conscious.

---

## 1. Zero Cloud Telemetry & Zero External Hosting
* **No Remote Database**: Your career data, resume, phone number, email address, salary expectations, and application history live strictly on your local disk.
* **No Tracking**: AI Job Agent contains zero tracking pixels, telemetry events, or user analytics.
* **Direct Network Calls Only**: Network requests are made directly from your machine to public employer ATS APIs (Greenhouse, Lever, Ashby, etc.) to fetch public career postings.

---

## 2. Git Protection Boundaries
The repository is configured with a strict, multi-layered `.gitignore` that guarantees personal files are never staged or committed:
* `candidate/MASTER_PROFILE.md` — 🔒 Ignored
* `candidate/SEARCH_PREFERENCES.md` — 🔒 Ignored
* `candidate/VERIFIED_ACHIEVEMENTS.md` — 🔒 Ignored
* `candidate/CAREER_STORIES.md` — 🔒 Ignored
* `candidate/skills.json` — 🔒 Ignored
* `candidate/*.pdf`, `candidate/*.docx` — 🔒 Ignored
* `output/resumes/*` — 🔒 Ignored
* `jobs/history.json` — 🔒 Ignored
* `.env` / credentials — 🔒 Ignored

---

## 3. Fictional Test Fixtures Only
The repository includes fictional candidate fixtures (`examples/jordan-taylor/`, `examples/alex-chen/`) for automated testing and documentation demonstrations. Real candidate profiles are never used in test suites or checked into version control.
