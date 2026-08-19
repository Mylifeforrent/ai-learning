from __future__ import annotations

from pathlib import Path

from loop_engineering.schemas import DocsRequest, PullRequestDraft, VerificationReport


class LocalPullRequestDraftPublisher:
    """Creates a reviewable PR artifact without pushing to a real remote repository."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def publish(
        self,
        run_id: str,
        request: DocsRequest,
        changed_files: list[str],
        diff: str,
        report: VerificationReport,
    ) -> PullRequestDraft:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        title = self._title(request.instruction)
        body = (
            "## Request\n\n"
            f"{request.instruction}\n\n"
            "## Changed files\n\n"
            + "\n".join(f"- `{path}`" for path in changed_files)
            + "\n\n## Verification\n\n"
            + report.feedback_text()
            + "\n\n## Diff\n\n```diff\n"
            + diff[:30_000]
            + "\n```\n"
        )
        artifact_path = self.output_dir / f"{run_id}.md"
        artifact_path.write_text(f"# {title}\n\n{body}", encoding="utf-8")
        return PullRequestDraft(title=title, body=body, artifact_path=artifact_path)

    @staticmethod
    def _title(instruction: str) -> str:
        normalized = " ".join(instruction.strip().split())
        if len(normalized) <= 72:
            return normalized
        return normalized[:69].rstrip() + "..."
