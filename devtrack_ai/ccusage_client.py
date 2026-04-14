"""ccusage client — pulls Claude Code token usage from Hetzner via SSH.

Runs `ccusage daily --json` on the server and parses per-project costs.
Requires SSH access to the Hetzner server (root@100.115.173.71).
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timedelta, timezone

HETZNER_HOST = "root@100.115.173.71"
LUBOT_PROJECT_PREFIX = "-srv-lubot-staging"


def _run_ssh(command: str) -> str:
    """Run a command on Hetzner via SSH and return stdout."""
    result = subprocess.run(
        ["ssh", HETZNER_HOST, command],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        return ""
    return result.stdout


def fetch_claude_usage(days: int = 7) -> dict:
    """Fetch Claude Code token usage from ccusage on Hetzner.

    Returns aggregated data: total cost, tokens, sessions, per-project breakdown.
    """
    try:
        raw = _run_ssh("ccusage daily --json")
        if not raw:
            return _empty_result()

        data = json.loads(raw)
        daily_entries = data.get("daily", [])

        # Filter to date range
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        recent = []
        for entry in daily_entries:
            try:
                dt = datetime.strptime(entry["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                if dt >= cutoff:
                    recent.append(entry)
            except (ValueError, KeyError):
                continue

        if not recent:
            return _empty_result(available=True)

        # Aggregate
        total_cost = sum(e.get("totalCost", 0) for e in recent)
        total_tokens = sum(e.get("totalTokens", 0) for e in recent)
        total_input = sum(e.get("inputTokens", 0) for e in recent)
        total_output = sum(e.get("outputTokens", 0) for e in recent)
        total_cache_read = sum(e.get("cacheReadTokens", 0) for e in recent)

        # Model breakdown
        models: dict[str, float] = {}
        for entry in recent:
            for mb in entry.get("modelBreakdowns", []):
                name = mb.get("modelName", "unknown")
                models[name] = models.get(name, 0) + mb.get("cost", 0)

        # Per-project breakdown from session data
        projects = _fetch_project_breakdown(days)

        return {
            "total_cost": round(total_cost, 2),
            "total_tokens": total_tokens,
            "input_tokens": total_input,
            "output_tokens": total_output,
            "cache_read_tokens": total_cache_read,
            "days_tracked": len(recent),
            "models": {k: round(v, 2) for k, v in models.items()},
            "projects": projects,
            "sessions": len(recent),
            "available": True,
        }

    except (json.JSONDecodeError, subprocess.TimeoutExpired, Exception):
        return _empty_result()


def _fetch_project_breakdown(days: int) -> dict:
    """Get per-project cost breakdown from session data."""
    try:
        raw = _run_ssh("ccusage session --json")
        if not raw:
            return {}

        data = json.loads(raw)
        sessions = data.get("sessions", [])

        # Aggregate by project path
        projects: dict[str, dict] = {}
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        for s in sessions:
            path = s.get("projectPath", "Unknown Project")
            # Extract clean project name
            if LUBOT_PROJECT_PREFIX in path:
                name = "lubot-staging"
            elif "hellopayments" in path.lower():
                name = "hellopayments"
            elif path == "Unknown Project":
                name = "other"
            else:
                name = path.split("/")[0] if "/" in path else path

            if name not in projects:
                projects[name] = {"cost": 0, "tokens": 0, "sessions": 0}

            projects[name]["cost"] += s.get("totalCost", 0)
            projects[name]["tokens"] += s.get("totalTokens", 0)
            projects[name]["sessions"] += 1

        # Round costs
        for p in projects.values():
            p["cost"] = round(p["cost"], 2)

        return projects

    except Exception:
        return {}


def _empty_result(available: bool = False) -> dict:
    return {
        "total_cost": 0,
        "total_tokens": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "days_tracked": 0,
        "models": {},
        "projects": {},
        "sessions": 0,
        "available": available,
    }
