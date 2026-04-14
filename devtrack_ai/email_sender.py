"""Email sender — sends weekly engineering reports via Resend.

Reads RESEND_API_KEY, RESEND_FROM, REPORT_EMAIL from .env.
When lubot.ai domain is verified, change RESEND_FROM to agent@lubot.ai.
"""

from __future__ import annotations

import os

import resend
from dotenv import load_dotenv

load_dotenv()


def send_report_email(subject: str, html_body: str) -> dict:
    """Send an email via Resend API.

    Returns dict with 'id' on success.
    RESEND_FROM defaults to onboarding@resend.dev until domain is verified.
    Switch to agent@lubot.ai by changing RESEND_FROM in .env.
    """
    resend.api_key = os.getenv("RESEND_API_KEY", "")
    from_email = os.getenv("RESEND_FROM", "onboarding@resend.dev")
    to_email = os.getenv("REPORT_EMAIL", "")

    result = resend.Emails.send({
        "from": f"DevTrack-AI <{from_email}>",
        "to": [to_email],
        "subject": subject,
        "html": html_body,
    })

    return result
