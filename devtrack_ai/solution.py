"""DevTrack-AI: 3 features + shared pipeline + CLI.

Feature 1: Issue Triage
Feature 2: PR Summary
Feature 3: Weekly Engineering Report (with self-coaching)
"""

from __future__ import annotations

import json
from pathlib import Path

from devtrack_ai.ccusage_client import fetch_claude_usage
from devtrack_ai.client import call_claude
from devtrack_ai.git_client import fetch_commits, fetch_issues, fetch_repo_stats
from devtrack_ai.guardrails import check_context, redact_pii
from devtrack_ai.langfuse_client import fetch_lubot_traces
from devtrack_ai.metrics import calc_code_health, calc_velocity, calc_work_patterns
from devtrack_ai.schemas import (
    CommitDigestEmail,
    CommitDigestInput,
    EngineeringMetrics,
    IssueTriageInput,
    IssueTriageOutput,
    PRSummaryInput,
    PRSummaryOutput,
)

SKILLS_DIR = Path(__file__).parent.parent / "claude_skills"


# === Shared Pipeline ===


def _load_skill(name: str) -> str:
    """Load a prompt skill from claude_skills/ directory."""
    return (SKILLS_DIR / name).read_text()


def _redact_model_strings(obj):
    """Recursively redact PII from string values in a parsed dict/list."""
    if isinstance(obj, str):
        redacted, _ = redact_pii(obj)
        return redacted
    if isinstance(obj, list):
        return [_redact_model_strings(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _redact_model_strings(v) for k, v in obj.items()}
    return obj


def _parse_json_response(text: str, model_class, system_prompt: str, user_content: str):
    """Parse Claude's response as JSON, validate with Pydantic. Retry once on failure."""
    # Strip markdown code fences if present
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)

    try:
        data = json.loads(cleaned)
        data = _redact_model_strings(data)
        return model_class(**data)
    except (json.JSONDecodeError, Exception):
        # Retry once with explicit instruction
        retry_prompt = (
            f"Your previous response was not valid JSON. "
            f"Respond with ONLY valid JSON matching the schema in the system prompt. "
            f"No markdown, no explanation, just the JSON object.\n\n"
            f"Original request:\n{user_content}"
        )
        retry_text = call_claude(system_prompt, retry_prompt, max_tokens=2000)
        retry_cleaned = retry_text.strip()
        if retry_cleaned.startswith("```"):
            lines = retry_cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            retry_cleaned = "\n".join(lines)
        data = json.loads(retry_cleaned)
        data = _redact_model_strings(data)
        return model_class(**data)


# === Feature 1: Issue Triage ===


def triage_issue(inp: IssueTriageInput) -> IssueTriageOutput:
    """Triage a GitHub issue — severity, priority, labels, owner."""
    # Redact PII from input
    redacted_title, _ = redact_pii(inp.title)
    redacted_body, _ = redact_pii(inp.body)
    redacted_comments = []
    for c in inp.comments:
        rc, _ = redact_pii(c)
        redacted_comments.append(rc)

    # Check context
    ctx = check_context("issue", {"body": redacted_body, "comments": redacted_comments})

    # Build user content
    user_content = f"Title: {redacted_title}\n\nBody: {redacted_body}"
    if redacted_comments:
        user_content += "\n\nComments:\n" + "\n".join(f"- {c}" for c in redacted_comments)
    if not ctx["sufficient"]:
        user_content += f"\n\nNOTE: {ctx['message']}"

    system_prompt = _load_skill("issue_triage.md")
    response = call_claude(system_prompt, user_content)
    return _parse_json_response(response, IssueTriageOutput, system_prompt, user_content)


# === Feature 2: PR Summary ===


def summarize_pr(inp: PRSummaryInput) -> PRSummaryOutput:
    """Summarize a PR with risk checklist."""
    # Redact PII from input
    redacted_title, _ = redact_pii(inp.title)
    redacted_desc, _ = redact_pii(inp.description)
    redacted_diffs = []
    for d in inp.diff_snippets:
        rd, _ = redact_pii(d)
        redacted_diffs.append(rd)

    # Check context
    ctx = check_context("pr", {"diff_snippets": redacted_diffs})

    # Build user content
    user_content = f"PR Title: {redacted_title}\n\nDescription: {redacted_desc}"
    if redacted_diffs:
        user_content += "\n\nDiff Snippets:\n" + "\n---\n".join(redacted_diffs)
    if not ctx["sufficient"]:
        user_content += f"\n\nNOTE: {ctx['message']}"

    system_prompt = _load_skill("pr_summary.md")
    response = call_claude(system_prompt, user_content)
    return _parse_json_response(response, PRSummaryOutput, system_prompt, user_content)


# === Feature 3: Commit Digest Email ===


def generate_commit_digest(inp: CommitDigestInput) -> CommitDigestEmail:
    """Generate a stakeholder email summarizing commits in a date range."""
    # Redact PII from commit messages
    redacted_commits = []
    for c in inp.commits:
        msg, _ = redact_pii(c.message)
        redacted_commits.append(f"[{c.sha}] {msg} by {c.author} on {c.date}")

    # Check context
    ctx = check_context("commits", {"commits": inp.commits})

    # Build user content
    user_content = f"Date range: {inp.date_range_start} to {inp.date_range_end}\n\nCommits:\n"
    user_content += "\n".join(f"- {c}" for c in redacted_commits)
    if not ctx["sufficient"]:
        user_content += f"\n\nNOTE: {ctx['message']}"

    system_prompt = _load_skill("commit_digest_email.md")
    response = call_claude(system_prompt, user_content)
    return _parse_json_response(response, CommitDigestEmail, system_prompt, user_content)


# === Feature 4: Weekly Engineering Report ===


class EngineeringReport:
    """Structured engineering report output."""

    def __init__(self, **kwargs):
        self.week_summary = kwargs.get("week_summary", "")
        self.velocity_score = kwargs.get("velocity_score", "medium")
        self.health_score = kwargs.get("health_score", "healthy")
        self.wins = kwargs.get("wins", [])
        self.concerns = kwargs.get("concerns", [])
        self.coaching = kwargs.get("coaching", [])
        self.burnout_risk = kwargs.get("burnout_risk", "low")
        self.burnout_note = kwargs.get("burnout_note", "")
        self.llm_insights = kwargs.get("llm_insights", [])
        self.next_week_priorities = kwargs.get("next_week_priorities", [])
        self.source_citations = kwargs.get("source_citations", [])


def generate_report(days: int = 7) -> EngineeringReport:
    """Generate weekly engineering self-coaching report from real git data."""
    # Pull real data from Forgejo
    commits = fetch_commits(limit=100, sha="develop")

    # Filter to date range (approximate — last N days)
    from datetime import datetime, timedelta, timezone

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    recent = []
    for c in commits:
        try:
            dt = datetime.fromisoformat(c["date"].replace("Z", "+00:00"))
            if dt >= cutoff:
                recent.append(c)
        except (ValueError, TypeError):
            continue

    # Check context
    ctx = check_context("commits", {"commits": recent})

    # Calculate metrics locally (no tokens burned)
    velocity = calc_velocity(recent)
    work_patterns = calc_work_patterns(recent)

    # Pull LLM usage from LuBot Staging Langfuse
    langfuse_data = fetch_lubot_traces(days=days)

    # Pull Claude Code dev costs from ccusage on Hetzner
    ccusage_data = fetch_claude_usage(days=days)

    # Build metrics summary for Claude
    metrics_text = f"""METRICS (calculated from git data — these are FACTS):

Velocity:
- Total commits this week: {velocity['total_commits']}
- Feature commits: {velocity['feature_commits']}
- Fix commits: {velocity['fix_commits']}
- Refactor commits: {velocity['refactor_commits']}
- Commits that include test files (RECR discipline): {velocity['commits_with_tests']} out of {velocity['total_commits']} ({round(velocity['commits_with_tests'] / max(velocity['total_commits'], 1) * 100)}% RECR compliance)
- NOTE: This developer follows RECR (Red-Execute-Check-Repeat) — tests are bundled WITH implementation commits, not in separate "test only" commits. A high commits_with_tests ratio means GOOD test discipline, not bad.
- Other commits (no test files): {velocity['total_commits'] - velocity['commits_with_tests']}

Work Patterns:
- Late night commits (midnight-6am): {work_patterns['late_night_commits']}
- Peak coding hour: {work_patterns['peak_hour']}:00

Recent Commits:
"""
    for c in recent[:30]:
        metrics_text += f"- [{c['sha']}] {c['message']} ({c['date'][:10]})\n"

    # Add Langfuse LLM data if available
    if langfuse_data.get("available") and langfuse_data.get("total_traces", 0) > 0:
        metrics_text += f"""
LLM Usage (from Langfuse — LuBot Staging):
- Total LLM calls this week: {langfuse_data['total_traces']}
- Total cost: ${langfuse_data['total_cost']}
- Input tokens: {langfuse_data['input_tokens']:,}
- Output tokens: {langfuse_data['output_tokens']:,}
- Average latency: {langfuse_data['avg_latency_ms']}ms
- Error count: {langfuse_data['error_count']}
- Models used: {', '.join(f'{m}: {c} calls' for m, c in langfuse_data['models_used'].items()) if langfuse_data['models_used'] else 'none tracked yet'}
"""
    else:
        metrics_text += "\nLLM Usage: No Langfuse data available yet (instrumentation may be new).\n"

    # Add Claude Code dev costs
    if ccusage_data.get("available") and ccusage_data.get("total_cost", 0) > 0:
        metrics_text += f"""
Claude Code Dev Costs (from ccusage — your building costs):
- Total cost this week: ${ccusage_data['total_cost']}
- Total tokens: {ccusage_data['total_tokens']:,}
- Days tracked: {ccusage_data['days_tracked']}
- Models: {', '.join(f'{m}: ${c}' for m, c in ccusage_data.get('models', {}).items()) if ccusage_data.get('models') else 'unknown'}
- Per-project breakdown: {', '.join(f'{p}: ${d["cost"]} ({d["sessions"]} sessions)' for p, d in ccusage_data.get('projects', {}).items()) if ccusage_data.get('projects') else 'no project data'}
"""
    else:
        metrics_text += "\nClaude Code Dev Costs: No ccusage data available.\n"

    if not ctx["sufficient"]:
        metrics_text += f"\nNOTE: {ctx['message']}"

    system_prompt = _load_skill("engineering_report.md")
    response = call_claude(system_prompt, metrics_text, max_tokens=3000)

    # Parse response
    cleaned = response.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # Retry
        retry_prompt = (
            "Your previous response was not valid JSON. "
            "Respond with ONLY the JSON object, no markdown.\n\n" + metrics_text
        )
        retry_text = call_claude(system_prompt, retry_prompt, max_tokens=3000)
        retry_cleaned = retry_text.strip()
        if retry_cleaned.startswith("```"):
            lines = retry_cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            retry_cleaned = "\n".join(lines)
        data = json.loads(retry_cleaned)

    return EngineeringReport(**data)


# === CLI ===


def main():
    """Run all 3 features with real data and print results."""
    import sys

    print("=" * 60)
    print("DevTrack-AI — Engineering Self-Tracker")
    print("=" * 60)

    # Feature 1: Triage a sample issue
    print("\n--- Feature 1: Issue Triage ---")
    issues = fetch_issues(state="open", limit=1)
    if issues:
        issue = issues[0]
        inp = IssueTriageInput(
            title=issue["title"],
            body=issue.get("body", "No body"),
            comments=[],
        )
        result = triage_issue(inp)
        print(json.dumps({"severity": result.severity, "priority": result.priority, "labels": result.labels, "owner": result.recommended_owner}, indent=2))
    else:
        print("No open issues found.")

    # Feature 2: (skip if no PRs — use sample data)
    print("\n--- Feature 2: PR Summary ---")
    print("(Using recent commit data as sample)")
    commits = fetch_commits(limit=5)
    if commits:
        inp = PRSummaryInput(
            title=f"Recent changes: {commits[0]['message']}",
            description="Recent development activity on LuBot",
            diff_snippets=[c["message"] for c in commits[:3]],
        )
        result = summarize_pr(inp)
        print(json.dumps({"summary": result.summary, "risks": len(result.risk_checklist)}, indent=2))

    # Feature 3: Commit Digest Email
    print("\n--- Feature 3: Commit Digest Email ---")
    if commits:
        from devtrack_ai.schemas import CommitDigestInput, CommitEntry
        digest_inp = CommitDigestInput(
            commits=[CommitEntry(sha=c["sha"], message=c["message"], author=c["author"], date=c["date"][:10]) for c in commits],
            date_range_start=commits[-1]["date"][:10],
            date_range_end=commits[0]["date"][:10],
        )
        digest_result = generate_commit_digest(digest_inp)
        print(json.dumps({"subject": digest_result.subject, "what_changed": digest_result.what_changed, "action_needed": digest_result.action_needed}, indent=2))

    # Feature 4: Weekly Engineering Report
    print("\n--- Feature 4: Weekly Engineering Report ---")
    report = generate_report(days=7)
    print(json.dumps({
        "week_summary": report.week_summary,
        "velocity": report.velocity_score,
        "health": report.health_score,
        "burnout_risk": report.burnout_risk,
        "wins": report.wins,
        "concerns": report.concerns,
        "coaching": report.coaching,
        "priorities": report.next_week_priorities,
    }, indent=2))

    print("\n" + "=" * 60)
    print("Done. Check Langfuse dashboard for traces.")


if __name__ == "__main__":
    main()
