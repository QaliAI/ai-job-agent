#!/usr/bin/env python3
"""Notification adapter for the daily digest.

Email is the first channel. Recipients and credentials come from the profile
or the environment. Nothing is hardcoded to a person. If credentials are
missing, the digest is already on disk and the search still succeeds.
"""

import os
from typing import Any, Dict, Optional

from email_notifier import send_email_brief
from profile_config import notification_preferences


def deliver_digest(
    profile: Dict[str, Any],
    html_body: str,
    preview_path: str,
    subject: str,
) -> Dict[str, Any]:
    prefs = notification_preferences(profile)
    channel = prefs["channel"]
    if channel in ("", "file", "none", "off"):
        return {
            "status": "saved",
            "channel": "file",
            "preview_path": preview_path,
            "message": "Digest saved with the profile. No notification was sent.",
        }

    if channel != "email":
        return {
            "status": "saved",
            "channel": "file",
            "preview_path": preview_path,
            "message": f"Notification channel '{channel}' is not configured. Digest saved.",
        }

    to_addr = prefs.get("to") or os.environ.get("JOB_AGENT_EMAIL_TO") or os.environ.get("SMTP_TO")
    try:
        result = send_email_brief(
            html_body,
            subject=subject,
            to_addr=to_addr,
            preview_path=preview_path,
        )
    except Exception as exc:
        return {
            "status": "saved",
            "channel": "file",
            "preview_path": preview_path,
            "message": f"Email delivery failed ({exc}). Digest saved. Search was not failed.",
        }

    if result.get("status") != "sent":
        result = dict(result)
        result["message"] = result.get("message") or (
            "Email credentials are absent or delivery did not complete. Digest saved."
        )
    return result
