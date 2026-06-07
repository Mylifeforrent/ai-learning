"""FastAPI backend for the lightweight test-case generation frontend."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from document_parse_agent import (
    DocumentParseAgent,
    DocumentParseError,
    ParseResult,
)
from document_parse_agent.events import (
    file_read_done,
    file_read_started,
    parse_done,
    parse_error,
    parse_final,
    parse_started,
    parse_warning,
)
from test_case_multi_agents.main import (
    DEFAULT_MAX_MESSAGES,
    PROJECT_ROOT,
    ConfigurationError,
    generate_review_cycle_for_web,
    stream_review_cycle_for_web,
)


FRONTEND_DIR = PROJECT_ROOT / "frontend"
logger = logging.getLogger(__name__)


class TestCaseRequest(BaseModel):
    """Request body for test-case generation."""

    requirement: str | None = Field(default=None, min_length=10)
    parsed_document_id: str | None = None
    confirmed_content: str | None = Field(default=None, min_length=10)
    parsed_document: dict[str, object] | None = None
    max_messages: int = Field(DEFAULT_MAX_MESSAGES, ge=4, le=30)


class RevisionRequest(BaseModel):
    """Request body for revising test cases after human rejection."""

    requirement: str | None = Field(default=None, min_length=10)
    parsed_document_id: str | None = None
    confirmed_content: str | None = Field(default=None, min_length=10)
    previous_test_cases: str = Field(..., min_length=10)
    reviewer_comments: str = Field(..., min_length=1)
    human_feedback: str = Field(..., min_length=3)
    max_messages: int = Field(DEFAULT_MAX_MESSAGES, ge=4, le=30)


app = FastAPI(title="Test Case Multi Agents API")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


def sse_event(payload: dict[str, object]) -> str:
    """Encode a payload as an SSE frame."""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def parsed_document_from_payload(payload: dict[str, object] | None) -> ParseResult | None:
    """Rebuild a ParseResult from a frontend payload when available."""
    if not payload:
        return None
    try:
        warnings = payload.get("warning_details") or []
        warning_messages = payload.get("warnings") or []
        from document_parse_agent.models import ParseWarning

        parsed_warnings = []
        if isinstance(warnings, list) and warnings:
            parsed_warnings = [
                ParseWarning(
                    message=str(item.get("message", "")),
                    code=str(item.get("code", "warning")),
                    details=dict(item.get("details", {})),
                )
                for item in warnings
                if isinstance(item, dict)
            ]
        elif isinstance(warning_messages, list):
            parsed_warnings = [ParseWarning(message=str(message)) for message in warning_messages]

        return ParseResult(
            document_id=str(payload.get("document_id", "")),
            filename=str(payload.get("filename", "")),
            mime_type=str(payload.get("mime_type", "")),
            backend=str(payload.get("backend") or payload.get("parser", "")),
            output_format=str(payload.get("output_format", "markdown")),
            content_markdown=str(payload.get("content_markdown", "")),
            content_raw=payload.get("content_raw"),
            metadata=dict(payload.get("metadata", {})),
            warnings=parsed_warnings,
            parse_quality_score=payload.get("parse_quality_score"),  # type: ignore[arg-type]
            assets=dict(payload.get("assets", {})),
        )
    except Exception:
        return None


def confirmed_content_from_request(request: TestCaseRequest | RevisionRequest) -> str:
    """Return confirmed parsed content or wrap legacy requirement text."""
    content = request.confirmed_content or request.requirement
    if not content or len(content.strip()) < 10:
        raise HTTPException(status_code=422, detail="confirmed_content is required and must contain at least 10 characters.")
    return content.strip()


async def stream_parse_response(file: UploadFile) -> AsyncGenerator[str, None]:
    """Stream file read and parse events as server-sent events."""
    filename = file.filename or "uploaded-document"
    mime_type = file.content_type or "application/octet-stream"
    try:
        yield sse_event(file_read_started(filename=filename, mime_type=mime_type))
        content = await file.read()
        yield sse_event(file_read_done(filename=filename, mime_type=mime_type, byte_count=len(content)))
        yield sse_event(parse_started())
        parsed = DocumentParseAgent().parse_bytes(filename=filename, mime_type=mime_type, content=content)
        for warning in parsed.warnings:
            yield sse_event(parse_warning(warning.message))
        yield sse_event(parse_done(parsed))
        yield sse_event(parse_final(parsed))
    except DocumentParseError as exc:
        yield sse_event(parse_error(exc))
    except Exception as exc:
        logger.exception("Unexpected document parsing failure.")
        yield sse_event(parse_error(exc))


async def stream_review_response(payload: dict[str, object]) -> AsyncGenerator[str, None]:
    """Stream review-cycle events as server-sent events."""
    try:
        async for event in stream_review_cycle_for_web(**payload):
            yield sse_event(event)
    except ConfigurationError as exc:
        logger.exception("Configuration error while streaming review.")
        yield sse_event({"event": "error", "source": "system", "type": exc.__class__.__name__, "content": str(exc)})
    except Exception as exc:
        logger.exception("Unexpected error while streaming review.")
        yield sse_event({"event": "error", "source": "system", "type": exc.__class__.__name__, "content": str(exc)})


@app.get("/")
async def index() -> FileResponse:
    """Serve the lightweight frontend."""
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
async def health() -> dict[str, str]:
    """Simple health check."""
    return {"status": "ok"}


@app.post("/api/documents/parse/stream")
async def parse_document_stream(file: UploadFile = File(...)) -> StreamingResponse:
    """Read and parse an uploaded document into Markdown."""
    return StreamingResponse(
        stream_parse_response(file),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@app.post("/api/review")
async def create_review(request: TestCaseRequest) -> dict[str, object]:
    """Generate draft test cases and AI review, then wait for human approval."""
    try:
        confirmed_content = confirmed_content_from_request(request)
        parsed_document = parsed_document_from_payload(request.parsed_document)
        if parsed_document is None and request.requirement and not request.confirmed_content:
            parsed_document = DocumentParseAgent().parse_text(request.requirement)
        return await generate_review_cycle_for_web(
            confirmed_content=confirmed_content,
            parsed_document=parsed_document,
            max_messages=request.max_messages,
        )
    except ConfigurationError as exc:
        logger.exception("Configuration error while generating review.")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error while generating review.")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/review/stream")
async def create_review_stream(request: TestCaseRequest) -> StreamingResponse:
    """Stream draft test cases, review, tool calls, and final payload."""
    confirmed_content = confirmed_content_from_request(request)
    parsed_document = parsed_document_from_payload(request.parsed_document)
    if parsed_document is None and request.requirement and not request.confirmed_content:
        parsed_document = DocumentParseAgent().parse_text(request.requirement)
    payload = {
        "confirmed_content": confirmed_content,
        "parsed_document": parsed_document,
        "max_messages": request.max_messages,
    }
    return StreamingResponse(
        stream_review_response(payload),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@app.post("/api/revise")
async def revise_test_cases(request: RevisionRequest) -> dict[str, object]:
    """Revise test cases using human rejection feedback."""
    try:
        confirmed_content = confirmed_content_from_request(request)
        return await generate_review_cycle_for_web(
            confirmed_content=confirmed_content,
            previous_test_cases=request.previous_test_cases.strip(),
            reviewer_comments=request.reviewer_comments.strip(),
            human_feedback=request.human_feedback.strip(),
            max_messages=request.max_messages,
        )
    except ConfigurationError as exc:
        logger.exception("Configuration error while revising test cases.")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error while revising test cases.")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/revise/stream")
async def revise_test_cases_stream(request: RevisionRequest) -> StreamingResponse:
    """Stream revised test cases, review, tool calls, and final payload."""
    confirmed_content = confirmed_content_from_request(request)
    payload = {
        "confirmed_content": confirmed_content,
        "previous_test_cases": request.previous_test_cases.strip(),
        "reviewer_comments": request.reviewer_comments.strip(),
        "human_feedback": request.human_feedback.strip(),
        "max_messages": request.max_messages,
    }
    return StreamingResponse(
        stream_review_response(payload),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@app.post("/api/test-cases")
async def create_test_cases(request: TestCaseRequest) -> dict[str, object]:
    """Backward-compatible alias for /api/review."""
    return await create_review(request)


def parse_args() -> argparse.Namespace:
    """Parse API server command-line arguments."""
    parser = argparse.ArgumentParser(description="Run the test-case multi-agent web API.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    return parser.parse_args()


def cli() -> None:
    """CLI entrypoint for the FastAPI server."""
    import uvicorn

    args = parse_args()
    uvicorn.run(
        "test_case_multi_agents.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    cli()
