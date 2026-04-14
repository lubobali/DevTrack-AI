"""Langfuse API client — pulls LLM usage data from LuBot Staging project.

Reads LUBOT_LANGFUSE_* keys from .env (separate from DevTrack-AI's own Langfuse keys).
Returns aggregated metrics: total traces, cost, models used, error rate, latency.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv

load_dotenv()

LUBOT_LANGFUSE_PUBLIC_KEY = os.getenv("LUBOT_LANGFUSE_PUBLIC_KEY", "")
LUBOT_LANGFUSE_SECRET_KEY = os.getenv("LUBOT_LANGFUSE_SECRET_KEY", "")
LUBOT_LANGFUSE_BASE_URL = os.getenv("LUBOT_LANGFUSE_BASE_URL", "https://us.cloud.langfuse.com")


def _langfuse_api(path: str, params: dict | None = None) -> dict:
    """Call Langfuse REST API with basic auth (public_key:secret_key)."""
    url = f"{LUBOT_LANGFUSE_BASE_URL}/api/public{path}"
    resp = requests.get(
        url,
        auth=(LUBOT_LANGFUSE_PUBLIC_KEY, LUBOT_LANGFUSE_SECRET_KEY),
        params=params or {},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_lubot_traces(days: int = 7) -> dict:
    """Fetch aggregated LLM usage from LuBot Staging Langfuse project.

    Returns dict with: total_traces, total_cost, models_used, avg_latency,
    error_count, token_usage.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    try:
        data = _langfuse_api("/traces", {"fromTimestamp": cutoff, "limit": 500})
        traces = data.get("data", [])
    except Exception:
        # Langfuse might not have data yet or API might be down
        return {
            "total_traces": 0,
            "total_cost": 0.0,
            "models_used": {},
            "avg_latency_ms": 0,
            "error_count": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "available": False,
        }

    if not traces:
        return {
            "total_traces": 0,
            "total_cost": 0.0,
            "models_used": {},
            "avg_latency_ms": 0,
            "error_count": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "available": True,
        }

    # Aggregate metrics
    total_cost = 0.0
    models: dict[str, int] = {}
    latencies: list[float] = []
    errors = 0
    input_tokens = 0
    output_tokens = 0

    for t in traces:
        # Cost
        cost = t.get("totalCost") or t.get("calculatedTotalCost") or 0
        total_cost += float(cost)

        # Model tracking from observations
        observations = t.get("observations", [])
        for obs in observations:
            model = obs.get("model", "unknown")
            models[model] = models.get(model, 0) + 1

            # Tokens
            usage = obs.get("usage", {}) or {}
            input_tokens += usage.get("input", 0) or 0
            output_tokens += usage.get("output", 0) or 0

            # Latency
            if obs.get("latency"):
                latencies.append(obs["latency"])

        # Errors
        if t.get("level") == "ERROR" or t.get("statusMessage"):
            errors += 1

    avg_latency = sum(latencies) / len(latencies) if latencies else 0

    return {
        "total_traces": len(traces),
        "total_cost": round(total_cost, 4),
        "models_used": models,
        "avg_latency_ms": round(avg_latency, 1),
        "error_count": errors,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "available": True,
    }
