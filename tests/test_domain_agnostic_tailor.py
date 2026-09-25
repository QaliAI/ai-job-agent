"""Tests for domain-agnostic resume tailoring and cover letters."""

import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
from tailor_engine import tailor_resume
from cover_letter_engine import generate_cover_letter


def test_non_technical_healthcare_tailoring():
    """Verify that a healthcare candidate generates truthful resumes without software engineering terms."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cand_dir = tmpdir

        # Create master profile for a healthcare professional
        with open(os.path.join(cand_dir, "MASTER_PROFILE.md"), "w", encoding="utf-8") as f:
            f.write("""# Master Profile: Elena Rostova

## 1. Candidate Overview & Contact
* **Full Name**: Elena Rostova
* **Current Title**: Clinical Nurse Coordinator
* **Location**: Chicago, IL
* **Email**: elena.rostova@example.com
* **Phone**: (312) 555-0188
* **Total Years of Experience**: 6 years

## 2. Professional Summary
Dedicated Clinical Nurse Coordinator with 6 years of experience managing acute care units, patient triage, and clinical compliance. Proven success optimizing patient flow and maintaining 100% adherence to hospital regulatory protocols.

## 3. Core Competencies & Skills
* **Proven Skills**: Patient Triage, EPIC EMR, HIPAA Compliance, BLS Certification, Clinical Documentation

## 4. Professional Experience

### **Clinical Nurse Coordinator** | Northwestern Memorial Hospital
*Chicago, IL | 2021 – Present*
* Coordinated care plans for 35 acute care beds, ensuring seamless multidisciplinary handoffs.
* Supervised digital patient chart audits in EPIC EMR achieving 99.8% compliance accuracy.

## 5. Education & Credentials
* **B.S. in Nursing (BSN)** | University of Illinois
""")

        with open(os.path.join(cand_dir, "skills.json"), "w", encoding="utf-8") as f:
            f.write("""{
  "proven_skills": ["Patient Triage", "EPIC EMR", "HIPAA Compliance", "BLS Certification", "Clinical Documentation"],
  "transferable_skills": ["Team Leadership", "Crisis De-escalation"],
  "domain_expertise": ["Inpatient Care"]
}""")

        with open(os.path.join(cand_dir, "VERIFIED_ACHIEVEMENTS.md"), "w", encoding="utf-8") as f:
            f.write("""# Verified Achievements
- [x] Coordinated care plans for 35 acute care beds with zero critical handoff delays.
- [x] Maintained 99.8% regulatory compliance across monthly EPIC EMR chart audits.
""")

        nurse_job = {
            "id": "nurse_job_123",
            "company": "Rush University Medical Center",
            "title": "Lead Patient Care Coordinator",
            "location": "Chicago, IL",
            "work_mode": "onsite",
            "description": "Seeking a Lead Patient Care Coordinator experienced in Patient Triage, EPIC EMR, and clinical documentation."
        }

        # 1. Test tailored resume
        tailored_md, qa_report = tailor_resume(cand_dir, nurse_job)
        assert qa_report["passed"], f"QA failed with violations: {qa_report.get('violations')}"
        assert "Elena Rostova" in tailored_md
        assert "Rush University Medical Center" in tailored_md
        assert "Patient Triage" in tailored_md
        assert "EPIC EMR" in tailored_md

        # Ensure NO software engineering terms were injected!
        assert "distributed systems" not in tailored_md.lower()
        assert "microservices" not in tailored_md.lower()
        assert "high throughput backend" not in tailored_md.lower()
        assert "python, go" not in tailored_md.lower()

        # 2. Test cover letter
        cover_md = generate_cover_letter(cand_dir, nurse_job)
        assert "Elena Rostova" in cover_md
        assert "Rush University Medical Center" in cover_md
        assert "Lead Patient Care Coordinator" in cover_md
        assert "distributed systems" not in cover_md.lower()
        assert "backend services" not in cover_md.lower()
        assert "Engineering Team" not in cover_md
