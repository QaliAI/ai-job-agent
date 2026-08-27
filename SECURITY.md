# Security & Privacy Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability or potential privacy leak in **AI Job Agent**, please report it responsibly by opening a confidential GitHub Security Advisory or contacting the maintainers directly.

---

## Core Security & Privacy Commitments
* **Local-First Boundary**: Candidate personal records (`candidate/`), generated resumes (`output/`), and search ledgers (`jobs/`) are protected by default via `.gitignore` and must never leave the user's machine unless explicitly configured.
* **No Telemetry**: The codebase contains zero analytics tracking, phone-home beacons, or remote telemetry.
* **Safe Parsing**: All HTML parsing and XML decoding is handled using secure standard library tools with defensive entity unescaping and error timeouts.
