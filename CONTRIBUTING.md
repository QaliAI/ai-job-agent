# Contributing to AI Job Agent

We welcome contributions from developers, recruiters, job seekers, and career coaches!

---

## Areas We Welcome Help With:
1. **Adding ATS Connectors**: Have an employer on an unlisted ATS? Add support in `scripts/ats_engine.py`.
2. **Company ATS Patterns**: Add verified company tokens to `knowledge/ats_patterns.json`.
3. **Role Family Knowledge Packs**: Add industry conventions to `knowledge/roles/` (e.g. design, legal, finance).
4. **Runtime Adapters**: Expand compatibility for new open-source agent frameworks.
5. **Testing**: Add automated test cases for parsing edge cases in `tests/`.

---

## Development & Testing Workflow

1. Clone the repo:
   ```bash
   git clone https://github.com/QaliAI/ai-job-agent.git
   cd ai-job-agent
   ```
2. Run automated test suite:
   ```bash
   python -m pytest tests/ -v
   ```
3. Run doctor diagnostics:
   ```bash
   python scripts/doctor.py
   ```
4. Submit a clean Pull Request with descriptive commit messages and license attribution if reusing open-source work.

---

## Code of Conduct & Grounding Standards
* **No AI Slop / Anti-Fabrication**: Code contributions must strictly preserve our factual grounding guarantees. Never add features that fabricate candidate skills, metrics, or credentials.
* **Respect Privacy**: Never commit personal data, real resumes, or sensitive API keys to the repository.
