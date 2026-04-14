"""Engineering metrics calculator — all 9 tracking categories.

Pure Python math. No LLM calls. No tokens burned.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone


# === Commit Categorization ===

CATEGORY_PATTERNS = [
    ("feature", re.compile(r"^(Feature|Add|Implement|Build|Create|Phase)", re.IGNORECASE)),
    ("fix", re.compile(r"^(Fix|Bug|Hotfix|Patch)", re.IGNORECASE)),
    ("refactor", re.compile(r"^(Refactor|Extract|Move|Rename|Cleanup|Delete|Remove)", re.IGNORECASE)),
    ("test", re.compile(r"^(Test|TEST|Add test|Fix test)", re.IGNORECASE)),
]


def categorize_commit(message: str) -> str:
    """Categorize a commit message into feature/fix/refactor/test/other."""
    for category, pattern in CATEGORY_PATTERNS:
        if pattern.search(message):
            return category
    return "other"


# === Category 1: Velocity ===


def calc_velocity(commits: list[dict]) -> dict:
    """Calculate velocity metrics from commit list."""
    categories = [categorize_commit(c["message"]) for c in commits]
    return {
        "total_commits": len(commits),
        "feature_commits": categories.count("feature"),
        "fix_commits": categories.count("fix"),
        "refactor_commits": categories.count("refactor"),
        "test_commits": categories.count("test"),
        "other_commits": categories.count("other"),
    }


# === Category 2: Code Health ===


def calc_code_health(commits: list[dict]) -> dict:
    """Calculate code health from commit stats (additions/deletions)."""
    total_added = 0
    total_removed = 0
    for c in commits:
        stats = c.get("stats", {})
        total_added += stats.get("additions", 0)
        total_removed += stats.get("deletions", 0)
    return {
        "lines_added": total_added,
        "lines_removed": total_removed,
        "net_change": total_added - total_removed,
    }


# === Category 8: Work Patterns ===


def calc_work_patterns(commits: list[dict]) -> dict:
    """Analyze commit timestamps for work patterns and burnout risk."""
    late_night = 0
    hours: list[int] = []
    days: list[int] = []

    for c in commits:
        date_str = c.get("date", "")
        if not date_str:
            continue
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            hour = dt.hour
            hours.append(hour)
            days.append(dt.weekday())
            if 0 <= hour < 6:
                late_night += 1
        except (ValueError, TypeError):
            continue

    hour_counts = {}
    for h in hours:
        hour_counts[h] = hour_counts.get(h, 0) + 1
    peak_hour = max(hour_counts, key=hour_counts.get) if hour_counts else 0

    day_counts = {}
    for d in days:
        day_counts[d] = day_counts.get(d, 0) + 1

    return {
        "total_commits": len(commits),
        "late_night_commits": late_night,
        "peak_hour": peak_hour,
        "commits_by_day": day_counts,
    }
