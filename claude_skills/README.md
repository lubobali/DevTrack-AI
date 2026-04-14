# Claude Skills

Prompt files used by DevTrack-AI to generate structured output from Claude.

Each skill is a system prompt loaded at runtime by `solution.py`. They define exact JSON schemas, rubrics, and rules that prevent hallucination and ensure consistent output.

## Skills

| Skill | Purpose | Output |
|-------|---------|--------|
| `issue_triage.md` | Triage GitHub issues by severity, priority, labels | Structured triage assessment |
| `pr_summary.md` | Summarize PRs with risk checklist | Technical summary + risks |
| `commit_digest_email.md` | Weekly commit digest grouped by theme | Stakeholder email sections |
| `engineering_report.md` | AI coaching based on engineering metrics | Self-improvement report |

## Design Principles

- **Closed sets over open-ended**: Severity is `critical|high|medium|low`, not "use your judgment"
- **Rubrics over vibes**: "3+ commits after midnight = burnout moderate" is data, not opinion
- **Citations required**: Every claim must reference a commit SHA or metric
- **Anti-hallucination**: Claude only comments on data it received, never invents
