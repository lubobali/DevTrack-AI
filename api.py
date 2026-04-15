#!/usr/bin/env python3
"""DevTrack-AI HTTP API — serves real-time engineering data for OpenClaw/Alfred.

Exposes DevTrack metrics as REST endpoints so AI agents (OpenClaw, etc.)
can query live engineering data without SSH access.

Usage:
    pip install fastapi uvicorn
    uvicorn api:app --host 0.0.0.0 --port 8099

Security: Bind to a private network (Tailscale, VPN) or add auth.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from fastapi import FastAPI, Query
from datetime import datetime, timedelta, timezone

from devtrack_ai.git_client import fetch_commits, fetch_issues, fetch_prs, fetch_repo_stats
from devtrack_ai.metrics import calc_velocity, calc_code_health, calc_work_patterns
from devtrack_ai.langfuse_client import fetch_lubot_traces
from devtrack_ai.ccusage_client import fetch_claude_usage

app = FastAPI(title="DevTrack-AI API", version="1.0")


def filter_by_days(commits: list[dict], days: int) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    result = []
    for c in commits:
        try:
            dt = datetime.fromisoformat(c["date"].replace("Z", "+00:00"))
            if dt >= cutoff:
                result.append(c)
        except (ValueError, KeyError):
            continue
    return result


@app.get("/commits")
def get_commits(days: int = Query(7), limit: int = Query(50)):
    commits = fetch_commits(limit=limit, sha="develop")
    if days:
        commits = filter_by_days(commits, days)
    return {"commits": commits, "count": len(commits), "days": days}


@app.get("/metrics")
def get_metrics(days: int = Query(7)):
    commits = fetch_commits(limit=100, sha="develop")
    if days:
        commits = filter_by_days(commits, days)
    velocity = calc_velocity(commits)
    health = calc_code_health(commits)
    return {"velocity": velocity, "code_health": health, "period_days": days, "commits_analyzed": len(commits)}


@app.get("/work-patterns")
def get_work_patterns(days: int = Query(7)):
    commits = fetch_commits(limit=100, sha="develop")
    if days:
        commits = filter_by_days(commits, days)
    patterns = calc_work_patterns(commits)
    late = patterns["late_night_commits"]
    patterns["burnout_risk"] = "high" if late > 5 else "moderate" if late > 3 else "low"
    return {"work_patterns": patterns, "period_days": days}


@app.get("/issues")
def get_issues(state: str = Query("open")):
    issues = fetch_issues(state=state)
    return {"issues": issues, "count": len(issues), "state": state}


@app.get("/prs")
def get_prs(state: str = Query("all")):
    prs = fetch_prs(state=state)
    return {"pull_requests": prs, "count": len(prs), "state": state}


@app.get("/langfuse")
def get_langfuse(days: int = Query(7)):
    data = fetch_lubot_traces(days=days)
    return {"langfuse": data, "period_days": days}


@app.get("/ccusage")
def get_ccusage(days: int = Query(7)):
    data = fetch_claude_usage(days=days)
    return {"ccusage": data, "period_days": days}


@app.get("/repo-stats")
def get_repo_stats():
    return {"repo": fetch_repo_stats()}


@app.get("/full-status")
def get_full_status(days: int = Query(7)):
    commits = fetch_commits(limit=100, sha="develop")
    if days:
        commits = filter_by_days(commits, days)
    velocity = calc_velocity(commits)
    health = calc_code_health(commits)
    patterns = calc_work_patterns(commits)
    late = patterns["late_night_commits"]
    patterns["burnout_risk"] = "high" if late > 5 else "moderate" if late > 3 else "low"
    langfuse = fetch_lubot_traces(days=days)
    repo = fetch_repo_stats()
    return {
        "period_days": days,
        "commits_analyzed": len(commits),
        "recent_commits": commits[:5],
        "velocity": velocity,
        "code_health": health,
        "work_patterns": patterns,
        "langfuse": langfuse,
        "repo": repo,
    }
