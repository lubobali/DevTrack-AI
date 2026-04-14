# DevTrack-AI

AI-powered engineering self-tracker. Pulls real data from your git server, LLM observability platform, and Claude Code usage logs — then generates a weekly coaching report that tells you what you did well, what to fix, and what to focus on next week.

Built for personal use by a solo developer building a production AI platform (LuBot — 635 Python files, 5,600+ tests, 6 NVIDIA models). Also serves as a homework submission for DataExpert.io AI Engineering Bootcamp (Week 2).

## Architecture

```
DATA SOURCES                          PROCESSING                    OUTPUT
+------------------+
| Forgejo API      |---> commits
| (git.lubot.ai)   |---> issues    +-------------+
|                  |---> PRs   --->| metrics.py  |---> velocity, code health,
+------------------+               | (local math)|     RECR discipline,
                                   +-------------+     work patterns
+------------------+                      |
| Langfuse         |---> LLM traces       |        +-------------+
| (LuBot Staging)  |---> cost, latency ---+------->| Claude      |---> Weekly Report
+------------------+                      |        | (Sonnet)    |     Issue Triage
                                          |        +-------------+     PR Summary
+------------------+                      |              |
| ccusage          |---> dev costs        |              v
| (Claude Code)    |---> per-project  ----+        +-------------+
+------------------+                               | Langfuse    |
                                                   | (DevTrack)  |
                                                   +-------------+
```

## Features

### 1. Issue Triage
Feed it a GitHub/Forgejo issue — the LLM assigns severity, priority, labels, and recommended owner based on strict rubrics (not vibes).

### 2. PR Summary
Feed it a PR with diff snippets — the LLM writes a technical summary and risk checklist with citations from the actual code.

### 3. Commit Digest Email
Feed it a list of commits from a date range — the LLM drafts a stakeholder email grouped by theme (not per-commit), with risk flags and action items. Every point cites specific commit SHAs.

### 4. Weekly Engineering Report
The main feature. Pulls data from all 4 sources and generates:
- Velocity score (commits, features, refactors, fixes)
- Code health assessment (monolith sizes, dead code, module extraction)
- RECR discipline check (test-first ratio, commit focus)
- Work pattern analysis (late night commits, burnout risk)
- LLM usage insights (LuBot Staging costs, model breakdown)
- Claude Code dev costs (per-project spending from ccusage)
- Self-coaching advice (specific, actionable, anti-sycophantic)

## Data Sources

| Source | What it tracks | How |
|--------|---------------|-----|
| Forgejo API | Commits, issues, PRs | REST API with token auth |
| Langfuse (LuBot) | LLM calls, tokens, cost, latency | Langfuse REST API |
| Langfuse (DevTrack) | This tool's own Claude usage | @observe decorator |
| ccusage | Claude Code dev costs per project | SSH + ccusage CLI on server |

## Safety Guardrails

1. **PII Redaction** — strips server IPs, API keys, emails, phone numbers from all data before sending to Claude
2. **Insufficient Context Fallback** — if no commits or empty issue body, Claude flags low confidence
3. **Schema Validation** — all Claude responses parsed and validated with Pydantic v2. Retry on bad JSON.
4. **Source Citations** — every claim in the report must cite a specific commit SHA or metric

## Setup

```bash
git clone https://github.com/lubobali/DevTrack-AI.git
cd DevTrack-AI
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your keys
```

### Required Environment Variables

```
ANTHROPIC_BASE_URL=https://www.dataexpert.io/api/v1/anthropic
ANTHROPIC_API_KEY=your-anthropic-or-proxy-key
FORGEJO_URL=https://your-git-server.com
FORGEJO_TOKEN=your-forgejo-api-token
FORGEJO_REPO=owner/repo
LANGFUSE_SECRET_KEY=your-devtrack-langfuse-secret
LANGFUSE_PUBLIC_KEY=your-devtrack-langfuse-public
LANGFUSE_BASE_URL=https://us.cloud.langfuse.com
LUBOT_LANGFUSE_SECRET_KEY=your-app-langfuse-secret
LUBOT_LANGFUSE_PUBLIC_KEY=your-app-langfuse-public
LUBOT_LANGFUSE_BASE_URL=https://us.cloud.langfuse.com
REPORT_EMAIL=your-email@example.com
```

## Usage

### Run all 3 features
```bash
python -m devtrack_ai.solution
```

### Run tests
```bash
python -m pytest devtrack_ai/test_solution.py -v
```

## Folder Structure

```
DevTrack-AI/
  devtrack_ai/
    client.py           — Anthropic SDK wrapper + Langfuse tracing
    git_client.py       — Forgejo API client (commits, issues, PRs)
    langfuse_client.py  — LuBot Staging LLM usage data
    ccusage_client.py   — Claude Code dev costs via SSH
    metrics.py          — Engineering metrics calculator (local math)
    schemas.py          — Pydantic v2 models for all I/O
    guardrails.py       — PII redaction + context sufficiency
    solution.py         — 3 features + shared pipeline + CLI
    test_solution.py    — 40 tests across 11 classes
    sample_inputs/      — Real data snapshots from Forgejo
    sample_outputs/     — Real Claude responses
  claude_skills/
    issue_triage.md     — Issue triage prompt
    pr_summary.md       — PR summary prompt
    commit_digest_email.md — Commit digest prompt
    engineering_report.md  — Weekly coaching prompt
  pyproject.toml
  requirements.txt
  writeup.md            — Design note
```

## Tests

40 tests across 11 classes:
- Schema validation (6 tests) — no API calls
- PII redaction (6 tests) — no API calls
- Context sufficiency (4 tests) — no API calls
- Git client (4 tests) — Forgejo API only
- Metrics calculator (4 tests) — pure math
- LLM client (1 test) — 1 API call
- Feature pipelines (7 tests) — real LLM calls (includes commit digest)
- Guardrail integration (5 tests) — end-to-end with PII output redaction
- Langfuse data pull (1 test) — Langfuse API
- ccusage data pull (1 test) — SSH to server

## Built With

- Python 3.13, Pydantic v2, pytest
- NVIDIA NIM API (Nemotron Ultra 253B) or Anthropic API (configurable via .env)
- Forgejo REST API
- Langfuse v4
- ccusage (Claude Code usage tracker)
