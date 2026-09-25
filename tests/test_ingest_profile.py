"""Tests for omnichannel profile ingestion engine."""

import json
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
from ingest_profile import build_canonical_profile_files, extract_contact_info, extract_career_metadata


def test_extract_contact_info():
    """Verify regex extraction of contact info from free-form text."""
    raw = """
    Marcus Vance
    Senior Financial Analyst
    marcus.vance@example.com | (415) 555-0133 | Chicago, IL
    linkedin.com/in/marcusvance-fictional
    """
    contact = extract_contact_info(raw)
    assert contact["name"] == "Marcus Vance"
    assert contact["email"] == "marcus.vance@example.com"
    assert contact["phone"] == "(415) 555-0133"
    assert "Chicago" in contact["location"]
    assert "linkedin.com/in/marcusvance-fictional" in contact["linkedin"]


def test_extract_career_metadata_and_build_files():
    """Verify extraction of skills, preferences, and generation of canonical profile files."""
    raw_notes = """
    My name is Sarah Miller.
    I am a Registered Nurse with 8 years of experience based in Austin, TX.
    Email: sarah.nurse@example.com, Phone: (512) 555-0199
    Looking for Remote or Hybrid roles paying at least $115,000 USD.
    Key skills: Patient Triage, EPIC EMR, BLS Certification, HIPAA Compliance, Vital Signs.
    
    Achievements:
    * Coordinated triage workflows across 40 acute care beds with zero critical handoff delays.
    * Reduced emergency department intake wait times by 22% through digital patient intake.
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        paths = build_canonical_profile_files(raw_notes, output_dir=tmpdir)

        assert os.path.exists(paths["master_profile"])
        assert os.path.exists(paths["skills"])
        assert os.path.exists(paths["preferences"])
        assert os.path.exists(paths["achievements"])

        # Check master profile content
        with open(paths["master_profile"], "r", encoding="utf-8") as f:
            m_text = f.read()
            assert "Sarah Miller" in m_text
            assert "Registered Nurse" in m_text
            assert "sarah.nurse@example.com" in m_text
            assert "8 years" in m_text
            assert "Patient Triage" in m_text

        # Check skills json
        with open(paths["skills"], "r", encoding="utf-8") as f:
            s_data = json.load(f)
            assert "Patient Triage" in s_data["proven_skills"]
            assert "EPIC EMR" in s_data["proven_skills"]

        # Check preferences
        with open(paths["preferences"], "r", encoding="utf-8") as f:
            p_text = f.read()
            assert "Registered Nurse" in p_text
            assert "$115,000 USD" in p_text
