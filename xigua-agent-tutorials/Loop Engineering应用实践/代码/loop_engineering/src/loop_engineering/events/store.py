from __future__ import annotations

import json
from pathlib import Path
from threading import Lock

from loop_engineering.schemas import EventRunRecord, EventRunStatus, utc_now


class EventRunStore:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self._lock = Lock()

    def create(self, record: EventRunRecord) -> EventRunRecord:
        self.save(record)
        return record

    def save(self, record: EventRunRecord) -> None:
        with self._lock:
            self.directory.mkdir(parents=True, exist_ok=True)
            record.updated_at = utc_now()
            path = self.directory / f"{record.run_id}.json"
            path.write_text(
                json.dumps(record.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

    def get(self, run_id: str) -> EventRunRecord | None:
        path = self.directory / f"{run_id}.json"
        if not path.exists():
            return None
        return EventRunRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def set_status(
        self,
        run_id: str,
        status: EventRunStatus,
        *,
        result=None,
        error: str | None = None,
    ) -> EventRunRecord:
        record = self.get(run_id)
        if record is None:
            raise KeyError(f"Unknown event run: {run_id}")
        record.status = status
        record.result = result
        record.error = error
        self.save(record)
        return record
