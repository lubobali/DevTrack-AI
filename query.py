#!/usr/bin/env python3
"""DevTrack-AI real-time query CLI for OpenClaw integration.

Thin wrapper over existing DevTrack modules. Outputs JSON to stdout.
Usage:
    python query.py commits [--days N] [--limit N]
    python query.py metrics [--days N]
    python query.py work-patterns [--days N]
    python query.py issues [--state open|closed|all]
    python query.py prs [--state open|closed|all]
    python query.py langfuse [--days N]
    python query.py ccusage [--days N]
    python query.py repo-stats
    python query.py full-status [--days N]
"""

from __future__ import annotations

import argparse
import json
import sys
import os
from datetime import datetime, timedelta, timezone

# Ensure devtrack_ai package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from devtrack_ai.git_client import fetch_commits, fetch_issues, fetch_prs, fetch_repo_stats
from devtrack_ai.metrics import calc_velocity, calc_code_health, calc_work_patterns
from devtrack_ai.langfuse_client import fetch_lubot_traces
from devtrack_ai.ccusage_client import fetch_claude_usage


def filter_by_days(commits: list[dict], days: int) -> list[dict]:
    """Filter commits to last N days."""
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


def cmd_commits(args):
    commits = fetch_commits(limit=args.limit, sha="develop")
    if args.days:
        commits = filter_by_days(commits, args.days)
    return {"commits": commits, "count": len(commits), "days": args.days}


def cmd_metrics(args):
    commits = fetch_commits(limit=100, sha="develop")
    if args.days:
        commits = filter_by_days(commits, args.days)
    velocity = calc_velocity(commits)
    health = calc_code_health(commits)
    return {"velocity": velocity, "code_health": health, "period_days": args.days, "commits_analyzed": len(commits)}


def cmd_work_patterns(args):
    commits = fetch_commits(limit=100, sha="develop")
    if args.days:
        commits = filter_by_days(commits, args.days)
    patterns = calc_work_patterns(commits)
    # Add burnout assessment
    late = patterns["late_night_commits"]
    if late > 5:
        patterns["burnout_risk"] = "high"
    elif late > 3:
        patterns["burnout_risk"] = "moderate"
    else:
        patterns["burnout_risk"] = "low"
    return {"work_patterns": patterns, "period_days": args.days}


def cmd_issues(args):
    issues = fetch_issues(state=args.state)
    return {"issues": issues, "count": len(issues), "state": args.state}


def cmd_prs(args):
    prs = fetch_prs(state=args.state)
    return {"pull_requests": prs, "count": len(prs), "state": args.state}


def cmd_langfuse(args):
    data = fetch_lubot_traces(days=args.days)
    return {"langfuse": data, "period_days": args.days}


def cmd_ccusage(args):
    data = fetch_claude_usage(days=args.days)
    return {"ccusage": data, "period_days": args.days}


def cmd_repo_stats(args):
    stats = fetch_repo_stats()
    return {"repo": stats}


def cmd_full_status(args):
    """Pull everything for a comprehensive status update."""
    commits = fetch_commits(limit=100, sha="develop")
    if args.days:
        commits = filter_by_days(commits, args.days)

    velocity = calc_velocity(commits)
    health = calc_code_health(commits)
    patterns = calc_work_patterns(commits)

    late = patterns["late_night_commits"]
    if late > 5:
        patterns["burnout_risk"] = "high"
    elif late > 3:
        patterns["burnout_risk"] = "moderate"
    else:
        patterns["burnout_risk"] = "low"

    langfuse = fetch_lubot_traces(days=args.days)
    repo = fetch_repo_stats()

    return {
        "period_days": args.days,
        "commits_analyzed": len(commits),
        "recent_commits": commits[:5],
        "velocity": velocity,
        "code_health": health,
        "work_patterns": patterns,
        "langfuse": langfuse,
        "repo": repo,
    }


def main():
    parser = argparse.ArgumentParser(description="DevTrack-AI real-time query")
    sub = parser.add_subparsers(dest="command", required=True)

    # commits
    p = sub.add_parser("commits")
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--limit", type=int, default=50)

    # metrics
    p = sub.add_parser("metrics")
    p.add_argument("--days", type=int, default=7)

    # work-patterns
    p = sub.add_parser("work-patterns")
    p.add_argument("--days", type=int, default=7)

    # issues
    p = sub.add_parser("issues")
    p.add_argument("--state", default="open", choices=["open", "closed", "all"])

    # prs
    p = sub.add_parser("prs")
    p.add_argument("--state", default="all", choices=["open", "closed", "all"])

    # langfuse
    p = sub.add_parser("langfuse")
    p.add_argument("--days", type=int, default=7)

    # ccusage
    p = sub.add_parser("ccusage")
    p.add_argument("--days", type=int, default=7)

    # repo-stats
    sub.add_parser("repo-stats")

    # full-status
    p = sub.add_parser("full-status")
    p.add_argument("--days", type=int, default=7)

    args = parser.parse_args()

    commands = {
        "commits": cmd_commits,
        "metrics": cmd_metrics,
        "work-patterns": cmd_work_patterns,
        "issues": cmd_issues,
        "prs": cmd_prs,
        "langfuse": cmd_langfuse,
        "ccusage": cmd_ccusage,
        "repo-stats": cmd_repo_stats,
        "full-status": cmd_full_status,
    }

    result = commands[args.command](args)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
