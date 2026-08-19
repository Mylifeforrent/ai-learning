from __future__ import annotations

from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException, status

from loop_engineering.config import get_settings
from loop_engineering.events.service import EventProcessingService
from loop_engineering.events.store import EventRunStore
from loop_engineering.schemas import DocsRequest, EventRunRecord, EventRunStatus

settings = get_settings()
store = EventRunStore(settings.data_dir / "events")
service = EventProcessingService(settings, store)

app = FastAPI(
    title="Loop Engineering Docs Agent",
    version="0.1.0",
    description="Local event-driven implementation of the four loop-engineering levels.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/events/docs-request",
    response_model=EventRunRecord,
    status_code=status.HTTP_202_ACCEPTED,
)
def receive_docs_request(
    request: DocsRequest,
    background_tasks: BackgroundTasks,
) -> EventRunRecord:
    event_run_id = str(uuid4())
    record = EventRunRecord(
        run_id=event_run_id,
        status=EventRunStatus.QUEUED,
        request=request,
    )
    store.create(record)
    background_tasks.add_task(service.process, event_run_id, request)
    return record


@app.get("/runs/{run_id}", response_model=EventRunRecord)
def get_run(run_id: str) -> EventRunRecord:
    record = store.get(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return record
