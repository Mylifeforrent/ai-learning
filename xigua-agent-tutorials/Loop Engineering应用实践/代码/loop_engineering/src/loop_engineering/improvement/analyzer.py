from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from uuid import uuid4

from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from loop_engineering.observability.tracing import LocalTraceStore
from loop_engineering.schemas import ImprovementProposal, LoopRunResult


class HarnessAnalysis(BaseModel):
    title: str
    observed_pattern: str
    prompt_additions: list[str] = Field(default_factory=list)
    verifier_changes: list[str] = Field(default_factory=list)
    expected_effect: str
    risks: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    safe_to_auto_apply: bool = False


class HarnessImprovementAnalyzer:
    """Loop 4: analyze run traces and propose a bounded harness improvement."""

    def __init__(
        self,
        trace_store: LocalTraceStore,
        proposal_dir: Path,
        model_name: str | None,
    ) -> None:
        self.trace_store = trace_store
        self.proposal_dir = proposal_dir
        self.model_name = model_name

    def analyze(self, limit: int = 30) -> ImprovementProposal:
        runs = self.trace_store.list_runs(limit=limit)
        if not runs:
            raise ValueError("No local run traces are available for analysis.")

        evidence = self._compact_evidence(runs)
        analysis = self._llm_analysis(evidence) if self.model_name else self._heuristic_analysis(runs)
        proposal = ImprovementProposal(
            proposal_id=str(uuid4()),
            title=analysis.title,
            evidence_run_ids=[run.run_id for run in runs],
            observed_pattern=analysis.observed_pattern,
            prompt_additions=analysis.prompt_additions,
            verifier_changes=analysis.verifier_changes,
            expected_effect=analysis.expected_effect,
            risks=analysis.risks,
            confidence=analysis.confidence,
            safe_to_auto_apply=analysis.safe_to_auto_apply,
        )
        self._save(proposal)
        return proposal

    def _llm_analysis(self, evidence: str) -> HarnessAnalysis:
        model = init_chat_model(self.model_name)
        analyzer = model.with_structured_output(HarnessAnalysis)
        return analyzer.invoke(
            [
                SystemMessage(
                    content=(
                        "You improve an AI agent harness from production-style traces. Identify a "
                        "repeated failure pattern, then propose the smallest prompt or verifier change "
                        "that would prevent it. Do not propose model fine-tuning, broad rewrites, or "
                        "changes unsupported by evidence. Prefer one to three precise prompt rules. "
                        "Set safe_to_auto_apply to false unless the change is purely additive, narrow, "
                        "and cannot expand the agent's permissions."
                    )
                ),
                HumanMessage(content=f"TRACE EVIDENCE:\n{evidence[:45_000]}"),
            ]
        )

    @staticmethod
    def _compact_evidence(runs: list[LoopRunResult]) -> str:
        records: list[dict] = []
        for run in runs:
            attempts = []
            for attempt in run.attempts:
                failed_codes = []
                scope_feedback: list[str] = []
                if attempt.verification:
                    failed_codes = [
                        check.code
                        for check in attempt.verification.deterministic_checks
                        if not check.passed
                    ]
                    if attempt.verification.scope_verdict and not attempt.verification.scope_verdict.passed:
                        scope_feedback = attempt.verification.scope_verdict.feedback
                attempts.append(
                    {
                        "attempt": attempt.attempt,
                        "changed_files": attempt.changed_files,
                        "failed_codes": failed_codes,
                        "scope_feedback": scope_feedback,
                        "agent_summary": attempt.agent_summary[:1_500],
                    }
                )
            records.append(
                {
                    "run_id": run.run_id,
                    "request": run.request.instruction,
                    "status": run.status,
                    "attempts": attempts,
                }
            )
        return json.dumps(records, indent=2, ensure_ascii=False)

    @staticmethod
    def _heuristic_analysis(runs: list[LoopRunResult]) -> HarnessAnalysis:
        counts: Counter[str] = Counter()
        for run in runs:
            for attempt in run.attempts:
                if not attempt.verification:
                    continue
                counts.update(
                    check.code
                    for check in attempt.verification.deterministic_checks
                    if not check.passed
                )
                if attempt.verification.scope_verdict and not attempt.verification.scope_verdict.passed:
                    counts.update(["semantic_scope"])

        most_common = counts.most_common(1)[0][0] if counts else "semantic_scope"
        rules = {
            "changes_present": "Before finishing, confirm that the requested documentation change is visible in the Git diff.",
            "docs_only_scope": "Never modify files outside Markdown or MDX documentation, even for convenience.",
            "git_diff_check": "Before finishing, inspect the diff for trailing whitespace and malformed patch lines.",
            "internal_link_resolves": "For every internal Markdown link you add or edit, resolve it from the source document and confirm the target exists.",
            "no_placeholders": "Do not leave TODO, TBD, or FIXME placeholders in final documentation.",
            "semantic_scope": "Create a requirement checklist from the request and verify every item against the final diff without adding unrelated cleanup.",
        }
        rule = rules.get(most_common, rules["semantic_scope"])
        return HarnessAnalysis(
            title=f"Reduce repeated {most_common} failures",
            observed_pattern=f"The most frequent failed check across recent traces was `{most_common}`.",
            prompt_additions=[rule],
            verifier_changes=[],
            expected_effect="The agent should catch this failure before returning its final answer.",
            risks=["A stricter prompt can make the agent slightly more conservative."],
            confidence=0.65,
            safe_to_auto_apply=False,
        )

    def _save(self, proposal: ImprovementProposal) -> Path:
        self.proposal_dir.mkdir(parents=True, exist_ok=True)
        path = self.proposal_dir / f"{proposal.proposal_id}.json"
        path.write_text(
            json.dumps(proposal.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return path
