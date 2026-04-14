# DevTrack-AI — Design Note

## Architecture Overview

DevTrack-AI follows a data-first pipeline: collect real metrics locally, then use Claude only for natural language generation. No LLM call happens until all data is calculated and validated.

```
Forgejo API --> git_client.py --> raw commits, issues, PRs
                                        |
ccusage (SSH) --> ccusage_client.py ----+---> metrics.py (local math)
                                        |          |
Langfuse API --> langfuse_client.py ----+    calculated metrics
                                                   |
                                        guardrails.py (PII redaction)
                                                   |
                                        claude_skills/*.md (prompts)
                                                   |
                                        client.py --> Claude API
                                                   |
                                        schemas.py (validate output)
                                                   |
                                              structured JSON
```

All math happens in Python. Claude only writes human-readable text from verified numbers. This prevents hallucination — Claude cannot invent metrics because it only sees pre-calculated facts.

## Prompt Strategy

Each feature has a dedicated prompt file in `claude_skills/`. Key design decisions:

1. **Strict JSON schema in every prompt** — Claude sees the exact output structure with field types. No ambiguity, no "use your judgment."

2. **Rubrics over vibes** — severity is not "how bad does it feel" but "critical = data loss, security vulnerability, or production outage." Every classification has a concrete definition.

3. **Closed sets for enums** — severity is `critical|high|medium|low`, not open-ended. Labels come from a fixed taxonomy. This makes output consistent and machine-parseable.

4. **Mandatory source citations** — every claim must cite a specific commit SHA or metric value. If Claude cannot cite evidence, it cannot make the claim. Same pattern used in LuBot's hallucination guard.

5. **Anti-sycophancy rules** — the engineering report prompt explicitly says "do NOT say great job without evidence" and "do NOT soften or hedge." This produces honest coaching.

## Guardrail Strategy

| Guardrail | Layer | When Applied | What It Catches |
|-----------|-------|-------------|----------------|
| PII Redaction | Input + Output | Before/after Claude call | Server IPs, API keys, emails, phones |
| Context Sufficiency | Input | Before Claude call | Empty issues, no commits, missing diffs |
| Schema Validation | Output | After Claude call | Malformed JSON, wrong enum values, missing fields |
| Source Citations | Prompt | During Claude generation | Ungrounded claims, hallucinated metrics |

PII redaction is critical for this project because commit messages contain real server IPs (178.156.214.8), API keys (sk-de-...), and email addresses. Without redaction, this data would leak to the Claude API.

## Error Handling

- **API failures**: 1 retry with exponential backoff, then structured error response
- **JSON parse failures**: Strip markdown code fences first (Claude sometimes wraps JSON in ```). If still invalid, retry once with explicit "respond with ONLY JSON" instruction.
- **Missing data sources**: Each data source (Forgejo, Langfuse, ccusage) returns a structured "not available" result if the API is down. The report generates with whatever data is available.
- **SSH timeout**: ccusage calls have 30-second timeout. If Hetzner is unreachable, that data source is skipped gracefully.

## Token Usage

Measured from Langfuse traces during development:

| Feature | Avg Input Tokens | Avg Output Tokens | Avg Latency |
|---------|-----------------|-------------------|-------------|
| Issue Triage | ~800 | ~300 | 2-3s |
| PR Summary | ~1,200 | ~400 | 3-4s |
| Engineering Report | ~2,500 | ~600 | 8-12s |

The engineering report is the most expensive because it includes commit lists, Langfuse data, and ccusage data in the prompt. Metrics calculation (velocity, work patterns, code health) is free — pure Python math, no tokens burned.

## Known Limitations

1. **PII regex is not exhaustive** — catches common patterns (emails, IPs, API keys) but may miss novel formats. No ML-based NER.
2. **ccusage requires SSH access** — only works when the Hetzner server is reachable from the machine running DevTrack-AI.
3. **Commit message categorization is keyword-based** — "Feature:", "Fix:", "Refactor:" prefixes. Commits without these prefixes go to "other."
4. **No historical trending** — each report is a snapshot of the last N days. Week-over-week comparison requires running the report weekly and comparing outputs manually.
5. **Langfuse free tier limits** — if the project exceeds the hobby plan trace limits, data pull may be incomplete.
6. **No email delivery** — generates the report content but does not send it. Email integration is a future feature.
