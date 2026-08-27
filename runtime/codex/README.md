# Running AI Job Agent with Codex & Developer Agents

This repository follows standard Agent Skills and tool calling conventions, making it fully compatible with OpenAI Codex, Aider, OpenCode, and developer terminal agents.

---

## Quickstart
1. Clone the repository:
   ```bash
   git clone https://github.com/QaliAI/ai-job-agent.git
   cd ai-job-agent
   python scripts/setup.py
   ```
2. Run automated commands directly:
   ```bash
   # Run full daily workflow
   python scripts/daily_workflow.py

   # Check system diagnostics
   python scripts/doctor.py

   # Tailor resume for a specific job
   python scripts/tailor_engine.py --job target_job.json --out output/resumes/my_tailored_resume.md

   # Run factual claim QA check
   python scripts/claim_check.py --draft output/resumes/my_tailored_resume.md
   ```
