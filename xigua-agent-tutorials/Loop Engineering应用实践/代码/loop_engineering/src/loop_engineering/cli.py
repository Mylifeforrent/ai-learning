from __future__ import annotations

import json
from pathlib import Path

import typer
import uvicorn
from rich.console import Console
from rich.syntax import Syntax

from loop_engineering.config import HarnessStore, get_settings
from loop_engineering.improvement.analyzer import HarnessImprovementAnalyzer
from loop_engineering.improvement.apply import HarnessProposalApplier
from loop_engineering.observability.tracing import LocalTraceStore
from loop_engineering.repository.git import GitRepository
from loop_engineering.repository.pull_request import LocalPullRequestDraftPublisher
from loop_engineering.schemas import DocsRequest
from loop_engineering.verification.loop import VerificationLoop

app = typer.Typer(no_args_is_help=True, help="Run the four loop-engineering demo.")
console = Console()


@app.command("run")
def run_request(
    instruction: str = typer.Argument(..., help="Documentation change request."),
    workspace: Path | None = typer.Option(None, help="Repository workspace to edit."),
    reset: bool = typer.Option(False, help="Discard existing changes before the run."),
) -> None:
    """Run loops 1 and 2 directly from the command line."""
    settings = get_settings()
    target = (workspace or settings.workspace_path).resolve()
    git = GitRepository(target)
    git.ensure_initialized()
    if reset:
        git.reset_hard()

    loop = VerificationLoop(
        settings=settings,
        workspace=target,
        harness_store=HarnessStore(settings.harness_path),
        trace_store=LocalTraceStore(settings.data_dir / "traces"),
        pr_publisher=LocalPullRequestDraftPublisher(settings.data_dir / "pull_request_drafts"),
        use_llm_judge=settings.use_llm_judge,
    )
    result = loop.run(DocsRequest(instruction=instruction, source="cli"))
    rendered = json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False)
    console.print(Syntax(rendered, "json", word_wrap=True))


@app.command("serve")
def serve(
    host: str = typer.Option("127.0.0.1"),
    port: int = typer.Option(8000),
    reload: bool = typer.Option(False),
) -> None:
    """Run loop 3 as a FastAPI event receiver."""
    uvicorn.run(
        "loop_engineering.events.api:app",
        host=host,
        port=port,
        reload=reload,
    )


@app.command("improve")
def improve(
    limit: int = typer.Option(30, min=1, max=200),
    offline: bool = typer.Option(
        False,
        help="Use failure-frequency heuristics instead of an LLM trace analyzer.",
    ),
) -> None:
    """Analyze traces and write a loop-4 harness improvement proposal."""
    settings = get_settings()
    analyzer = HarnessImprovementAnalyzer(
        trace_store=LocalTraceStore(settings.data_dir / "traces"),
        proposal_dir=settings.data_dir / "harness_proposals",
        model_name=None if offline else settings.improvement_model,
    )
    proposal = analyzer.analyze(limit=limit)
    console.print(
        Syntax(
            json.dumps(proposal.model_dump(mode="json"), indent=2, ensure_ascii=False),
            "json",
            word_wrap=True,
        )
    )
    console.print(
        "[yellow]Proposal generated but not applied. Review it, then use `docs-loop approve`."
    )


@app.command("approve")
def approve(
    proposal: Path = typer.Argument(..., exists=True, dir_okay=False),
    approved_by: str = typer.Option("human-reviewer"),
) -> None:
    """Apply an additive prompt proposal after explicit human review."""
    settings = get_settings()
    applied = HarnessProposalApplier(HarnessStore(settings.harness_path)).apply(
        proposal_path=proposal,
        approved_by=approved_by,
    )
    console.print(f"[green]Applied proposal {applied.proposal_id} to {settings.harness_path}.")


@app.command("traces")
def traces(limit: int = typer.Option(10, min=1, max=100)) -> None:
    """List recent local run traces."""
    settings = get_settings()
    runs = LocalTraceStore(settings.data_dir / "traces").list_runs(limit=limit)
    summary = [
        {
            "run_id": run.run_id,
            "status": run.status,
            "attempts": len(run.attempts),
            "request": run.request.instruction,
        }
        for run in runs
    ]
    console.print(Syntax(json.dumps(summary, indent=2), "json", word_wrap=True))
