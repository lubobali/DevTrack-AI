"""Safety guardrails: PII redaction, context sufficiency, schema validation."""

from __future__ import annotations

import re


# === PII Redaction ===

PII_PATTERNS = [
    ("email", re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")),
    ("phone", re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b")),
    ("ip", re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")),
    ("api_key", re.compile(r"\b(sk-[a-zA-Z0-9_-]{10,}|ghp_[a-zA-Z0-9]{10,})\b")),
]

REPLACEMENT_MAP = {
    "email": "[EMAIL]",
    "phone": "[PHONE]",
    "ip": "[IP]",
    "api_key": "[API_KEY]",
}


def redact_pii(text: str) -> tuple[str, list[dict]]:
    """Redact PII from text. Returns (redacted_text, redaction_log)."""
    log: list[dict] = []
    for pii_type, pattern in PII_PATTERNS:
        for match in pattern.finditer(text):
            log.append({"type": pii_type, "original": match.group(), "position": match.start()})
        text = pattern.sub(REPLACEMENT_MAP[pii_type], text)
    return text, log


# === Context Sufficiency ===


def check_context(input_type: str, data: dict) -> dict:
    """Check if input has enough context for a useful response.

    Returns {"sufficient": bool, "message": str}.
    """
    if input_type == "issue":
        body = data.get("body", "")
        comments = data.get("comments", [])
        if len(body.strip()) < 20 and not comments:
            return {"sufficient": False, "message": "Issue body is too short and has no comments. Assessment will have lower confidence."}
        return {"sufficient": True, "message": ""}

    if input_type == "pr":
        diffs = data.get("diff_snippets", [])
        if not diffs:
            return {"sufficient": False, "message": "No diff snippets provided. Risk assessment will be limited."}
        return {"sufficient": True, "message": ""}

    if input_type == "commits":
        commits = data.get("commits", [])
        if not commits:
            return {"sufficient": False, "message": "No commits in date range. Cannot generate report."}
        return {"sufficient": True, "message": ""}

    return {"sufficient": True, "message": ""}
