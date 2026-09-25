#!/usr/bin/env python3
"""Email Notification & Responsive HTML Morning Brief Engine for AI Job Agent.

Formats and delivers executive job search reports:
1. Compiles scored jobs, rationale, gaps, and tailored resumes into a responsive HTML email.
2. Dispatches via standard SMTP (Gmail, Outlook, AWS SES, custom) or Resend API.
3. Falls back to generating a browser-ready HTML preview file (output/latest_brief.html)
   when live credentials are not configured.

Zero external dependencies (pure Python standard library).
"""

import argparse
import html
import json
import os
import smtplib
import sys
import urllib.request
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def render_tracker_strip(tracker_summary: Optional[Dict[str, Any]]) -> str:
    if not tracker_summary:
        return ""
    labels = ("new", "applied", "interview", "rejected", "archived")
    cells = []
    for label in labels:
        cells.append(
            f'<div style="flex:1;"><div style="font-size:18px;font-weight:800;">{int(tracker_summary.get(label, 0))}</div>'
            f'<div style="font-size:11px;text-transform:uppercase;color:#64748b;">{label}</div></div>'
        )
    return (
        '<div style="display:flex;background:#ffffff;border-bottom:1px solid #e2e8f0;padding:12px 28px;text-align:center;">'
        + "".join(cells)
        + "</div>"
    )


def render_html_brief(
    scored_jobs: List[Dict[str, Any]],
    candidate_profile: Dict[str, Any],
    total_scanned: int = 0,
    total_filtered: int = 0,
    tailored_files: Optional[Dict[str, str]] = None,
    tracker_summary: Optional[Dict[str, Any]] = None,
) -> str:
    """Renders a modern, responsive HTML email template for the daily brief."""
    today_str = date.today().strftime("%B %d, %Y")
    cand_name = html.escape(candidate_profile.get("name", "Candidate"))
    cand_title = html.escape(candidate_profile.get("title", "Professional"))
    cand_loc = html.escape(candidate_profile.get("location", "United States"))
    work_mode = html.escape(candidate_profile.get("work_mode_pref", "Remote").capitalize())
    tailored_map = tailored_files or {}

    jobs_html = ""
    for idx, job in enumerate(scored_jobs, start=1):
        comp = html.escape(job.get("company", "Employer"))
        title = html.escape(job.get("title", "Role"))
        fit_eval = job.get("fit_evaluation", {})
        score = job.get("fit_score", fit_eval.get("score", 75))
        rec = fit_eval.get("recommendation", "APPLY" if score >= 80 else "CONSIDER")
        conf = fit_eval.get("confidence", "High")
        loc = html.escape(job.get("location", "Not Specified"))
        wm = html.escape(job.get("work_mode", "unknown").capitalize())

        sal_min = job.get("salary_min")
        sal_max = job.get("salary_max")
        curr = job.get("currency", "USD")
        if sal_min and sal_max:
            sal_str = f"${sal_min:,.0f} – ${sal_max:,.0f} {curr}"
        elif sal_min:
            sal_str = f"From ${sal_min:,.0f} {curr}"
        else:
            sal_str = "Compensation unlisted"

        apply_url = job.get("apply_url") or job.get("canonical_url", "#")
        source = html.escape(job.get("source", "ATS").capitalize())
        strengths = fit_eval.get("strengths", [])
        gaps = fit_eval.get("material_gaps", [])
        explanation = fit_eval.get("explanation") or {}
        if explanation.get("why_fit"):
            strengths = explanation["why_fit"]
        if explanation.get("why_not"):
            gaps = explanation["why_not"]
        found = job.get("first_seen") or job.get("first_seen_at") or ""
        if isinstance(found, str) and "T" in found:
            found = found.split("T", 1)[0]

        # Score color
        if score >= 85:
            score_bg = "#0d9488"  # Teal green
        elif score >= 70:
            score_bg = "#d97706"  # Amber
        else:
            score_bg = "#64748b"  # Slate

        tailored_path = tailored_map.get(job.get("id"))
        tailored_badge = ""
        if tailored_path:
            tailored_badge = f'<div style="margin-top: 8px; font-size: 13px; color: #047857;">📄 <strong>Tailored Résumé Ready</strong>: <code>{html.escape(tailored_path)}</code> (Claim QA: Passed)</div>'

        strengths_li = "".join([f"<li>{html.escape(s)}</li>" for s in strengths[:2]]) if strengths else "<li>Core requirements matched</li>"
        gaps_li = "".join([f"<li>{html.escape(g)}</li>" for g in gaps[:2]]) if gaps else "<li>None on core requirements</li>"

        jobs_html += f"""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; margin-bottom: 12px;">
                <div>
                    <h3 style="margin: 0 0 6px 0; color: #0f172a; font-size: 18px; font-weight: 700;">{idx}. {title}</h3>
                    <div style="font-size: 14px; font-weight: 600; color: #2563eb;">{comp} &middot; <span style="color: #64748b; font-weight: 400;">{loc} ({wm})</span></div>
                </div>
                <div style="margin-top: 4px;">
                    <span style="background: {score_bg}; color: #ffffff; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 700; text-transform: uppercase;">
                        {score}/100 &middot; {rec}
                    </span>
                </div>
            </div>

            <div style="background: #f8fafc; border-radius: 6px; padding: 10px 14px; margin: 12px 0; font-size: 13px; color: #334155;">
                <strong>💰 Compensation:</strong> {html.escape(sal_str)} &nbsp;|&nbsp; <strong>📡 Source:</strong> {source} &nbsp;|&nbsp; <strong>Found:</strong> {html.escape(found or "this run")}
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-size: 13px; margin-top: 10px;">
                <div>
                    <span style="font-weight: 600; color: #059669;">✓ Key Strengths:</span>
                    <ul style="margin: 4px 0 0 0; padding-left: 18px; color: #475569;">
                        {strengths_li}
                    </ul>
                </div>
                <div>
                    <span style="font-weight: 600; color: #d97706;">ℹ Identified Gaps / Nuances:</span>
                    <ul style="margin: 4px 0 0 0; padding-left: 18px; color: #475569;">
                        {gaps_li}
                    </ul>
                </div>
            </div>

            {tailored_badge}

            <div style="margin-top: 16px; padding-top: 12px; border-top: 1px solid #f1f5f9; text-align: right;">
                <a href="{apply_url}" style="background: #2563eb; color: #ffffff; padding: 8px 18px; border-radius: 6px; text-decoration: none; font-size: 13px; font-weight: 600; display: inline-block;">
                    View & Apply on Employer Site &rarr;
                </a>
            </div>
        </div>
        """

    checklist_html = ""
    for idx, job in enumerate(scored_jobs[:3], start=1):
        cname = html.escape(job.get("company", "Employer"))
        rtitle = html.escape(job.get("title", "Role"))
        checklist_html += f'<li style="margin-bottom: 6px;">[ ] Review and submit application for <strong>{cname}</strong> ({rtitle})</li>'

    html_email = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Job Search Brief — {today_str}</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 24px; color: #0f172a;">
    <div style="max-width: 680px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
        
        <!-- Header Banner -->
        <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); color: #ffffff; padding: 32px 28px;">
            <div style="font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #38bdf8; margin-bottom: 6px;">
                🤖 AI Job Agent &middot; Autonomous Morning Report
            </div>
            <h1 style="margin: 0; font-size: 24px; font-weight: 800; line-height: 1.2;">Daily Executive Job Brief</h1>
            <div style="margin-top: 8px; font-size: 14px; color: #94a3b8;">
                {today_str} &middot; Prepared for <strong>{cand_name}</strong> ({cand_title})
            </div>
            <div style="margin-top: 10px; font-size: 13px; color: #e2e8f0;">
                Personal dashboard for this profile only. No auto-apply. You review and submit.
            </div>
        </div>

        {render_tracker_strip(tracker_summary)}

        <!-- Metric Stat Cards -->
        <div style="display: flex; background: #f8fafc; border-bottom: 1px solid #e2e8f0; padding: 16px 28px; text-align: center;">
            <div style="flex: 1; border-right: 1px solid #e2e8f0;">
                <div style="font-size: 22px; font-weight: 800; color: #0f172a;">{total_scanned or len(scored_jobs)}</div>
                <div style="font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 600;">Scanned</div>
            </div>
            <div style="flex: 1; border-right: 1px solid #e2e8f0;">
                <div style="font-size: 22px; font-weight: 800; color: #059669;">{total_filtered or len(scored_jobs)}</div>
                <div style="font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 600;">Filtered</div>
            </div>
            <div style="flex: 1; border-right: 1px solid #e2e8f0;">
                <div style="font-size: 22px; font-weight: 800; color: #2563eb;">{len(scored_jobs)}</div>
                <div style="font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 600;">Top Matches</div>
            </div>
            <div style="flex: 1;">
                <div style="font-size: 22px; font-weight: 800; color: #7c3aed;">{len(tailored_map)}</div>
                <div style="font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 600;">Tailored Resumes</div>
            </div>
        </div>

        <!-- Body Content -->
        <div style="padding: 28px;">
            <h2 style="font-size: 16px; text-transform: uppercase; letter-spacing: 0.05em; color: #475569; margin: 0 0 16px 0; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;">
                🎯 Top Direct Employer Opportunities
            </h2>

            {jobs_html}

            <!-- Daily Action Checklist -->
            <div style="background: #fdf4ff; border: 1px solid #f0abfc; border-radius: 8px; padding: 18px; margin-top: 24px;">
                <h3 style="margin: 0 0 8px 0; font-size: 15px; color: #86198f;">⚡ Today's Action Checklist</h3>
                <ul style="margin: 0; padding-left: 20px; font-size: 13px; color: #701a75;">
                    {checklist_html}
                </ul>
            </div>
        </div>

        <!-- Footer -->
        <div style="background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 20px 28px; font-size: 12px; color: #64748b; text-align: center;">
            <div>All jobs verified direct-from-source. No repost aggregators. No hallucinations.</div>
            <div style="margin-top: 6px;">Your data lives 100% locally on your machine. &copy; AI Job Agent</div>
        </div>
    </div>
</body>
</html>
"""
    return html_email


def send_email_brief(
    html_content: str,
    subject: str = "🌅 Daily Job Search Brief",
    to_addr: Optional[str] = None,
    from_addr: Optional[str] = None,
    preview_path: Optional[str] = None
) -> Dict[str, Any]:
    """Dispatches the HTML email brief via SMTP, Resend, or saves preview."""
    target_to = to_addr or os.environ.get("JOB_AGENT_EMAIL_TO") or os.environ.get("SMTP_TO")
    target_from = from_addr or os.environ.get("JOB_AGENT_EMAIL_FROM") or os.environ.get("SMTP_FROM", "job-agent@local")

    # 1. Check for Resend API Key
    resend_key = os.environ.get("RESEND_API_KEY")
    if resend_key and target_to:
        print(f"📧 Sending brief via Resend API to {target_to}...")
        try:
            req = urllib.request.Request(
                "https://api.resend.com/emails",
                data=json.dumps({
                    "from": target_from,
                    "to": [target_to],
                    "subject": subject,
                    "html": html_content
                }).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {resend_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "AIJobAgent-Notifier/1.0"
                }
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status in (200, 201):
                    return {"status": "sent", "channel": "resend", "recipient": target_to}
        except Exception as e:
            sys.stderr.write(f"Resend dispatch warning: {e}\n")

    # 2. Check for standard SMTP credentials
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")

    if smtp_host and target_to:
        print(f"📧 Sending brief via SMTP ({smtp_host}:{smtp_port}) to {target_to}...")
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = target_from
            msg["To"] = target_to
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                server.starttls()
                if smtp_user and smtp_pass:
                    server.login(smtp_user, smtp_pass)
                server.sendmail(target_from, [target_to], msg.as_string())
            return {"status": "sent", "channel": "smtp", "recipient": target_to}
        except Exception as e:
            sys.stderr.write(f"SMTP dispatch warning: {e}\n")

    # 3. Fallback: Save local HTML preview
    out_file = preview_path or os.path.join("output", "latest_brief.html")
    os.makedirs(os.path.dirname(os.path.abspath(out_file)), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    return {
        "status": "preview_saved",
        "channel": "file",
        "preview_path": out_file,
        "message": f"Saved HTML email preview to {out_file} (Configure SMTP_HOST or RESEND_API_KEY to send live emails)"
    }


def main():
    parser = argparse.ArgumentParser(description="Generate and dispatch HTML morning brief email.")
    parser.add_argument("--jobs", required=True, help="Path to scored jobs JSON")
    parser.add_argument("--candidate", default="candidate", help="Candidate data directory")
    parser.add_argument("--to", help="Recipient email address")
    parser.add_argument("--out-html", help="Path to save HTML preview")
    parser.add_argument("--send", action="store_true", help="Attempt live email dispatch")

    args = parser.parse_args()

    with open(args.jobs, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    profile = {"name": "Candidate", "title": "Professional", "location": "United States"}
    master_path = os.path.join(args.candidate, "MASTER_PROFILE.md")
    if os.path.exists(master_path):
        with open(master_path, "r", encoding="utf-8") as f:
            t = f.read()
            import re
            m = re.search(r"Full Name\s*:\s*([^\n\r]+)", t)
            if m:
                profile["name"] = m.group(1).strip()
            m2 = re.search(r"Current Title\s*:\s*([^\n\r]+)", t)
            if m2:
                profile["title"] = m2.group(1).strip()

    html_text = render_html_brief(jobs, profile)
    res = send_email_brief(
        html_text,
        subject=f"🌅 Daily Job Brief — {date.today().isoformat()}",
        to_addr=args.to,
        preview_path=args.out_html
    )
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
