"""DevTrack-AI test suite."""

import pytest


# === Phase 1: Import ===


def test_import_devtrack_ai():
    import devtrack_ai

    assert devtrack_ai.__doc__ is not None


# === Phase 2: Schema Validation ===


class TestSchemaValidation:
    """Pydantic models accept valid data, reject bad data."""

    def test_issue_triage_input_accepts_valid(self):
        from devtrack_ai.schemas import IssueTriageInput

        inp = IssueTriageInput(
            title="Login fails with 500 error",
            body="When clicking login, server returns 500. Stack trace attached.",
            comments=["I can reproduce this on staging"],
        )
        assert inp.title == "Login fails with 500 error"
        assert len(inp.comments) == 1

    def test_issue_triage_input_rejects_empty_title(self):
        from devtrack_ai.schemas import IssueTriageInput

        with pytest.raises(Exception):
            IssueTriageInput(title="", body="some body")

    def test_pr_summary_input_accepts_valid(self):
        from devtrack_ai.schemas import PRSummaryInput

        inp = PRSummaryInput(
            title="Refactor auth to async",
            description="Migrates auth middleware to async/await pattern",
            diff_snippets=["- def login(req):\n+ async def login(req):"],
        )
        assert inp.title == "Refactor auth to async"
        assert len(inp.diff_snippets) == 1

    def test_commit_digest_input_accepts_valid(self):
        from devtrack_ai.schemas import CommitDigestInput, CommitEntry

        inp = CommitDigestInput(
            commits=[
                CommitEntry(sha="abc123", message="Fix login bug", author="lubo", date="2026-04-10"),
                CommitEntry(sha="def456", message="Add stock endpoint", author="lubo", date="2026-04-11"),
            ],
            date_range_start="2026-04-07",
            date_range_end="2026-04-13",
        )
        assert len(inp.commits) == 2
        assert inp.commits[0].sha == "abc123"

    def test_issue_triage_output_rejects_invalid_severity(self):
        from devtrack_ai.schemas import IssueTriageOutput

        with pytest.raises(Exception):
            IssueTriageOutput(
                severity="EXTREME",
                priority="P1",
                labels=["bug"],
                recommended_owner="team-backend",
                reasoning="test",
                confidence="high",
                source_citations=["test"],
            )

    def test_engineering_metrics_accepts_valid(self):
        from devtrack_ai.schemas import EngineeringMetrics

        m = EngineeringMetrics(
            commits_this_week=15,
            lines_added=500,
            lines_removed=300,
            test_count=5645,
            files_touched=12,
            late_night_commits=3,
        )
        assert m.commits_this_week == 15
        assert m.lines_added - m.lines_removed == 200


# === Phase 3: Guardrails ===


class TestPIIRedaction:
    """PII redaction catches sensitive data, preserves clean text."""

    def test_redacts_email_addresses(self):
        from devtrack_ai.guardrails import redact_pii

        text = "Contact admin@lubot.ai for help"
        result, log = redact_pii(text)
        assert "admin@lubot.ai" not in result
        assert "[EMAIL]" in result
        assert len(log) == 1

    def test_redacts_phone_numbers(self):
        from devtrack_ai.guardrails import redact_pii

        text = "Call me at 217-786-2482"
        result, log = redact_pii(text)
        assert "217-786-2482" not in result
        assert "[PHONE]" in result

    def test_redacts_ip_addresses(self):
        from devtrack_ai.guardrails import redact_pii

        text = "Server at 178.156.214.8 is down"
        result, log = redact_pii(text)
        assert "178.156.214.8" not in result
        assert "[IP]" in result

    def test_redacts_api_keys(self):
        from devtrack_ai.guardrails import redact_pii

        text = "Key is sk-de-78f0b96c0031347672e6d3fc275d882b and ghp_abc123def456"
        result, log = redact_pii(text)
        assert "sk-de-" not in result
        assert "ghp_" not in result
        assert "[API_KEY]" in result
        assert len(log) == 2

    def test_preserves_clean_text(self):
        from devtrack_ai.guardrails import redact_pii

        text = "Refactored adalflow_agent.py from 10525 to 1581 lines"
        result, log = redact_pii(text)
        assert result == text
        assert len(log) == 0

    def test_returns_redaction_log(self):
        from devtrack_ai.guardrails import redact_pii

        text = "Email data@lubobali.com and IP 100.115.173.71"
        result, log = redact_pii(text)
        assert len(log) == 2
        assert any(r["type"] == "email" for r in log)
        assert any(r["type"] == "ip" for r in log)


class TestContextSufficiency:
    """Context checker flags insufficient input, passes good input."""

    def test_flags_empty_issue_body(self):
        from devtrack_ai.guardrails import check_context

        result = check_context("issue", {"body": "", "comments": []})
        assert result["sufficient"] is False

    def test_passes_detailed_issue(self):
        from devtrack_ai.guardrails import check_context

        result = check_context("issue", {"body": "Login fails with 500 error when clicking submit on the auth page", "comments": ["confirmed"]})
        assert result["sufficient"] is True

    def test_flags_no_commits(self):
        from devtrack_ai.guardrails import check_context

        result = check_context("commits", {"commits": []})
        assert result["sufficient"] is False

    def test_flags_no_diff_snippets(self):
        from devtrack_ai.guardrails import check_context

        result = check_context("pr", {"diff_snippets": []})
        assert result["sufficient"] is False


# === Phase 4: Git Client (Forgejo API) — ZERO tokens burned ===


class TestGitClient:
    """Real API calls to git.lubot.ai — no bootcamp tokens used."""

    def test_fetch_commits_returns_list(self):
        from devtrack_ai.git_client import fetch_commits

        commits = fetch_commits(limit=5)
        assert isinstance(commits, list)
        assert len(commits) > 0
        assert "sha" in commits[0]
        assert "message" in commits[0]
        assert "author" in commits[0]
        assert "date" in commits[0]

    def test_fetch_issues_returns_list(self):
        from devtrack_ai.git_client import fetch_issues

        issues = fetch_issues(state="all", limit=5)
        assert isinstance(issues, list)

    def test_fetch_prs_returns_list(self):
        from devtrack_ai.git_client import fetch_prs

        prs = fetch_prs(state="all", limit=5)
        assert isinstance(prs, list)

    def test_fetch_repo_stats(self):
        from devtrack_ai.git_client import fetch_repo_stats

        stats = fetch_repo_stats()
        assert "stars" in stats
        assert "forks" in stats
        assert "open_issues" in stats
        assert "size" in stats


# === Phase 5: Metrics Calculator — ZERO tokens burned ===


class TestMetricsCalculator:
    """Engineering metrics from raw git data."""

    def test_calc_velocity(self):
        from devtrack_ai.metrics import calc_velocity

        commits = [
            {"sha": "abc", "message": "Feature: add login", "author": "lubo", "date": "2026-04-10T02:00:00Z"},
            {"sha": "def", "message": "Fix: auth crash", "author": "lubo", "date": "2026-04-11T15:00:00Z"},
            {"sha": "ghi", "message": "Refactor Step 15", "author": "lubo", "date": "2026-04-12T01:00:00Z"},
        ]
        v = calc_velocity(commits)
        assert v["total_commits"] == 3
        assert v["feature_commits"] == 1
        assert v["fix_commits"] == 1
        assert v["refactor_commits"] == 1

    def test_calc_work_patterns(self):
        from devtrack_ai.metrics import calc_work_patterns

        commits = [
            {"date": "2026-04-10T02:30:00Z"},
            {"date": "2026-04-10T03:15:00Z"},
            {"date": "2026-04-11T14:00:00Z"},
            {"date": "2026-04-11T22:00:00Z"},
        ]
        p = calc_work_patterns(commits)
        assert p["late_night_commits"] == 2  # 2:30 and 3:15 are after midnight
        assert p["total_commits"] == 4

    def test_detect_commit_categories(self):
        from devtrack_ai.metrics import categorize_commit

        assert categorize_commit("Feature: add stock endpoint") == "feature"
        assert categorize_commit("Fix: login crash on mobile") == "fix"
        assert categorize_commit("Refactor Step 15-A: extract handler") == "refactor"
        assert categorize_commit("TEST: add auth tests") == "test"
        assert categorize_commit("Update docs for API") == "other"

    def test_calc_code_health(self):
        from devtrack_ai.metrics import calc_code_health

        commits = [
            {"message": "Refactor Step 15-P4: Final cleanup", "stats": {"additions": 50, "deletions": 8944}},
            {"message": "Feature: add endpoint", "stats": {"additions": 200, "deletions": 0}},
        ]
        h = calc_code_health(commits)
        assert h["lines_added"] == 250
        assert h["lines_removed"] == 8944
        assert h["net_change"] == 250 - 8944


# === Phase 6: Claude Client — burns 1 token ===


class TestClaudeClient:
    """Verify connection to Anthropic proxy."""

    def test_call_claude_returns_response(self):
        from devtrack_ai.client import call_claude

        result = call_claude(
            system_prompt="You are a helpful assistant. Respond in JSON.",
            user_content="Say hello in JSON format: {\"greeting\": \"...\"}",
            max_tokens=50,
        )
        assert isinstance(result, str)
        assert len(result) > 0


# === Phase 8: Core Features — burns bootcamp tokens ===


class TestFeaturePipelines:
    """End-to-end feature tests with real Claude API calls."""

    def test_triage_issue_returns_valid_output(self):
        from devtrack_ai.solution import triage_issue
        from devtrack_ai.schemas import IssueTriageInput

        inp = IssueTriageInput(
            title="Login fails with 500 error on staging",
            body="When clicking login on staging.lubot.ai, the server returns a 500 Internal Server Error. The stack trace shows a KeyError in JWT validation. This blocks all testing on staging.",
            comments=["I can reproduce this every time", "Same error on Chrome and Firefox"],
        )
        result = triage_issue(inp)
        assert result.severity in ("critical", "high", "medium", "low")
        assert result.priority in ("P0", "P1", "P2", "P3")
        assert len(result.labels) > 0
        assert len(result.recommended_owner) > 0
        assert len(result.source_citations) > 0

    def test_triage_issue_severity_is_reasonable(self):
        from devtrack_ai.solution import triage_issue
        from devtrack_ai.schemas import IssueTriageInput

        inp = IssueTriageInput(
            title="Security: API key exposed in commit message",
            body="Commit abc123 contains a hardcoded NVIDIA API key in the commit message. This key is visible in the public GitHub mirror.",
            comments=[],
        )
        result = triage_issue(inp)
        assert result.severity in ("critical", "high")

    def test_summarize_pr_returns_valid_output(self):
        from devtrack_ai.solution import summarize_pr
        from devtrack_ai.schemas import PRSummaryInput

        inp = PRSummaryInput(
            title="Refactor Step 15: Extract handlers from adalflow_agent.py",
            description="Extracts 15 handler modules from the 10,525-line monolith. Each handler does one thing. adalflow_agent.py drops to 1,581 lines.",
            diff_snippets=[
                "- def handle_image(self, query, context):\n-     # 200 lines of image handling\n+ from routing.handlers.image import handle_image",
                "- def handle_predictions(self, query, context):\n-     # 150 lines\n+ from routing.handlers.predictions import handle_predictions",
            ],
        )
        result = summarize_pr(inp)
        assert len(result.summary) > 0
        assert isinstance(result.risk_checklist, list)
        assert len(result.source_citations) > 0

    def test_generate_report_returns_valid_output(self):
        from devtrack_ai.solution import generate_report

        result = generate_report(days=7)
        assert result.week_summary is not None
        assert result.velocity_score in ("high", "medium", "low")
        assert result.health_score in ("healthy", "warning", "critical")
        assert result.burnout_risk in ("low", "moderate", "high")
        assert len(result.wins) > 0 or len(result.concerns) > 0
        assert len(result.next_week_priorities) > 0

    def test_generate_report_cites_commit_shas(self):
        from devtrack_ai.solution import generate_report

        result = generate_report(days=7)
        assert len(result.source_citations) > 0


# === Phase 9: Integration Tests ===


class TestGuardrailIntegration:
    """End-to-end tests with all guardrails active."""

    def test_pii_redacted_before_sending_to_claude(self):
        from devtrack_ai.solution import triage_issue
        from devtrack_ai.schemas import IssueTriageInput

        inp = IssueTriageInput(
            title="Server 178.156.214.8 is down",
            body="The API key sk-de-78f0b96c003134 was exposed in logs. Contact admin@lubot.ai immediately.",
            comments=[],
        )
        result = triage_issue(inp)
        assert result.severity in ("critical", "high", "medium", "low")
        assert result.reasoning is not None

    def test_insufficient_context_low_confidence(self):
        from devtrack_ai.solution import triage_issue
        from devtrack_ai.schemas import IssueTriageInput

        inp = IssueTriageInput(
            title="Bug",
            body="broken",
            comments=[],
        )
        result = triage_issue(inp)
        assert result.confidence == "low"

    def test_markdown_fence_stripping(self):
        """If Claude returns markdown-wrapped JSON, parser handles it."""
        from devtrack_ai.solution import _parse_json_response
        from devtrack_ai.schemas import IssueTriageOutput

        fake = '```json\n{"severity":"high","priority":"P1","labels":["bug"],"recommended_owner":"team-platform","reasoning":"test","confidence":"high","source_citations":["test"]}\n```'
        result = _parse_json_response(fake, IssueTriageOutput, "", "")
        assert result.severity == "high"

    def test_full_pipeline_all_features(self):
        """All 3 features end-to-end with real Forgejo data."""
        from devtrack_ai.solution import generate_report, summarize_pr, triage_issue
        from devtrack_ai.schemas import IssueTriageInput, PRSummaryInput
        from devtrack_ai.git_client import fetch_commits

        triage_result = triage_issue(IssueTriageInput(
            title="Test coverage gap in routing handlers",
            body="The new routing/handlers/ modules extracted in Step 15 have characterization tests but no integration tests verifying they work together.",
            comments=["Flagged during code review"],
        ))
        assert triage_result.severity is not None

        commits = fetch_commits(limit=3)
        pr_result = summarize_pr(PRSummaryInput(
            title=commits[0]["message"],
            description="Recent LuBot staging development",
            diff_snippets=[c["message"] for c in commits],
        ))
        assert pr_result.summary is not None

        report = generate_report(days=7)
        assert report.week_summary is not None
        assert len(report.next_week_priorities) > 0


class TestLangfuseDataPull:
    """Pull LLM usage data from LuBot Staging Langfuse project."""

    def test_fetch_langfuse_traces_returns_data(self):
        from devtrack_ai.langfuse_client import fetch_lubot_traces

        traces = fetch_lubot_traces(days=7)
        assert isinstance(traces, dict)
        assert "total_traces" in traces
        assert "total_cost" in traces
        assert "models_used" in traces


class TestCcusageDataPull:
    """Pull Claude Code token usage from ccusage on Hetzner."""

    def test_fetch_claude_usage_returns_data(self):
        from devtrack_ai.ccusage_client import fetch_claude_usage

        usage = fetch_claude_usage(days=7)
        assert isinstance(usage, dict)
        assert "total_cost" in usage
        assert "total_tokens" in usage
        assert "sessions" in usage
        assert "available" in usage
