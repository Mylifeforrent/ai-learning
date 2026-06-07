"""Compatibility exports for the portable document_parse_agent package."""

from __future__ import annotations

from document_parse_agent import (
    DocumentParseAgent,
    DocumentParseError,
    MarkerUnavailableError,
    ParseLimitError,
    ParseOptions,
    ParseResult,
    UnsupportedDocumentError,
)


ParsedDocument = ParseResult


def parse_uploaded_document(filename: str, mime_type: str, content: bytes) -> ParseResult:
    """Backward-compatible wrapper around DocumentParseAgent.parse_bytes."""
    return DocumentParseAgent().parse_bytes(filename=filename, mime_type=mime_type, content=content)


def create_plain_text_document(content: str, filename: str = "pasted-requirement.md") -> ParseResult:
    """Backward-compatible wrapper around DocumentParseAgent.parse_text."""
    return DocumentParseAgent().parse_text(content=content, filename=filename)


__all__ = [
    "DocumentParseAgent",
    "DocumentParseError",
    "MarkerUnavailableError",
    "ParseLimitError",
    "ParseOptions",
    "ParseResult",
    "ParsedDocument",
    "UnsupportedDocumentError",
    "create_plain_text_document",
    "parse_uploaded_document",
]
