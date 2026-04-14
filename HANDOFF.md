# DevTrack-AI — Handoff Document

**Last updated:** April 13, 2026
**Author:** Lubo Bali
**Repo:** github.com/lubobali/DevTrack-AI

## Current Project Status

DevTrack-AI v1.1 is **COMPLETE and deployed to GitHub**. All 4 core features work end-to-end with real data. 43 tests passing. 4 data sources wired. Weekly reports sent via Resend email. NVIDIA Nemotron Ultra 253B for analysis. The tool generates actionable weekly engineering reports from real LuBot development data.

**Milestone: v1.1 — SHIPPED (with email delivery)**

## Completed Tasks

| Task | Status | Tests | Notes |
|------|--------|-------|-------|
| Project infrastructure | DONE | 1 | pyproject.toml, requirements.txt, venv, .env |
| Pydantic schemas (9 models) | DONE | 6 | All inputs + outputs + EngineeringMetrics |
| PII redaction guardrail | DONE | 6 | Email, phone, IP, API key patterns |
| Context sufficiency guardrail | DONE | 4 | Empty issue, no commits, no diffs |
| Forgejo API client | DONE | 4 | Commits, issues, PRs, repo stats from git.lubot.ai |
| Metrics calculator | DONE | 5 | Velocity, code health, work patterns — pure math |
| Claude API client | DONE | 1 | Anthropic proxy + Langfuse @observe |
| 4 claude_skills prompts | DONE | — | Triage, PR summary, digest, engineering report |
| Issue triage feature | DONE | 2 | Severity/priority/labels/owner with citations |
| PR summary feature | DONE | 2 | Technical summary + risk checklist |
| Engineering report feature | DONE | 2 | Weekly self-coaching with 4 data sources |
| Langfuse LuBot Staging pull | DONE | 1 | LLM usage, cost, models, latency |
| ccusage integration | DONE | 1 | Claude Code dev costs per project via SSH |
| Integration tests | DONE | 4 | PII pipeline, context fallback, JSON retry, e2e |
| Sample inputs (3 files) | DONE | — | Real Forgejo data snapshots |
| Sample outputs (3 files) | DONE | — | Real Claude responses |
| README.md | DONE | — | Architecture, setup, usage, folder structure |
| writeup.md | DONE | — | Design note: prompts, guardrails, error handling |
| CLAUDE.md | DONE | — | AI operating context |
| Push to GitHub | DONE | — | github.com/lubobali/DevTrack-AI |

## Pending Tasks (Future v2.0)

| Task | Priority | Effort | Notes |
|------|----------|--------|-------|
| Email delivery (Resend) | HIGH | 2 hours | Send weekly report to agent@lubot.ai automatically |
| Cron scheduler | HIGH | 1 hour | Run report every Sunday night via APScheduler or cron |
| Historical trending | MEDIUM | 4 hours | Save reports to DB, compare week-over-week |
| CI pass/fail tracking | MEDIUM | 2 hours | Pull Forgejo Actions run results |
| Dependency audit | LOW | 1 hour | pip audit integration in metrics |
| Frontend dashboard | LOW | 8 hours | Simple web UI showing weekly trends |
| Multi-repo support | LOW | 3 hours | Track HelloPayments and LuBot from one tool |
| Switch to NVIDIA NIM | FUTURE | 30 min | Change .env when bootcamp tokens expire |

## Open Issues / Risks / Blockers

| Issue | Severity | Status | Mitigation |
|-------|----------|--------|------------|
| Bootcamp tokens expire | MEDIUM | Known | Switch ANTHROPIC_BASE_URL to NVIDIA NIM. Only .env change. |
| ccusage requires SSH | LOW | Accepted | If Hetzner unreachable, data source skipped gracefully |
| No historical data | MEDIUM | Planned | Each run is a snapshot. Need DB for trending. |
| Langfuse hobby tier limits | LOW | Monitor | 491 traces in first day. May hit limits in weeks. |
| PII regex not exhaustive | LOW | Accepted | Covers common patterns. ML-based NER is overkill for now. |

## Decision Log

| Date | Decision | Why |
|------|----------|-----|
| Apr 12, 2026 | Use raw HTTP instead of Anthropic SDK | DataExpert proxy returns SSE stream that SDK doesn't parse |
| Apr 12, 2026 | Separate Langfuse projects for DevTrack vs LuBot | Different concerns — own costs vs app costs. Different keys. |
| Apr 12, 2026 | metrics.py does all math locally | Prevents hallucination. Claude only interprets pre-calculated facts. |
| Apr 12, 2026 | ccusage via SSH, not local | Claude Code runs on Hetzner, logs are there. Must SSH to read. |
| Apr 12, 2026 | No LangChain | Proxy is Anthropic-style. SDK would add unnecessary abstraction. |
| Apr 13, 2026 | One repo for HW1 + HW2 | DevTrack-AI exceeds both homework requirements. Staff DE move. |
| Apr 13, 2026 | Anti-sycophancy in coaching prompt | Engineering reports must be honest. "Don't say great job without evidence." |
| Apr 13, 2026 | Strict JSON schemas in all prompts | Closed enums + required fields = consistent, machine-parseable output. |

## Next 7-Day Execution Plan

| Day | Task | Time |
|-----|------|------|
| Mon Apr 14 | Submit HW1 + HW2 to DataExpert bootcamp | 5 min |
| Tue Apr 15 | Add Resend email delivery to agent@lubot.ai | 2 hrs |
| Wed Apr 16 | Add cron scheduler (Sunday 11 PM weekly run) | 1 hr |
| Thu Apr 17 | Run first real weekly report, review coaching quality | 30 min |
| Fri Apr 18 | Iterate on prompts based on report quality | 1 hr |
| Sat Apr 19 | Add CI pass/fail tracking from Forgejo Actions API | 2 hrs |
| Sun Apr 20 | First automated weekly email arrives | 0 min (automated) |

## Ownership / Contact Map

| Area | Owner | Contact |
|------|-------|---------|
| DevTrack-AI (all) | Lubo Bali | data@lubobali.com |
| LuBot Staging | Lubo Bali | agent@lubot.ai |
| Hetzner Server | Lubo Bali | root@100.115.173.71 (Tailscale) |
| DataExpert Bootcamp | Zach Wilson | dataexpert.io |

## Recovery Steps

**If Claude API stops working:**
1. Check .env — is ANTHROPIC_API_KEY valid?
2. Test manually: `curl` the proxy URL with the key
3. If bootcamp tokens expired: switch to NVIDIA NIM (change ANTHROPIC_BASE_URL)
4. If proxy is down: wait or use direct Anthropic API

**If Forgejo API stops working:**
1. Check `curl https://git.lubot.ai/api/v1/repos/lubo/lubot` with token
2. If 401: regenerate token in Forgejo settings
3. If server down: check Hetzner status, SSH to 100.115.173.71

**If ccusage fails:**
1. SSH to Hetzner: `ssh root@100.115.173.71`
2. Run: `ccusage daily --json | head -5`
3. If not installed: `npm install -g ccusage`
4. If SSH fails: check Tailscale connection

**If Langfuse API fails:**
1. Check us.cloud.langfuse.com dashboard — is the project accessible?
2. Verify keys in .env match the project
3. If hobby tier exceeded: upgrade or wait for reset

**If tests fail after changes:**
1. Run fast tests first: `pytest -k "Schema or PII or Context"`
2. If fast tests pass but API tests fail: check .env keys
3. If ccusage test fails: check SSH connectivity
4. Never weaken a test to make it pass — fix the implementation
