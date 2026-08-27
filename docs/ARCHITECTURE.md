# AI Job Agent — System Architecture & Data Flow

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
                 |                     |         [3. Ingestion & Schema Normalizer]
                 |                     |         (scripts/ats_engine.py)
                 |                     |         Standardizes to Canonical Job Schema
                 |                     |                    |
                 |                     |                    v
                 |                     |         [4. Persistent Ledger & Dedup]
                 |                     |         (scripts/jobstore.py)
                 |                     |         SHA-1 Hash -> jobs/history.json
                 |                     |                    |
                 |                     |                    v
                 |                     |         [5. Live Freshness Verification]
                 |                     |         (scripts/verify_postings.py)
                 |                     |         Checks HTTP status & Schema.org LD
                 |                     |                    |
                 |                     |                    v
                 +---------------------+-------> [6. Strict Hard Exclusion Filter]
                                       |         (scripts/filter_jobs.py)
                                       |         Drops blacklisted companies,
                                       |         disallowed titles, salary mismatches
                                       |                    |
                                       |                    v
                                       |         [7. Transparent Rubric Fit Scorer]
                                       |         (scripts/scorer.py)
                                       |         6-Factor Weighted Rubric (0-100)
                                       |         Strengths + Material Gap Analysis
                                       |                    |
                                       |                    v
                                       |         [8. Select Top 10 Opportunities]
                                       |                    |
                                       +-------> [9. Grounded Résumé Tailoring Engine]
                                       |         (scripts/tailor_engine.py)
                                       |         Tailors top 1-3 opportunities
                                       |                    |
                                       v                    v
                          [10. Independent Claim QA Verification]
                          (scripts/claim_check.py)
                          Catches hallucinations, invented tools & metrics
                                       |
                                       v
                          [11. Signature Daily Morning Brief]
                          (scripts/morning_brief.py)
                          Saved to output/latest_brief.md
```

---

## 1. Canonical Schemas

### Job Schema
```json
{
  "id": "hash16",
  "source": "greenhouse|lever|ashby|smartrecruiters|workable|recruitee|personio|bamboohr|teamtailor|workday",
  "source_type": "ats_direct",
  "company": "Company Name",
  "title": "Role Title",
  "location": "City, State / Remote",
  "work_mode": "remote|hybrid|onsite|unknown",
  "salary_min": 160000,
  "salary_max": 200000,
  "currency": "USD",
  "employment_type": "Full-time",
  "description": "Cleaned plaintext job description",
  "posted_at": "ISO-8601 string or null",
  "first_seen_at": "ISO-8601 string",
  "last_verified_at": "ISO-8601 string",
  "apply_url": "https://...",
  "canonical_url": "https://...",
  "is_live": true
}
```

### Rubric Scoring Formula
$$\text{Score} = 0.25 \cdot T + 0.25 \cdot S + 0.15 \cdot E + 0.15 \cdot D + 0.10 \cdot L + 0.10 \cdot P$$
Where:
* $T$ = Title & Role Relevance (0–100)
* $S$ = Core Required Skills Match (0–100)
* $E$ = Seniority & Years of Experience (0–100)
* $D$ = Domain & Industry Fit (0–100)
* $L$ = Location & Work Arrangement (0–100)
* $P$ = Preferred Qualifications & Nice-to-Haves (0–100)

---

## 2. Anti-Fabrication Invariants
1. **Source Authorization**: No claim may appear on a tailored resume or cover letter that is not substantiated by `candidate/MASTER_PROFILE.md` or `candidate/VERIFIED_ACHIEVEMENTS.md`.
2. **Metric Integrity**: Numbers, percentages, and dollar figures must exist in candidate ground truth.
3. **Continuous Verification**: `scripts/claim_check.py` validates drafts before saving.
