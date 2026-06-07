"""Reusable event payload builders for document parsing UIs and APIs."""

from __future__ import annotations

from typing import Any

from document_parse_agent.models import ParseResult


def file_read_started(filename: str, mime_type: str) -> dict[str, Any]:
    """Build a file-read-started event."""
    return {
        "event": "file_read_started",
        "source": "FileReadAgent",
        "type": "Status",
        "content": f"Reading uploaded file: {filename}",
        "filename": filename,
        "mime_type": mime_type,
    }


def file_read_done(filename: str, mime_type: str, byte_count: int) -> dict[str, Any]:
    """Build a file-read-complete event."""
    return {
        "event": "file_read_done",
        "source": "FileReadAgent",
        "type": "FileInfo",
        "content": f"Read {byte_count} bytes from {filename}.",
        "filename": filename,
        "mime_type": mime_type,
        "byte_count": byte_count,
    }


def parse_started() -> dict[str, Any]:
    """Build a parse-started event."""
    return {
        "event": "parse_started",
        "source": "DocumentParseAgent",
        "type": "Status",
        "content": "Parsing document into Markdown.",
    }


def parse_warning(message: str) -> dict[str, Any]:
    """Build a parse warning event."""
    return {
        "event": "warning",
        "source": "DocumentParseAgent",
        "type": "Warning",
        "content": message,
    }


def parse_done(result: ParseResult) -> dict[str, Any]:
    """Build a parse-complete event."""
    return {
        "event": "parse_done",
        "source": "DocumentParseAgent",
        "type": "ParsedDocument",
        "content": f"Parsed {result.filename} with {result.backend}.",
        "parsed_document": result.to_dict(),
    }


def parse_final(result: ParseResult) -> dict[str, Any]:
    """Build a final parse payload event."""
    return {
        "event": "final",
        "source": "DocumentParseAgent",
        "type": "FinalPayload",
        "content": "Document parsing complete. Awaiting human parse confirmation.",
        "parsed_document": result.to_dict(),
        "awaiting_parse_confirmation": True,
    }


def parse_error(exc: Exception) -> dict[str, Any]:
    """Build a parse error event."""
    return {
        "event": "error",
        "source": "DocumentParseAgent",
        "type": exc.__class__.__name__,
        "content": str(exc),
    }
