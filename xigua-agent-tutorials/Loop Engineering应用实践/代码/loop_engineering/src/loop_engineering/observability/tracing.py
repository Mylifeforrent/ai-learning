from __future__ import annotations

import json
from pathlib import Path

from loop_engineering.schemas import LoopRunResult


class LocalTraceStore:
    """Persists compact run traces used by the local hill-climbing demonstration."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def save(self, run: LoopRunResult) -> Path:
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / f"{run.run_id}.json"
        path.write_text(
            json.dumps(run.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return path

    def load(self, run_id: str) -> LoopRunResult:
        path = self.directory / f"{run_id}.json"
        return LoopRunResult.model_validate_json(path.read_text(encoding="utf-8"))

    def list_runs(self, limit: int = 50) -> list[LoopRunResult]:
        if not self.directory.exists():
            return []
        paths = sorted(
            self.directory.glob("*.json"),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )[:limit]
        return [LoopRunResult.model_validate_json(path.read_text(encoding="utf-8")) for path in paths]
