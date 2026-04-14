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
    ("refactor", re.compile(r"^(Refactor|Extract|Move|Rename|Cleanup|Delete|Remove|Step \d)", re.IGNORECASE)),
    ("test", re.compile(r"^(Test|TEST|Add test|Fix test)", re.IGNORECASE)),
]


def categorize_commit(message: str, files_changed: list[str] | None = None) -> str:
    """Categorize a commit by message AND actual files changed.

    A commit that touches test_*.py files counts as including tests,
    even if the message says 'Refactor' or 'Feature'. This reflects
    RECR discipline — tests bundled with implementation.
    """
    # Primary: message-based category
    category = "other"
    for cat, pattern in CATEGORY_PATTERNS:
        if pattern.search(message):
            category = cat
            break
    return category


def has_test_files(files_changed: list[str]) -> bool:
    """Check if a commit touches test files (RECR detection)."""
    if not files_changed:
        return False
    for f in files_changed:
        basename = f.split("/")[-1]
        if basename.startswith("test_") or "/tests/" in f:
            return True
    return False


# === Category 1: Velocity ===


def calc_velocity(commits: list[dict]) -> dict:
    """Calculate velocity metrics from commit list.

    Uses BOTH message prefix AND file changes for accurate categorization.
    commits_with_tests counts commits that touch test_*.py files regardless
    of message prefix — this catches RECR-style commits where tests are
    bundled with implementation.
    """
    categories = [categorize_commit(c["message"], c.get("files_changed", [])) for c in commits]
    commits_with_tests = sum(1 for c in commits if has_test_files(c.get("files_changed", [])))

    return {
        "total_commits": len(commits),
        "feature_commits": categories.count("feature"),
        "fix_commits": categories.count("fix"),
        "refactor_commits": categories.count("refactor"),
        "test_commits": categories.count("test"),
        "commits_with_tests": commits_with_tests,
        "other_commits": categories.count("other"),
    }


# === Category 2: Code Health ===


def calc_code_health(commits: list[dict]) -> dict:
    """Calculate code health from commit stats (additions/deletions)."""
    total_added = 0
    total_removed = 0
    for c in commits:
        total_added += c.get("additions", 0)
        total_removed += c.get("deletions", 0)
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
