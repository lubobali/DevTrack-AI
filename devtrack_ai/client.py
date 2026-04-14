"""LLM client — supports Anthropic proxy AND NVIDIA NIM API.

Reads LLM_PROVIDER from .env: "anthropic" (default) or "nvidia".
Switch providers by changing .env — no code changes needed.
Langfuse @observe decorator traces every call automatically.
"""

from __future__ import annotations

import json
import os
import uuid

import requests
from dotenv import load_dotenv
from langfuse import observe

load_dotenv()


def _call_anthropic(system_prompt: str, user_content: str, max_tokens: int) -> str:
    """Call Anthropic-compatible API (DataExpert proxy). Returns text."""
    base_url = os.getenv("ANTHROPIC_BASE_URL", "")
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

    resp = requests.post(
        f"{base_url}/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
            "x-session-id": str(uuid.uuid4()),
        },
        json={
            "model": model,
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_content}],
        },
        timeout=60,
    )
    resp.raise_for_status()

    # Parse SSE stream
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


def _call_nvidia(system_prompt: str, user_content: str, max_tokens: int) -> str:
    """Call NVIDIA NIM API (OpenAI-compatible). Returns text."""
    api_key = os.getenv("NVIDIA_API_KEY", "")
    model = os.getenv("NVIDIA_MODEL", "nvidia/llama-3.3-nemotron-super-49b-v1")

    resp = requests.post(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": "detailed thinking off\n" + system_prompt},
                {"role": "user", "content": user_content},
            ],
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


@observe(name="call_claude")
def call_claude(system_prompt: str, user_content: str, max_tokens: int = 2000) -> str:
    """Call LLM and return the text response.

    Provider determined by LLM_PROVIDER env var: "anthropic" or "nvidia".
    Langfuse traces via @observe.
    """
    provider = os.getenv("LLM_PROVIDER", "anthropic")

    if provider == "nvidia":
        return _call_nvidia(system_prompt, user_content, max_tokens)
    else:
        return _call_anthropic(system_prompt, user_content, max_tokens)
