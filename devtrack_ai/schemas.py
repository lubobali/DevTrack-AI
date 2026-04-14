"""Pydantic v2 models for all DevTrack-AI inputs and outputs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, field_validator


# === Input Models ===


class IssueTriageInput(BaseModel):
    title: str
    body: str
    comments: list[str] = []

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title cannot be empty")
        return v


class PRSummaryInput(BaseModel):
    title: str
    description: str
    diff_snippets: list[str]


class CommitEntry(BaseModel):
    sha: str
    message: str
    author: str
    date: str
    files_changed: list[str] = []


class CommitDigestInput(BaseModel):
    commits: list[CommitEntry]
    date_range_start: str
    date_range_end: str


# === Output Models ===


class RiskItem(BaseModel):
    risk: str
    severity: Literal["high", "medium", "low"]
    mitigation: str


class IssueTriageOutput(BaseModel):
    severity: Literal["critical", "high", "medium", "low"]
    priority: Literal["P0", "P1", "P2", "P3"]
    labels: list[str]
    recommended_owner: str
    reasoning: str
    confidence: Literal["high", "medium", "low"]
    source_citations: list[str]


class PRSummaryOutput(BaseModel):
    summary: str
    risk_checklist: list[RiskItem]
    files_affected: list[str]
    source_citations: list[str]


class CommitDigestEmail(BaseModel):
    subject: str
    what_changed: list[str]
    risk_impact: list[str]
    action_needed: list[str]
    source_citations: list[str]


# === Engineering Metrics ===


class EngineeringMetrics(BaseModel):
    commits_this_week: int = 0
    lines_added: int = 0
    lines_removed: int = 0
    test_count: int = 0
    files_touched: int = 0
    late_night_commits: int = 0
    ci_pass_rate: float = 0.0
    largest_file_lines: int = 0
    largest_file_name: str = ""
    refactor_commits: int = 0
    fix_commits: int = 0
    feature_commits: int = 0
    test_commits: int = 0
    deps_count: int = 0
    backup_forgejo_ok: bool = True
    backup_github_ok: bool = True
    backup_b2_ok: bool = True
