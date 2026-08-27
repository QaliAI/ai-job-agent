# Troubleshooting & FAQ

---

## 1. Diagnostics Tool
Whenever you encounter an issue, first run the automated health check:
```bash
python scripts/doctor.py
```
This tests your Python version, `.gitignore` privacy boundaries, candidate files, and network reachability to employer ATS APIs.

---

## 2. Common Issues & Solutions

### `UnicodeEncodeError: 'charmap' codec can't encode character...`
* **Cause**: Windows default terminal character encoding (`cp1252`).
* **Solution**: AI Job Agent scripts automatically configure Python streams to UTF-8. If using legacy `cmd.exe`, run `chcp 65001` first or use Windows Terminal / PowerShell.

### `HTTP Error 404 / 403 on ATS Endpoint`
* **Cause**: An employer may have recently changed their ATS token or migrated platforms (e.g. from Greenhouse to Ashby).
* **Solution**: AI Job Agent catches per-board errors gracefully and continues searching all other boards without crashing. To update a company's token, run:
  ```bash
  python scripts/discover_ats.py <company_name> --add-to-registry knowledge/ats_patterns.json
  ```

### `Claim Check QA Flagged Unsupported Claims`
* **Cause**: A draft resume or cover letter contains a technology, metric, or title that is not listed in `candidate/skills.json`, `candidate/MASTER_PROFILE.md`, or `candidate/VERIFIED_ACHIEVEMENTS.md`.
* **Solution**: If you actually possess this skill or achieved this metric, add it to your `candidate/skills.json` or `candidate/VERIFIED_ACHIEVEMENTS.md` and re-run. This safeguard exists specifically to protect you from AI hallucinations!

### `No Jobs Found Matching Preferences`
* **Cause**: Search query or hard exclusion filters may be overly restrictive (e.g. minimum salary set above market rate or strict title filtering).
* **Solution**: Check `candidate/SEARCH_PREFERENCES.md` and widen your target title list or relax minimum compensation.
