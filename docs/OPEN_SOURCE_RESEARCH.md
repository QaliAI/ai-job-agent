# Open Source Research & Repository Audit

> **Product**: AI Job Agent  
> **Philosophy**: Do not reinvent mature open-source work. Build consumer-grade onboarding, local-first privacy, transparent rubric scoring, and anti-hallucination verification on top of the strongest open-source foundations.

---

## Executive Summary

Before building **AI Job Agent**, we conducted a comprehensive technical and legal audit of existing open-source job search tools, ATS APIs, resume tailoring engines, and agent skill libraries.

Our objective was to identify:
1. Proven public ATS interface patterns (avoiding fragile browser scraping).
2. Transparent fit-scoring rubrics (avoiding ungrounded LLM "match percentages").
3. Anti-fabrication QA mechanisms (enforcing candidate ground truth).
4. Portable Agent Skills standards (compatible across Hermes, Claude Code, Codex, Cursor, ChatGPT, etc.).
5. Consumer-grade onboarding needs (closing the gap between developer tooling and everyday job seekers).

---

## Evaluated Repositories & Findings

### 1. `jain777/jobclaw-skills`
* **License**: MIT
* **Last Maintained / Pushed**: June 2026
* **Language / Runtime**: Python / Claude Code & Cursor
* **Architecture**: Collection of ~20 modular skills with Python helper scripts for public ATS boards (Greenhouse, Lever, Ashby, Workday, SmartRecruiters, Teamtailor), RenderCV integration, and email triage.
* **Key Strengths**: 
  - Robust direct ATS board connectors using public endpoints.
  - Deterministic ID hashing and persistent cross-run deduplication store (`jobstore.py`).
  - Strict RenderCV schema mapping without crashing on unrecognized fields.
* **Limitations / Rejections**:
  - Heavily geared toward Claude Code and developer workflows; lacks consumer-friendly onboarding.
  - Hardcoded region assumptions in some modules; lacks an integrated cross-platform UI/installer.
* **Reuse Decision**: **Adapted & Incorporated**. Reused and modernized the ATS endpoint query patterns, deterministic hashing strategy, and schema normalization with proper attribution.

---

### 2. `Remotivated/job-hunt-skills`
* **License**: MIT
* **Last Maintained / Pushed**: August 2026
* **Language / Runtime**: JavaScript / Python / Claude Code / Cowork
* **Architecture**: Agent skills suite covering resume tailoring, cover letters, company research, and an evidence-backed truth verification layer.
* **Key Strengths**:
  - `claim-check` skill: Excellent verification model that flags unsupported metrics, unverified tools, and scope inflation by checking against candidate evidence files.
  - Fictional candidate fixtures (Avery Castillo, Maya Chen) and practical job search philosophy guides.
* **Limitations / Rejections**:
  - Plugin packaging is tied to Cowork/Claude plugins; requires adaptation for Hermes, Codex, Cursor, and standalone CLI.
* **Reuse Decision**: **Adapted & Incorporated**. Reused the anti-fabrication verification philosophy and claim-checking heuristics to build our standalone `claim_check.py` QA engine.

---

### 3. `nuin/resume-tailor`
* **License**: MIT
* **Last Maintained / Pushed**: June 2026
* **Language / Runtime**: Markdown / Claude Code Skill
* **Architecture**: Two-model verification skill that tailors resumes strictly grounded in a master candidate profile.
* **Key Strengths**:
  - Strong emphasis on "Honest Framings" (documenting partial fits and transferable skills truthfully).
  - Clear, modular ATS-friendly markdown resume templates.
* **Limitations / Rejections**:
  - Pure prompt-based skill without automated ATS discovery or scheduling.
* **Reuse Decision**: **Referenced & Adapted**. Adopted the master profile formatting conventions and honest framing guidelines.

---

### 4. `ConorsCode/ats-api-reference`
* **License**: MIT
* **Last Maintained / Pushed**: August 2026
* **Language / Runtime**: HTML / Documentation
* **Architecture**: Verified cross-platform technical reference for 9 major ATS platforms (Greenhouse, Lever, Ashby, Workday, SmartRecruiters, Workable, Recruitee, Personio, BambooHR).
* **Key Strengths**:
  - Exact URL patterns, request parameters, and response structures.
  - Critical production quirk documentation: Greenhouse double-encoded HTML, Personio XML responses, BambooHR/Personio redirect-on-missing behaviors, Workday CXS pagination.
* **Limitations / Rejections**:
  - Documentation only; no executable Python crawler code.
* **Reuse Decision**: **Direct Reference & Implementation Basis**. Served as the authoritative specification for our `ats_engine.py` multi-platform crawler.

---

### 5. `devilscrapes/ats-jobs-api` & `noble-ronin/ats-job-apis`
* **License**: Open / Public Reference
* **Last Maintained / Pushed**: July 2026
* **Architecture**: Public endpoint listings and Apify Actor references for company career boards.
* **Key Strengths**:
  - Confirmed public keyless endpoint patterns for BambooHR, Breezy, and Teamtailor RSS feeds.
* **Limitations / Rejections**:
  - Promotes paid Apify scrapers for complex flows.
* **Reuse Decision**: **Referenced**. Validated public API endpoints for keyless career board ingestion.

---

### 6. `sinaatalay/rendercv`
* **License**: MIT
* **Stars / Community**: 17,000+ stars; industry standard for open-source resume rendering.
* **Language**: Python / Typst / LaTeX
* **Architecture**: Converts structured YAML/JSON into pixel-perfect PDF, Markdown, HTML, and PNG resumes.
* **Key Strengths**:
  - Clean typographic layout, high ATS readability, completely open-source.
* **Limitations / Rejections**:
  - Requires LaTeX/Typst toolchain for local PDF compilation which can be heavy for non-technical users.
* **Reuse Decision**: **Supported as Progressive Enhancement**. We output standard clean ATS Markdown / Plain-Text by default (zero dependency) and provide RenderCV YAML export for users who want compiled PDFs.

---

### 7. `cullenwatson/JobSpy`
* **License**: MIT
* **Language**: Python
* **Architecture**: Scraper library for LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google Jobs.
* **Key Strengths**:
  - Wide coverage across secondary job boards.
* **Limitations / Rejections**:
  - Frequently suffers from anti-bot blocking (Cloudflare/DataDome) and HTML structure breakages.
  - Job boards contain high ratios of duplicate reposts and stale ghost jobs.
* **Reuse Decision**: **Rejected as Core; Kept as Optional Secondary Input**. Core discovery is built on direct ATS APIs to ensure 100% fresh, verified employer postings without rate-limiting or IP bans.

---

### 8. `ApplyU-ai/ResumeAgent` & `narendranathe/tailor-resume`
* **License**: Apache-2.0
* **Architecture**: Complex multi-agent resume optimization and LaTeX compilers.
* **Key Strengths**:
  - JD gap analysis concepts and taxonomy references.
* **Limitations / Rejections**:
  - High installation friction; requires multiple heavy Python/LaTeX dependencies and API keys.
* **Reuse Decision**: **Referenced Concepts Only**. Kept our implementation lightweight, fast, and runnable with zero external API dependencies.

---

### 9. `strelov1/freehire`
* **License**: MIT
* **Language**: Go
* **Architecture**: Full-featured open-source job search engine.
* **Reuse Decision**: **Referenced**. Valuable reference for search indexing and domain filtering.

---

### 10. `workopia/ai-resume-tailor`
* **License**: MIT
* **Language**: Next.js / TypeScript
* **Architecture**: Web-based resume rewrite tool.
* **Reuse Decision**: **Evaluated**. Replaced web-app architecture with local-first privacy-preserving files.

---

## Synthesis Matrix: What AI Job Agent Builds

| Component | Source of Truth / Reference | Our Differentiated Value |
| :--- | :--- | :--- |
| **Direct ATS Feeds** | `ConorsCode/ats-api-reference`, `jain777/jobclaw-skills` | Unified, zero-dependency Python multi-ATS engine (Greenhouse, Lever, Ashby, SmartRecruiters, Workable, Recruitee, BambooHR, Personio, Workday, Teamtailor). |
| **Deduplication & Ledger** | `jain777/jobclaw-skills` | Persistent cross-run ledger with first-seen timestamps, canonical URL resolution, and status tracking. |
| **Candidate Profile** | `nuin/resume-tailor`, `Remotivated/job-hunt-skills` | Separation of Master Profile facts, Search Preferences, Verified Achievements, and STAR Career Stories. |
| **Fit Scoring** | Custom Transparent Rubric | Explainable 6-factor weighted rubric (0–100) with proven vs partial match and hard disqualifiers (NO fake LLM percentages). |
| **Anti-Slop QA** | `Remotivated/job-hunt-skills` (`claim-check`) | Automated 3-way check (Master Profile vs JD vs Tailored Resume) that catches hallucinated skills, metrics, or credentials. |
| **Daily Morning Brief** | Product Requirement | Beautiful, high-signal daily report with top ~10 vetted opportunities, direct application links, and tailored files. |
| **Onboarding UX** | Product Requirement | Zero-jargon non-technical wizard (`START-HERE.md`, `setup.py`, `doctor.py`), cross-platform (Windows & macOS). |
| **Multi-Runtime** | Standard Agent Skills Spec | Portable skill definitions runnable on Hermes, Claude Code, Codex, Cursor, OpenCode, and ChatGPT Desktop. |
