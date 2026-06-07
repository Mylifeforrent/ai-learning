"""Exceptions raised by the portable document parsing agent."""

from __future__ import annotations


class DocumentParseError(RuntimeError):
    """Base exception for document parsing failures."""


class UnsupportedDocumentError(DocumentParseError):
    """Raised when no backend supports the uploaded document type."""


class MarkerUnavailableError(DocumentParseError):
    """Raised when Marker parsing is requested but marker-pdf is not installed."""


class ParseLimitError(DocumentParseError):
    """Raised when an input violates configured parse limits."""
