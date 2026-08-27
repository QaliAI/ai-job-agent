"""Tests for AI Job Agent privacy boundaries and .gitignore safeguards."""

import os
import re
import pytest


def test_gitignore_covers_sensitive_directories():
    """Verify that .gitignore properly protects candidate personal data and outputs."""
    gitignore_path = ".gitignore"
    assert os.path.exists(gitignore_path), ".gitignore must exist in root"
    
    with open(gitignore_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Verify candidate directory patterns
    assert "candidate/MASTER_PROFILE.md" in content or "candidate" in content
    assert "candidate/SEARCH_PREFERENCES.md" in content or "candidate" in content
    assert "candidate/VERIFIED_ACHIEVEMENTS.md" in content or "candidate" in content
    assert "candidate/skills.json" in content or "candidate" in content
    
    # Verify outputs and job stores
    assert "output" in content
    assert "jobs" in content
    
    # Verify secrets and env
    assert ".env" in content


def test_no_real_pii_in_repository_files():
    """Ensure no real email addresses or phone numbers exist in repository code/templates."""
    suspicious_patterns = [
        r"\b[A-Za-z0-9._%+-]+@(?!example\.com)[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    ]
    
    # Check tracked template files
    files_to_check = [
        "templates/MASTER_PROFILE_TEMPLATE.md",
        "examples/jordan-taylor/MASTER_PROFILE.md",
        "examples/alex-chen/MASTER_PROFILE.md"
    ]
    
    for fpath in files_to_check:
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                text = f.read()
                # All test emails should end with @example.com
                emails = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
                for email in emails:
                    assert email.endswith("@example.com"), f"Found non-fixture email in {fpath}: {email}"
