# Public ATS Job Sources Reference

AI Job Agent connects directly to first-party Applicant Tracking System (ATS) public endpoints, eliminating the low-quality reposts, ghost jobs, and scraper breakages associated with secondary aggregators.

---

## Supported Public ATS Platforms

| Platform | Endpoint Pattern | Format | Authentication | Production Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Greenhouse** | `https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true` | JSON | Keyless | Double HTML entity unescaping required; handles pagination gracefully. |
| **Lever** | `https://api.lever.co/v0/postings/{token}?mode=json` | JSON | Keyless | Returns plain text `descriptionPlain` alongside HTML. |
| **Ashby** | `https://api.ashbyhq.com/posting-api/job-board/{token}` | JSON | Keyless | Modern JSON structure with `isRemote` flag and structured compensation. |
| **SmartRecruiters** | `https://api.smartrecruiters.com/v1/companies/{token}/postings` | JSON | Keyless | Supports server-side query parameter `?q={query}`. |
| **Workable** | `https://apply.workable.com/api/v1/widget/accounts/{token}?details=true` | JSON | Keyless | Direct widget endpoint provides complete department and location trees. |
| **Recruitee** | `https://{token}.recruitee.com/api/offers/` | JSON | Keyless | Clean JSON array of active offers. |
| **BambooHR** | `https://{token}.bamboohr.com/careers/list` | JSON | Keyless | Public careers list endpoint. |
| **Personio** | `https://{token}.jobs.personio.de/xml` | XML | Keyless | Clean XML feed containing positions, offices, and job descriptions. |
| **Teamtailor** | `https://{token}.teamtailor.com/jobs.rss` | RSS / XML | Keyless | Public RSS feed common at European startups. |


---

## Adding New Companies to Your Search
Use the built-in sniffer:
```bash
python scripts/discover_ats.py <company_name> --add-to-registry knowledge/ats_patterns.json
```
Example:
```bash
python scripts/discover_ats.py linear --add-to-registry knowledge/ats_patterns.json
```


## Documented but not yet wired: Workday

Workday commonly exposes a public CXS endpoint at `https://{tenant}.wd{N}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs`, using POST pagination. The current AI Job Agent dispatcher does **not** claim Workday support yet because a reliable implementation needs per-board `host`, `tenant`, and `site` configuration rather than the single-token registry schema used by the other adapters. Do not add a Workday company to `knowledge/ats_patterns.json` until that adapter is implemented and tested.
