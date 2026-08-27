# Welcome to AI Job Agent: Start Here! 👋

> **Who this guide is for**: You are looking for a job and want AI to help you find fresh opportunities, score them honestly, and prepare tailored resumes — without needing to be a software developer or learning complicated technical tools.

---

## What is AI Job Agent?

Think of **AI Job Agent** as your free, private, personal job-search assistant that runs right on your computer.

Every morning, it:
1. **Scans real employer websites** (places like Stripe, Figma, Ramp, Reddit, and dozens of others) directly through their official career systems (Greenhouse, Lever, Ashby, etc.).
2. **Ignores spam and low-quality reposts** from aggregator boards.
3. **Checks if you actually match the job** using an honest, transparent scoring rubric (no fake AI fluff).
4. **Highlights your real strengths and points out genuine gaps** so you know exactly what to prepare for.
5. **Tailors your resume** for your top matching opportunities using **only your real, verified experience** (it will NEVER invent skills or fake metrics).
6. **Prepares a clean Daily Morning Brief** with direct application links waiting for you.

---

## Choose Your Path

### Option A: "I already use ChatGPT" (Easiest — No Coding Needed)
If you have a ChatGPT account (Desktop app or Web):
1. Create a private **Project** or **Custom GPT** in ChatGPT.
2. Upload the files in the [`candidate/`](candidate/) and [`knowledge/`](knowledge/) folders.
3. Paste any job posting link into ChatGPT and say:
   > *"Score this job against my profile and give me a tailored resume."*
4. Read full details in the [ChatGPT Operating Guide](runtime/chatgpt/README.md).

---

### Option B: "I want the automated morning report on my computer" (5 Minutes)

#### Step 1: Open Your Terminal or PowerShell
* **On Windows**: Press the Windows Key, type `PowerShell`, and hit Enter.
* **On Mac**: Press `Command + Space`, type `Terminal`, and hit Enter.

#### Step 2: Download and Run Setup
Copy and paste this command:
```bash
git clone https://github.com/QaliAI/ai-job-agent.git
cd ai-job-agent
python scripts/setup.py
```
*(On Mac, use `python3 scripts/setup.py` if needed)*

The setup wizard will ask you 6 simple questions (your name, target roles, preferred work mode, and minimum salary) and create your private profile files.

#### Step 3: Run Your First Job Search
```bash
python scripts/daily_workflow.py
```
In seconds, AI Job Agent will scan employer career boards, score opportunities, tailor your top resumes, and generate your morning report in `output/latest_brief.md`!

---

## Your Privacy Guarantee 🔒

Your resume contains personal details like your name, phone number, and work history.
* All your data stays **100% on your own computer**.
* This project is pre-configured so that your personal files in `candidate/` and generated applications in `output/` are **never** shared publicly or uploaded to GitHub.

---

## Need Help?
* Check [SETUP-WIZARD.md](SETUP-WIZARD.md) for a detailed walkthrough.
* Read [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for solutions to common questions.
