from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from loop_engineering.agent.factory import create_docs_agent
from loop_engineering.agent.runner import DocsAgentRunner
from loop_engineering.config import HarnessStore, Settings
from loop_engineering.observability.tracing import LocalTraceStore
from loop_engineering.repository.git import GitRepository
from loop_engineering.repository.local import LocalDocumentationRepository
from loop_engineering.repository.pull_request import LocalPullRequestDraftPublisher
from loop_engineering.schemas import (
    AgentAttempt,
    DocsRequest,
    LoopRunResult,
    VerificationReport,
    utc_now,
)
from loop_engineering.tools.docs_tools import build_documentation_tools
from loop_engineering.verification.deterministic import DeterministicVerifier
from loop_engineering.verification.llm_judge import LLMScopeJudge


class VerificationLoop:
    """Loop 2: run the agent, grade the diff, and retry with feedback."""

    def __init__(
        self,
        settings: Settings,
        workspace: Path,
        harness_store: HarnessStore,
        trace_store: LocalTraceStore,
        pr_publisher: LocalPullRequestDraftPublisher,
        use_llm_judge: bool | None = None,
    ) -> None:
        self.settings = settings
        self.workspace = workspace.resolve()
        self.harness_store = harness_store
        self.trace_store = trace_store
        self.pr_publisher = pr_publisher
        self.use_llm_judge = settings.use_llm_judge if use_llm_judge is None else use_llm_judge

        harness = harness_store.load()
        self.repository = LocalDocumentationRepository(
            self.workspace,
            allowed_extensions=harness.allowed_extensions,
            protected_paths=harness.protected_paths,
        )
        self.git = GitRepository(self.workspace)
        self.git.ensure_initialized()
        tools = build_documentation_tools(self.repository, self.git)
        self.agent_runner = DocsAgentRunner(create_docs_agent(settings, harness, tools))
        self.deterministic_verifier = DeterministicVerifier(self.repository, self.git)
        self.scope_judge = LLMScopeJudge(settings.grader_model) if self.use_llm_judge else None

    def run(self, request: DocsRequest) -> LoopRunResult:
        run = LoopRunResult(
            run_id=str(uuid4()),
            request=request,
            status="running",
            workspace=self.workspace,
        )
        feedback: str | None = None

        try:
            for attempt_number in range(1, self.settings.max_verification_attempts + 1):
                attempt = AgentAttempt(attempt=attempt_number)
                attempt.agent_summary = self.agent_runner.run(request, feedback)
                attempt.diff = self.git.diff()
                attempt.changed_files = self.git.status_paths()

                deterministic_checks = self.deterministic_verifier.run()
                scope_verdict = None
                if self.scope_judge is not None:
                    scope_verdict = self.scope_judge.grade(
                        request=request,
                        changed_files=attempt.changed_files,
                        diff=attempt.diff,
                    )

                deterministic_passed = all(check.passed for check in deterministic_checks)
                passed = deterministic_passed and (
                    scope_verdict is None or scope_verdict.passed
                )
                attempt.verification = VerificationReport(
                    passed=passed,
                    deterministic_checks=deterministic_checks,
                    scope_verdict=scope_verdict,
                )
                attempt.finished_at = utc_now()
                run.attempts.append(attempt)
                run.final_report = attempt.verification
                self.trace_store.save(run)

                if passed:
                    run.status = "succeeded"
                    run.pull_request = self.pr_publisher.publish(
                        run_id=run.run_id,
                        request=request,
                        changed_files=attempt.changed_files,
                        diff=attempt.diff,
                        report=attempt.verification,
                    )
                    break

                feedback = attempt.verification.feedback_text()
            else:
                run.status = "failed_verification"
        except Exception as exc:
            run.status = "failed"
            run.error = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            run.finished_at = utc_now()
            self.trace_store.save(run)

        return run
