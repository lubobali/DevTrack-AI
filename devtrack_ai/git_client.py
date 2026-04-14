"""Forgejo API client — pulls real commits, issues, PRs from git.lubot.ai."""

from __future__ import annotations

import os

import requests
from dotenv import load_dotenv

load_dotenv()

FORGEJO_URL = os.getenv("FORGEJO_URL", "https://git.lubot.ai")
FORGEJO_TOKEN = os.getenv("FORGEJO_TOKEN", "")
FORGEJO_REPO = os.getenv("FORGEJO_REPO", "lubo/lubot")


def _headers() -> dict:
    return {"Authorization": f"token {FORGEJO_TOKEN}", "Accept": "application/json"}


def _api(path: str, params: dict | None = None) -> list | dict:
    url = f"{FORGEJO_URL}/api/v1{path}"
    resp = requests.get(url, headers=_headers(), params=params or {}, timeout=15)
    resp.raise_for_status()
    return resp.json()


def fetch_commits(limit: int = 50, sha: str = "develop") -> list[dict]:
    """Fetch recent commits from the repo."""
    raw = _api(f"/repos/{FORGEJO_REPO}/commits", {"sha": sha, "limit": limit})
    results = []
    for c in raw:
        files = [f["filename"] for f in c.get("files", []) or []]
        stats = c.get("stats", {}) or {}
        results.append({
            "sha": c["sha"][:7],
            "full_sha": c["sha"],
            "message": c["commit"]["message"].split("\n")[0],
            "author": c["commit"]["author"]["name"],
            "date": c["commit"]["author"]["date"],
            "files_changed": files,
            "additions": stats.get("additions", 0),
            "deletions": stats.get("deletions", 0),
        })
    return results


def fetch_issues(state: str = "open", limit: int = 50) -> list[dict]:
    """Fetch issues from the repo."""
    raw = _api(f"/repos/{FORGEJO_REPO}/issues", {"state": state, "limit": limit, "type": "issues"})
    return [
        {
            "id": i["number"],
            "title": i["title"],
            "body": i.get("body", ""),
            "state": i["state"],
            "labels": [l["name"] for l in i.get("labels", [])],
            "created": i["created_at"],
            "comments_count": i.get("comments", 0),
        }
        for i in raw
    ]


def fetch_prs(state: str = "all", limit: int = 50) -> list[dict]:
    """Fetch pull requests from the repo."""
    raw = _api(f"/repos/{FORGEJO_REPO}/pulls", {"state": state, "limit": limit})
    return [
        {
            "id": p["number"],
            "title": p["title"],
            "body": p.get("body", ""),
            "state": p["state"],
            "merged": p.get("merged", False),
            "created": p["created_at"],
            "diff_url": p.get("diff_url", ""),
        }
        for p in raw
    ]


def fetch_repo_stats() -> dict:
    """Fetch repo-level stats (stars, forks, size, open issues)."""
    raw = _api(f"/repos/{FORGEJO_REPO}")
    return {
        "stars": raw.get("stars_count", 0),
        "forks": raw.get("forks_count", 0),
        "open_issues": raw.get("open_issues_count", 0),
        "size": raw.get("size", 0),
        "default_branch": raw.get("default_branch", "main"),
        "updated": raw.get("updated_at", ""),
    }
