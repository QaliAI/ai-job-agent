# macOS Setup & Operating Guide

A complete guide for running AI Job Agent on macOS (Apple Silicon M1/M2/M3/M4 & Intel).

---

## 1. Prerequisites
1. **Python 3.10+**: Pre-installed on macOS or install via [Homebrew](https://brew.sh):
   ```bash
   brew install python
   ```
2. **Git**: Built-in with Xcode Command Line Tools (`xcode-select --install`).

---

## 2. Quickstart (Terminal)
Open **Terminal** and run:

```bash
# 1. Clone repository
git clone https://github.com/QaliAI/ai-job-agent.git
cd ai-job-agent

# 2. Run guided setup wizard
python3 scripts/setup.py

# 3. Verify system health
python3 scripts/doctor.py

# 4. Run your first autonomous search
python3 scripts/daily_workflow.py
```

---

## 3. Daily Automation (macOS `launchd`)
To schedule AI Job Agent to run automatically every morning at 8:00 AM using macOS's native `launchd`:

1. Copy the plist configuration to your LaunchAgents directory:
   ```bash
   cp runtime/scheduling/macos_launchd.plist ~/Library/LaunchAgents/com.aijobagent.daily.plist
   ```
2. Edit `~/Library/LaunchAgents/com.aijobagent.daily.plist` to replace `/Users/YOUR_USERNAME/ai-job-agent` with your actual project path.
3. Load the daemon:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.aijobagent.daily.plist
   ```

Your morning report will be automatically refreshed daily in `output/latest_brief.md`.
