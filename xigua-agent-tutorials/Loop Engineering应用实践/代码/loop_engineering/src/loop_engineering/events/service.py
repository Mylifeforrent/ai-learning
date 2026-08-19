from __future__ import annotations

from pathlib import Path
from threading import Lock

from loop_engineering.config import HarnessStore, Settings
from loop_engineering.events.store import EventRunStore
from loop_engineering.observability.tracing import LocalTraceStore
from loop_engineering.repository.git import GitRepository
from loop_engineering.repository.pull_request import LocalPullRequestDraftPublisher
from loop_engineering.schemas import DocsRequest, EventRunStatus
from loop_engineering.verification.loop import VerificationLoop


class EventProcessingService:
    """Loop 3 worker: turn an external event into an isolated agent run."""

    def __init__(self, settings: Settings, store: EventRunStore) -> None:
        self.settings = settings
        self.store = store
        self._source_lock = Lock()

    def process(self, event_run_id: str, request: DocsRequest) -> None:
        self.store.set_status(event_run_id, EventRunStatus.RUNNING)
        try:
            workspace = self._create_isolated_workspace(event_run_id)
            loop = VerificationLoop(
                settings=self.settings,
                workspace=workspace,
                harness_store=HarnessStore(self.settings.harness_path),
                trace_store=LocalTraceStore(self.settings.data_dir / "traces"),
                pr_publisher=LocalPullRequestDraftPublisher(
                    self.settings.data_dir / "pull_request_drafts"
                ),
            )
            result = loop.run(request)
            status = (
                EventRunStatus.SUCCEEDED
                if result.status == "succeeded"
                else EventRunStatus.FAILED
            )
            self.store.set_status(event_run_id, status, result=result, error=result.error)
        except Exception as exc:
            self.store.set_status(
                event_run_id,
                EventRunStatus.FAILED,
                error=f"{type(exc).__name__}: {exc}",
            )

    def _create_isolated_workspace(self, run_id: str) -> Path:
        source = self.settings.workspace_path.resolve()
        with self._source_lock:
            source_git = GitRepository(source)
            source_git.ensure_initialized()
        destination = self.settings.data_dir / "workspaces" / run_id
        GitRepository.clone_local(source, destination)
        return destination
