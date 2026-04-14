"""Anthropic SDK wrapper — calls Claude via DataExpert proxy (or any Anthropic-compatible API).

Reads ANTHROPIC_BASE_URL and ANTHROPIC_API_KEY from .env.
Langfuse @observe decorator traces every call automatically.
Switch providers by changing .env — no code changes needed.
"""

from __future__ import annotations

import json
import os
import re
import uuid

import requests
from dotenv import load_dotenv
from langfuse import observe

load_dotenv()


@observe(name="call_claude")
def call_claude(system_prompt: str, user_content: str, max_tokens: int = 2000) -> str:
    """Call Claude and return the text response.

    Uses raw HTTP because the DataExpert proxy returns SSE stream
    that the Anthropic SDK doesn't parse correctly.
    Langfuse traces via @observe.
    """
    base_url = os.getenv("ANTHROPIC_BASE_URL", "")
    api_key = os.getenv("ANTHROPIC_API_KEY", "")

    resp = requests.post(
        f"{base_url}/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
            "x-session-id": str(uuid.uuid4()),
        },
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_content}],
        },
        timeout=60,
    )
    resp.raise_for_status()

    # Parse SSE stream — extract text deltas
    text_parts = []
    for line in resp.text.split("\n"):
        if line.startswith("data: "):
            try:
                data = json.loads(line[6:])
                if data.get("type") == "content_block_delta":
                    text_parts.append(data["delta"]["text"])
            except (json.JSONDecodeError, KeyError):
                continue

    return "".join(text_parts)
