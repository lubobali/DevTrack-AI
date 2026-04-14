# DevTrack-AI — AI Operating Context

## Project Overview
DevTrack-AI is an AI-powered engineering self-tracker that pulls real data from 4 sources (Forgejo, Langfuse, ccusage, Anthropic API) and generates weekly coaching reports. Built for a solo developer managing a production AI platform (LuBot — 635 Python files, 5,600+ tests).

**Goal:** Replace manual progress tracking with automated, data-driven self-coaching. Every insight must be grounded in real metrics — no hallucinations, no sycophancy.

## Build / Test / Lint Commands

```bash
# Activate environment
source venv/bin/activate

# Run all tests (37 tests — ~2 min, includes real API calls)
python -m pytest devtrack_ai/test_solution.py -v

# Run fast tests only (no API calls — ~1 sec)
python -m pytest devtrack_ai/test_solution.py -v -k "Schema or PII or Context or Metrics"

# Run the full demo (all 3 features)
python -m devtrack_ai.solution

# Lint
ruff check devtrack_ai/
ruff format devtrack_ai/
```

## Folder Map + Key Modules

```
DevTrack-AI/
  devtrack_ai/
    client.py           — Claude API wrapper. Raw HTTP + SSE parsing.
                          Langfuse @observe traces every call.
    git_client.py       — Forgejo REST API. Pulls commits, issues, PRs, repo stats.
                          Auth via FORGEJO_TOKEN in .env.
    langfuse_client.py  — Pulls LLM usage from LuBot Staging Langfuse project.
                          Separate keys from DevTrack-AI's own Langfuse.
    ccusage_client.py   — SSH to Hetzner, runs ccusage CLI, parses JSON output.
                          Per-project Claude Code dev costs.
    metrics.py          — Pure Python math. Velocity, code health, work patterns.
                          NO LLM calls. NO tokens burned.
    schemas.py          — Pydantic v2 models. 9 models for all inputs and outputs.
                          IssueTriageOutput uses Literal enums (not open strings).
    guardrails.py       — PII redaction (regex: email, phone, IP, API keys).
                          Context sufficiency checker. Applied pre and post Claude.
    solution.py         — Main entry point. 3 features + shared _run_pipeline().
                          CLI via __main__. Loads prompts from claude_skills/.
    test_solution.py    — 37 tests, 10 classes. Layered: unit > integration > e2e.
  claude_skills/
    issue_triage.md     — Strict rubrics: severity/priority/labels/owner.
    pr_summary.md       — 5 risk categories, citation required.
    commit_digest_email.md — Group by theme, not per-commit.
    engineering_report.md  — Self-coaching with anti-sycophancy rules.
```

## Coding Conventions and Style Rules

- **RECR loop**: Write test FIRST, implement ONE thing, check, repeat. No batching.
- **Pydantic for all I/O**: Every input and output has a schema. No raw dicts crossing module boundaries.
- **Literal types for enums**: `Literal["critical", "high", "medium", "low"]` — not open strings.
- **PII redaction on ALL data**: Before sending to Claude AND after receiving response.
- **Prompts in markdown files**: claude_skills/*.md loaded at runtime. Never hardcode prompts in Python.
- **JSON output from Claude**: Every prompt specifies exact JSON schema. Parse with json.loads + Pydantic validation.
- **Retry once on bad JSON**: Strip markdown fences first, then retry with explicit instruction.
- **Line length**: 120 chars (ruff config).
- **Python 3.11+**: Uses `from __future__ import annotations` for forward refs.

## Deployment / Runtime Constraints

- **API**: Supports NVIDIA NIM (Nemotron Ultra 253B) and Anthropic proxy. Set `LLM_PROVIDER=nvidia` or `LLM_PROVIDER=anthropic` in .env. Currently using NVIDIA NIM.
- **SSH required for ccusage**: Must have SSH key access to root@[HETZNER_IP] (Hetzner). If SSH fails, ccusage data is skipped gracefully.
- **Two Langfuse projects**: DevTrack-AI (own traces) and LuBot Staging (app traces). Different keys in .env. Do not mix them.
- **No database**: Stateless. Each run pulls fresh data. Historical comparison requires saving outputs manually.

## Security / Privacy Boundaries

- **.env contains secrets** — NEVER commit .env. Only .env.example goes to git.
- **PII in commit messages** — Real commits contain server IPs ([SERVER_IP]), API keys (sk-de-...), email addresses. guardrails.py strips these BEFORE Claude sees them.
- **Forgejo token is read-only** — Can read repos/issues but cannot push code.
- **SSH key gives root access to Hetzner** — ccusage_client.py only runs `ccusage` commands, never destructive operations.

## Do / Don't Instructions for AI Assistants

### DO
- Run tests after every change: `python -m pytest devtrack_ai/test_solution.py -v`
- Add PII patterns to guardrails.py if you find new sensitive data types
- Keep prompts in claude_skills/*.md — load at runtime, never inline
- Use Pydantic models for any new input/output
- Mock external APIs in tests (Claude, Forgejo, Langfuse, SSH)
- Keep metrics.py free of LLM calls — pure math only

### DON'T
- Don't commit .env or any file with real API keys
- Don't hardcode model names — read from LLM_PROVIDER, ANTHROPIC_MODEL, NVIDIA_MODEL in .env
- Don't add LLM calls to metrics.py — it must stay zero-cost
- Don't weaken tests to make them pass — fix the implementation
- Don't remove PII redaction for any reason
- Don't call SSH commands other than ccusage on the Hetzner server
- Don't create new prompt files without the JSON schema + rules + anti-hallucination section

## Common Pitfalls and Debugging Tips

- **SSE parsing**: DataExpert proxy returns raw SSE stream, not parsed Messages object. client.py handles this with manual line parsing. If you get `AttributeError: 'str' object has no attribute 'content'`, the proxy response format changed.
- **Langfuse v4 import**: `from langfuse import observe` (NOT `from langfuse.decorators import observe` — that was v3).
- **ccusage timeout**: SSH calls timeout after 30s. If Hetzner is slow or unreachable, the test will fail. This is expected — ccusage is an optional data source.
- **Markdown fences in Claude output**: Claude sometimes wraps JSON in ```json blocks. _parse_json_response strips these before parsing. If parsing still fails, check for nested fences.
- **Empty Forgejo data**: If no open issues exist, triage demo shows "No open issues found." This is correct behavior, not a bug.
