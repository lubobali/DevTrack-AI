# Documentation Rationale Note

## Why These Documents Exist

CLAUDE.md and HANDOFF.md serve different audiences with different needs:

**CLAUDE.md** is for AI assistants (Claude Code, Copilot, future agents). It answers: "How do I work in this codebase without breaking things?" It includes build commands, folder maps, coding conventions, and explicit do/don't rules. An AI agent reading this file can immediately contribute without asking questions.

**HANDOFF.md** is for humans (new team members, future self, collaborators). It answers: "What is this project, where is it, what works, what doesn't, and what should I do next?" It includes status tables, decision history, recovery playbooks, and a 7-day execution plan.

## Structure Tradeoffs

**CLAUDE.md — breadth over depth.** Every section is short but covers a different concern (build, style, security, pitfalls). AI assistants need to know a little about everything — they can read specific files when they need depth. The do/don't section is the most important part because it prevents common mistakes without requiring the AI to understand the full architecture.

**HANDOFF.md — status over architecture.** A new developer doesn't need to understand every function — they need to know what works, what's broken, and what to do next. The decision log is critical because it explains WHY choices were made, not just what was chosen. Without this, the next person would re-evaluate decisions that were already settled.

## What I Would Change

If this project grew to a team of 5+, I would split CLAUDE.md into per-directory files (devtrack_ai/CLAUDE.md, claude_skills/CLAUDE.md) so each area has focused instructions. The root CLAUDE.md would become a pointer file.

For HANDOFF.md, I would move the decision log to a separate DECISIONS.md file and add a RUNBOOK.md for the recovery steps. At scale, one document becomes too long to scan.

For a solo project like this, single files are simpler and sufficient.
