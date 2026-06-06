"""FastAPI backend for the lightweight test-case generation frontend."""

from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from test_case_multi_agents.main import (
    DEFAULT_MAX_MESSAGES,
    PROJECT_ROOT,
    ConfigurationError,
    generate_review_cycle_for_web,
)


FRONTEND_DIR = PROJECT_ROOT / "frontend"
logger = logging.getLogger(__name__)


class TestCaseRequest(BaseModel):
    """Request body for test-case generation."""

    requirement: str = Field(..., min_length=10)
    max_messages: int = Field(DEFAULT_MAX_MESSAGES, ge=4, le=30)


class RevisionRequest(BaseModel):
    """Request body for revising test cases after human rejection."""

    requirement: str = Field(..., min_length=10)
    previous_test_cases: str = Field(..., min_length=10)
    reviewer_comments: str = Field(..., min_length=1)
    human_feedback: str = Field(..., min_length=3)
    max_messages: int = Field(DEFAULT_MAX_MESSAGES, ge=4, le=30)


app = FastAPI(title="Test Case Multi Agents API")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
async def index() -> FileResponse:
    """Serve the lightweight frontend."""
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
async def health() -> dict[str, str]:
    """Simple health check."""
    return {"status": "ok"}


@app.post("/api/review")
async def create_review(request: TestCaseRequest) -> dict[str, object]:
    """Generate draft test cases and AI review, then wait for human approval."""
    try:
        return await generate_review_cycle_for_web(
            requirements=request.requirement.strip(),
            max_messages=request.max_messages,
        )
    except ConfigurationError as exc:
        logger.exception("Configuration error while generating review.")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error while generating review.")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/revise")
async def revise_test_cases(request: RevisionRequest) -> dict[str, object]:
    """Revise test cases using human rejection feedback."""
    try:
        return await generate_review_cycle_for_web(
            requirements=request.requirement.strip(),
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
