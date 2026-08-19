from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


class CheckSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"


class CheckResult(BaseModel):
    code: str
    passed: bool
    message: str
    severity: CheckSeverity = CheckSeverity.ERROR
    path: str | None = None


class ScopeVerdict(BaseModel):
    passed: bool
    score: int = Field(ge=0, le=100)
    rationale: str
    feedback: list[str] = Field(default_factory=list)


class VerificationReport(BaseModel):
    passed: bool
    deterministic_checks: list[CheckResult]
    scope_verdict: ScopeVerdict | None = None

    def feedback_text(self) -> str:
        problems = [check.message for check in self.deterministic_checks if not check.passed]
        if self.scope_verdict and not self.scope_verdict.passed:
            problems.extend(self.scope_verdict.feedback or [self.scope_verdict.rationale])
        if not problems:
            return "Verification passed."
        return "Verification failed:\n" + "\n".join(f"- {item}" for item in problems)


class AgentAttempt(BaseModel):
    attempt: int
    started_at: datetime = Field(default_factory=utc_now)
    finished_at: datetime | None = None
    agent_summary: str = ""
    diff: str = ""
    changed_files: list[str] = Field(default_factory=list)
    verification: VerificationReport | None = None


class DocsRequest(BaseModel):
    instruction: str = Field(min_length=5)
    source: str = "cli"
    event_id: str | None = None
    requested_by: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class PullRequestDraft(BaseModel):
    title: str
    body: str
    artifact_path: Path


class LoopRunResult(BaseModel):
    run_id: str
    request: DocsRequest
    status: str
    workspace: Path
    started_at: datetime = Field(default_factory=utc_now)
    finished_at: datetime | None = None
    attempts: list[AgentAttempt] = Field(default_factory=list)
    final_report: VerificationReport | None = None
    pull_request: PullRequestDraft | None = None
    error: str | None = None


class EventRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class EventRunRecord(BaseModel):
    run_id: str
    status: EventRunStatus
    request: DocsRequest
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    result: LoopRunResult | None = None
    error: str | None = None


class ImprovementProposal(BaseModel):
    proposal_id: str
    created_at: datetime = Field(default_factory=utc_now)
    title: str
    evidence_run_ids: list[str]
    observed_pattern: str
    prompt_additions: list[str] = Field(default_factory=list)
    verifier_changes: list[str] = Field(default_factory=list)
    expected_effect: str
    risks: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    safe_to_auto_apply: bool = False
    status: str = "pending_human_review"
