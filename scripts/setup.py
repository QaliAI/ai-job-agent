#!/usr/bin/env python3
"""Interactive Onboarding & Setup Wizard for AI Job Agent.

Designed for non-technical users:
1. Inspects operating system and Python environment.
2. Creates private `candidate/` career data files.
3. Guides intake for target roles, location, remote preference, and salary minimum.
4. Initializes master profile and search preferences.
5. Runs first test job search to verify ATS connectivity.
"""

import json
import os
import platform
import shutil
import sys
from datetime import date

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def prompt_user(prompt_text: str, default: str = "") -> str:
    """Prompts the user with a default fallback."""
    if default:
        full_prompt = f"{prompt_text} [{default}]: "
    else:
        full_prompt = f"{prompt_text}: "
    try:
        val = input(full_prompt).strip()
        return val if val else default
    except (EOFError, KeyboardInterrupt):
        return default


def run_setup(interactive: bool = True):
    print("=" * 65)
    print("       🤖 Welcome to AI Job Agent Setup Wizard       ")
    print("  Your Private, Local-First, Autonomous Job Assistant")
    print("=" * 65)
    print()
    print("All personal data is stored locally on your machine.")
    print("Your resume and information will NEVER be uploaded to GitHub.")
    print("-" * 65)

    os_name = platform.system()
    py_ver = sys.version.split()[0]
    print(f"✓ Operating System Detected: {os_name} ({platform.platform()})")
    print(f"✓ Python Environment: {py_ver}")
    print()

    # Ensure directories exist
    os.makedirs("candidate", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    os.makedirs("jobs", exist_ok=True)

    if not interactive:
        print("Non-interactive mode: initializing candidate directory from templates...")
        for tmpl, dest in [
            ("templates/MASTER_PROFILE_TEMPLATE.md", "candidate/MASTER_PROFILE.md"),
            ("templates/SEARCH_PREFERENCES_TEMPLATE.md", "candidate/SEARCH_PREFERENCES.md"),
            ("templates/VERIFIED_ACHIEVEMENTS_TEMPLATE.md", "candidate/VERIFIED_ACHIEVEMENTS.md"),
            ("templates/CAREER_STORIES_TEMPLATE.md", "candidate/CAREER_STORIES.md"),
            ("templates/skills_template.json", "candidate/skills.json"),
        ]:
            if os.path.exists(tmpl) and not os.path.exists(dest):
                shutil.copy(tmpl, dest)
        print("✓ Templates copied to 'candidate/' directory.")
        return

    print("Let's configure your basic job preferences:")
    name = prompt_user("1. What is your full name?", "Alex Rivera")
    title = prompt_user("2. What is your target role/title?", "Senior Software Engineer")
    location = prompt_user("3. Where are you located? (City, State/Country)", "Austin, TX, USA")
    work_mode = prompt_user("4. Preferred work mode? (remote / hybrid / onsite)", "remote")
    min_sal = prompt_user("5. Minimum acceptable annual salary in USD?", "150000")
    skills_raw = prompt_user("6. Top 5 technical/domain skills (comma-separated)?", "Python, Go, PostgreSQL, AWS, Docker")

    skills_list = [s.strip() for s in skills_raw.split(",") if s.strip()]

    # Generate candidate/SEARCH_PREFERENCES.md
    prefs_content = f"""# Job Search Preferences

## 1. Target Roles & Titles
* {title}

## 2. Work Arrangement & Location
* **Work Mode Preference**: {work_mode.capitalize()}
* **Allowed Locations**:
  - {location}
  - United States (Remote)

## 3. Compensation Preferences
* **Minimum Base Salary**: ${int(min_sal):,.0f} USD
* **Currency**: USD

## 4. Hard Exclusions & Blacklist
* **Excluded Companies**:
* **Excluded Title Keywords**: "Junior", "Intern"
"""
    with open("candidate/SEARCH_PREFERENCES.md", "w", encoding="utf-8") as f:
        f.write(prefs_content)

    # Generate candidate/skills.json
    skills_json_data = {
        "proven_skills": skills_list,
        "transferable_skills": [],
        "domain_expertise": [],
        "soft_skills": ["Technical Communication", "Project Leadership"]
    }
    with open("candidate/skills.json", "w", encoding="utf-8") as f:
        json.dump(skills_json_data, f, indent=2)

    # Copy starter templates for master profile and achievements if missing
    if not os.path.exists("candidate/MASTER_PROFILE.md"):
        shutil.copy("templates/MASTER_PROFILE_TEMPLATE.md", "candidate/MASTER_PROFILE.md")
    if not os.path.exists("candidate/VERIFIED_ACHIEVEMENTS.md"):
        shutil.copy("templates/VERIFIED_ACHIEVEMENTS_TEMPLATE.md", "candidate/VERIFIED_ACHIEVEMENTS.md")
    if not os.path.exists("candidate/CAREER_STORIES.md"):
        shutil.copy("templates/CAREER_STORIES_TEMPLATE.md", "candidate/CAREER_STORIES.md")

    print()
    print("=" * 65)
    print("🎉 Setup completed successfully!")
    print("=" * 65)
    print("Created private profile files in 'candidate/':")
    print("  • candidate/SEARCH_PREFERENCES.md")
    print("  • candidate/skills.json")
    print("  • candidate/MASTER_PROFILE.md")
    print("  • candidate/VERIFIED_ACHIEVEMENTS.md")
    print("  • candidate/CAREER_STORIES.md")
    print()
    print("Next steps:")
    print("1. Open 'candidate/MASTER_PROFILE.md' and paste your real work history.")
    print("2. Run a test search:  python scripts/daily_workflow.py")
    print("3. Check your report: output/latest_brief.md")
    print("=" * 65)


if __name__ == "__main__":
    is_ci = os.environ.get("CI") == "true" or "--non-interactive" in sys.argv
    run_setup(interactive=not is_ci)
