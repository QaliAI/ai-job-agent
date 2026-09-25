# 🤖 AI Job Agent

> **A free, local-first, privacy-conscious autonomous AI job search staff.**  
> Turns AI tools you already have — **Hermes, Claude Code, ChatGPT, Cursor, Codex, OpenCode** — into your personal job search team.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Zero External Dependencies](https://img.shields.io/badge/dependencies-zero-success.svg)](scripts/)
[![Privacy: Local--First](https://img.shields.io/badge/privacy-100%25%20local--first-green.svg)](docs/PRIVACY.md)

---

## ⚡ Above The Fold: Everything You Need To Know

| Question | Answer |
| :--- | :--- |
| **What is this?** | An autonomous AI job search staff that finds fresh job openings directly from employer career boards, scores them using a transparent rubric, points out real gaps, tailors resumes with **zero hallucinations**, and delivers a clean morning report every day. |
| **Why should I care?** | **This is NOT a spray-and-pray auto-apply bot.** Ten vetted, high-match opportunities with tailored resumes beat 500 spam applications. AI does the tedious research, deduplication, and drafting — you make the final review and submission. |
| **Can I use it?** | **Yes.** Built for normal job seekers. No developer experience needed. Works out-of-the-box on Windows, macOS, and Linux. |
| **What do I need?** | Standard Python 3.10+ (pre-installed or free download) and your existing résumé. No paid API subscriptions required. |
| **What do I do next?** | Follow the **[10-Minute Quickstart](#-10-minute-quickstart)** below or read **[START-HERE.md](START-HERE.md)**. |

---

## 🌟 Key Capabilities

* 🌐 **Direct-From-The-Source ATS Discovery**: Scans public career endpoints directly (Greenhouse, Lever, Ashby, SmartRecruiters, Workable, Recruitee, BambooHR, Personio, Teamtailor, Workday) — no repost aggregators, no ghost jobs.
* ⚖️ **Explainable Rubric Fit Scoring**: Evaluates candidate fit across a transparent 6-factor weighted rubric (0–100) with explicit strength and material gap disclosures (no fake LLM match percentages).
* 🛡️ **Strict Anti-Slop / Anti-Fabrication QA**: Every claim on a tailored resume or cover letter is independently verified against your candidate ground truth by `scripts/claim_check.py`. **Zero invented metrics, fake skills, or inflated scopes.**
* 🌅 **Signature Daily Morning Brief**: Produces an executive report summarizing fresh postings, fit scores, rationale, direct employer application links, and tailored files.
* 🧭 **Multi-Track Opportunity Hunting**: Supports candidates who legitimately span several lanes (for example AI transformation, product building, growth systems, and fractional advisory) instead of forcing everything into one title.
* 💼 **Consulting / Fractional / Buyer-Signal Research**: Normalizes non-job revenue opportunities separately from employment postings, retains source evidence, and recommends the executive/function roles most likely to own the problem.
* 👤 **Evidence-Backed Person Targeting**: Researches the actual decision-maker only after an opportunity is qualified; no invented names, emails, or mass outreach.
* 🗄️ **Persistent Application Ledger**: Maintains `jobs/history.json` so you never see or re-process duplicate opportunities across daily runs.
* 🔒 **100% Local-First & Privacy Guaranteed**: Your resume, contact details, and application materials live strictly in your private local directory and are protected from accidental git commits.

---

## 🏗️ Architecture & Dataflow

```
+-------------------------------------------------------------------------------+
|                             AI JOB AGENT CORE                                 |
+-------------------------------------------------------------------------------+
                                       |
    [1. Candidate Ground Truth]        |        [2. Direct Public ATS Feeds]
    --------------------------         |        ----------------------------
    candidate/MASTER_PROFILE.md        |        Greenhouse  Lever    Ashby
    candidate/SEARCH_PREFERENCES.md    |        Workday     Recruitee  SmartRecruiters
    candidate/VERIFIED_ACHIEVEMENTS.md |        Personio    BambooHR  Teamtailor
    candidate/skills.json              |                    |
                 |                     |                    v
                 |                     |         [3. Ingestion & Normalizer]
                 |                     |         (scripts/ats_engine.py)
                 |                     |                    |
                 |                     |                    v
                 |                     |         [4. Persistent Ledger & Dedup]
                 |                     |         (scripts/jobstore.py)
                 |                     |                    |
                 |                     |                    v
                 |                     |         [5. Live Freshness Verification]
                 |                     |         (scripts/verify_postings.py)
                 |                     |                    |
                 |                     |                    v
                 +---------------------+-------> [6. Hard Exclusion Filter]
                                       |         (scripts/filter_jobs.py)
                                       |                    |
                                       |                    v
                                       |         [7. Rubric Fit Scorer]
                                       |         (scripts/scorer.py)
                                       |                    |
                                       |                    v
                                       |         [8. Select Top 10 Opportunities]
                                       |                    |
                                       +-------> [9. Grounded Résumé Tailoring]
                                       |         (scripts/tailor_engine.py)
                                       |                    |
                                       v                    v
                          [10. Independent Claim QA Check]
                          (scripts/claim_check.py)
                                       |
                                       v
                          [11. Signature Daily Morning Brief]
                          (output/latest_brief.md)
```

---

## ⏱️ 10-Minute Quickstart

### Step 1: Clone and Run Setup Wizard
```bash
# 1. Clone repository
git clone https://github.com/QaliAI/ai-job-agent.git
cd ai-job-agent

# 2. Run guided setup wizard (creates your local private profile)
python scripts/setup.py
```
*(On macOS/Linux, use `python3 scripts/setup.py`)*

### Step 2: Add Your Real Experience
Open `candidate/MASTER_PROFILE.md` and paste your actual work history, verified skills, and contact details.

### Step 3: Run Your Daily Job Search
```bash
python scripts/daily_workflow.py
```
In seconds, your morning brief will be generated in `output/latest_brief.md` and tailored resumes will be saved to `output/resumes/`!

---

## 🌅 Example Morning Brief Report

```markdown
# 🌅 Daily Job Search Brief — 2026-08-27

**Candidate**: Jordan Taylor (Senior Backend Engineer)
**Target Roles**: Senior Backend Engineer, Distributed Systems Engineer
**Work Mode**: Remote Only | **Target Salary**: $180k – $220k USD

---

## 📊 Executive Summary
* **Total Postings Scanned**: 128
* **Passed Strict Filters**: 42
* **Top Opportunities Identified**: **8**
* **Tailored Resumes Prepared & Verified**: **3**

---

## 🎯 Top Opportunities (Direct Employer Postings)

### 1. [Stripe] — Senior Backend Engineer, Payments Infrastructure
* **Fit Score**: **94/100** | **Confidence**: High | **Recommendation**: **APPLY**
* **Location**: Remote (US) | **Compensation**: $195,000 – $235,000 USD + Equity
* **Source**: Greenhouse Direct · **Status**: Live & Verified
* **Key Strengths**: High-throughput backend architecture, Go/Python, PostgreSQL optimization, Kafka streaming
* **Identified Gaps**: Job mentions Ruby for legacy services; Jordan has Python/Go background (transferable)
* **Tailored Résumé**: `output/resumes/2026-08-27_stripe_senior-backend.md` (Claim QA: 100% Grounded)
* **Direct Application Link**: https://boards.greenhouse.io/stripe/jobs/5928104

---

### 2. [Ramp] — Staff Distributed Systems Engineer
* **Fit Score**: **91/100** | **Confidence**: High | **Recommendation**: **APPLY**
* **Location**: Remote (US) | **Compensation**: $210,000 – $245,000 USD + Equity
* **Source**: Ashby Direct · **Status**: Live & Verified
* **Key Strengths**: Background task execution engine, Redis, PostgreSQL performance tuning
* **Identified Gaps**: None on core requirements
* **Tailored Résumé**: `output/resumes/2026-08-27_ramp_staff-distributed-systems.md` (Claim QA: 100% Grounded)
* **Direct Application Link**: https://jobs.ashbyhq.com/ramp/8831920
```

---

## 🤖 Supported Agent Runtimes

AI Job Agent adheres to the open **Agent Skills specification** (`skills/*/SKILL.md`) and standard tool interfaces.

| Runtime / Agent | Support Level | Discovery Method | Setup Guide |
| :--- | :--- | :--- | :--- |
| **Standalone CLI** | **Tier 1 (Full)** | `scripts/daily_workflow.py` | [START-HERE.md](START-HERE.md) |
| **Hermes** | **Tier 1 (Full)** | `skills/` + `hermes_skills.json` | [runtime/hermes/](runtime/hermes/README.md) |
| **Claude Code** | **Tier 1 (Full)** | `.claude-plugin/plugin.json` + `skills/` | [runtime/claude-code/](runtime/claude-code/README.md) |
| **Cursor** | **Tier 1 (Full)** | `.cursor/rules/job-agent.mdc` | [runtime/cursor/](runtime/cursor/README.md) |
| **Codex / OpenCode** | **Tier 1 (Full)** | `.codex-plugin/plugin.json` | [runtime/codex/](runtime/codex/README.md) |
| **ChatGPT (Web/App)** | **Tier 2 (Guided)** | File uploads in Projects / Custom GPT | [runtime/chatgpt/](runtime/chatgpt/README.md) |

---

## ⚖️ Feature Comparison

| Feature | AI Job Agent | Mass Auto-Apply Bots | Generic Job Boards |
| :--- | :---: | :---: | :---: |
| **Direct Employer Postings** | ✅ 100% Direct ATS | ❌ Scrapes aggregators | ❌ Heavy repost duplication |
| **Anti-Hallucination QA** | ✅ Built-in Claim Check | ❌ Unchecked LLM output | ❌ N/A |
| **Transparent Rubric Scoring** | ✅ Explainable 6 factors | ❌ Fake "98% match" | ❌ Keyword density only |
| **Personal Data Privacy** | ✅ 100% Local-First | ❌ Stored on third-party servers | ❌ Sold to recruiters |
| **Free & Open Source** | ✅ MIT Licensed | ❌ Paid subscriptions | ❌ Ads & paywalls |
| **Human In The Loop** | ✅ Human reviews & submits | ❌ Spam submissions (banned by ATS) | ❌ Manual search fatigue |

---

## 📅 Daily Automation & Scheduling

* **Windows**: Run `powershell -ExecutionPolicy Bypass -File .\runtime\scheduling\windows_schedule.ps1` to register an automated 8:00 AM daily background task.
* **macOS**: Follow the launchd instructions in **[docs/MACOS.md](docs/MACOS.md)**.
* **Hermes**: Configure native cron scheduling as detailed in **[runtime/hermes/README.md](runtime/hermes/README.md)**.

---

## 🔒 Privacy Guarantee

Your career history contains sensitive personal data. AI Job Agent is designed from day one to protect your privacy:
* All files in `candidate/`, `jobs/`, and `output/` are **automatically ignored by `.gitignore`**.
* No data is ever sent to third-party tracking services or external databases.
* For more information, read **[docs/PRIVACY.md](docs/PRIVACY.md)**.

---

## 📚 Documentation & Guides

* **[START-HERE.md](START-HERE.md)** — Plain-language quickstart guide for non-technical users.
* **[SETUP-WIZARD.md](SETUP-WIZARD.md)** — Step-by-step onboarding walkthrough.
* **[docs/OPEN_SOURCE_RESEARCH.md](docs/OPEN_SOURCE_RESEARCH.md)** — Full audit of 10+ open source projects.
* **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** — In-depth architectural specification and dataflow.
* **[docs/MULTI_TRACK_OPPORTUNITY_HUNTER.md](docs/MULTI_TRACK_OPPORTUNITY_HUNTER.md)** — Multi-lane job, consulting, buyer-signal, and decision-maker targeting model.
* **[docs/JOB-SOURCES.md](docs/JOB-SOURCES.md)** — Technical details on supported public ATS endpoints.
* **[docs/WINDOWS.md](docs/WINDOWS.md)** & **[docs/MACOS.md](docs/MACOS.md)** — OS-specific operational guides.
* **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** — Diagnostic solutions and FAQ.

---

## 🤝 Open Source Attribution

AI Job Agent proudly builds upon, adapts, and credits foundational open-source work:
* **JobClaw Skills** (`jain777/jobclaw-skills`, MIT) — ATS query patterns, deterministic hashing, and jobstore design.
* **Job Hunt Skills** (`Remotivated/job-hunt-skills`, MIT) — Evidence-layer verification and anti-fabrication QA concepts.
* **ATS API Reference** (`ConorsCode/ats-api-reference`, MIT) — Public ATS endpoint patterns and production quirk documentation.
* **Resume Tailor** (`nuin/resume-tailor`, MIT) — Grounded master profile formatting and honest framing concepts.
* **RenderCV** (`sinaatalay/rendercv`, MIT) — Resume layout standards and schema compatibility.

See **[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)** for full copyright notices and licenses.

---

## 📄 License

Distributed under the **MIT License**. See **[LICENSE](LICENSE)** for details.
