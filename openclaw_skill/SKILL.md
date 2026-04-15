---
name: devtrack
description: "Real-time engineering metrics — commits, velocity, burnout, issues, PRs, LLM usage"
metadata:
  {
    "openclaw": {
      "emoji": "📊",
      "requires": {},
      "always": true
    }
  }
---

# DevTrack-AI — Real-Time Engineering Tracker

You have access to live engineering data via the DevTrack-AI API. Use this skill whenever the user asks about coding activity, commits, velocity, burnout, issues, PRs, or development patterns.

All data is pulled LIVE from real APIs (Forgejo/GitHub, Langfuse, ccusage) — never cached, always fresh.

## How to query

Use curl to hit the DevTrack API:

```bash
curl -s "http://YOUR_SERVER_IP:8099/<endpoint>?<params>"
```

## Available endpoints

| Endpoint | Description |
|---|---|
| `/commits?days=1` | Recent commits (days=1 for today, days=7 for week) |
| `/metrics?days=7` | Velocity, code health, RECR discipline |
| `/work-patterns?days=7` | Late night commits, burnout risk, peak hours |
| `/issues?state=open` | Open issues |
| `/prs?state=all` | Pull requests |
| `/langfuse?days=7` | LLM usage & costs |
| `/ccusage?days=7` | Claude Code dev spending |
| `/repo-stats` | Repository stats |
| `/full-status?days=7` | Everything at once |

## When to use which endpoint

| User asks... | Hit this |
|---|---|
| "What did I do today?" | `/commits?days=1` |
| "What did I ship this week?" | `/commits?days=7` |
| "How's my velocity?" | `/metrics?days=7` |
| "Am I burning out?" | `/work-patterns?days=7` |
| "How's my week going?" | `/full-status?days=7` |
| "Any open issues?" | `/issues?state=open` |
| "How much am I spending on Claude?" | `/ccusage?days=7` |

## How to present results

- Be conversational, not robotic.
- Lead with the most important insight, not raw numbers.
- Flag burnout risk if moderate or high.
- Celebrate wins: high commit count, good RECR discipline, net code reduction.
- Flag concerns: zero test commits, high fix ratio, growing code without tests.
- Keep it brief — 3-5 bullet points max unless asked for detail.

## Interpreting metrics

- **Velocity**: 20+ commits/week = high, 10-19 = medium, <10 = low
- **RECR discipline**: commits_with_tests / total_commits. Above 40% = excellent.
- **Burnout**: >3 late night commits = moderate, >5 = high
- **Code health**: lines_removed > lines_added in refactor weeks = GOOD
- **Fix ratio**: fix_commits > 30% of total = too many bugs getting through
