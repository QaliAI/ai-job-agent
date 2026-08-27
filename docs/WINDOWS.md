# Windows Setup & Operating Guide

A complete guide for running AI Job Agent on Windows 10/11.

---

## 1. Prerequisites
1. **Python 3.10+**: Download and install from [python.org](https://www.python.org/downloads/).
   > ⚠️ **Important**: Check the box **"Add Python to PATH"** during installation.
2. **Git** (optional, but recommended): Download from [git-scm.com](https://git-scm.com/).

---

## 2. Quickstart (PowerShell)
Open **PowerShell** or **Windows Terminal** and run:

```powershell
# 1. Clone repository
git clone https://github.com/QaliAI/ai-job-agent.git
cd ai-job-agent

# 2. Run guided setup wizard
python scripts\setup.py

# 3. Verify system health
python scripts\doctor.py

# 4. Run your first autonomous search
python scripts\daily_workflow.py
```

---

## 3. Daily Automation (Windows Task Scheduler)
To have AI Job Agent automatically run every morning at 8:00 AM:

```powershell
powershell -ExecutionPolicy Bypass -File .\runtime\scheduling\windows_schedule.ps1
```
This registers a native Windows background task named `AIJobAgentDailySearch`. Your daily morning report will always be waiting in `output\latest_brief.md`.

---

## 4. Windows Character Encoding (UTF-8)
All AI Job Agent scripts automatically reconfigure Python's console streams to UTF-8 to prevent Windows code page (`cp1252`) encoding issues. If running in legacy Command Prompt, enable UTF-8 with:
```cmd
chcp 65001
```
