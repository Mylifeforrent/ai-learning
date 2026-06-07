"""Portable document parsing agent facade."""

from __future__ import annotations

import os
from pathlib import Path

from document_parse_agent.backends.local import parse_local_bytes, parse_text, supports_local_file
from document_parse_agent.backends.marker import MarkerBackend, supports_marker_file
from document_parse_agent.errors import ParseLimitError, UnsupportedDocumentError
from document_parse_agent.models import ParseInput, ParseOptions, ParseResult


class DocumentParseAgent:
    """General-purpose document parsing service.

    This class deliberately has no AutoGen, FastAPI, or app-specific dependency so
    it can be copied into other projects or packaged as a standalone utility.
    """

    def __init__(self, options: ParseOptions | None = None) -> None:
        self.options = options or configured_parse_options()

    def parse_bytes(self, filename: str, content: bytes, mime_type: str = "") -> ParseResult:
        """Parse file bytes into a normalized result."""
        parse_input = ParseInput(filename=filename, content=content, mime_type=mime_type)
        self._ensure_allowed_size(parse_input)

        if supports_local_file(parse_input.filename):
            return parse_local_bytes(
                filename=parse_input.filename,
                mime_type=parse_input.mime_type,
                content=parse_input.content,
                options=self.options,
            )

        if supports_marker_file(parse_input.filename):
            return MarkerBackend(options=self.options).parse_bytes(
                filename=parse_input.filename,
                mime_type=parse_input.mime_type,
                content=parse_input.content,
            )

        raise UnsupportedDocumentError(
            f"Unsupported file type '{parse_input.suffix or 'unknown'}'. "
            f"Supported local types: md, markdown, txt, csv, xlsx. "
            "Supported Marker types require marker-pdf in a separate parser environment: "
            "pdf, docx, pptx, epub, html, images."
        )

    def parse_file(self, path: str | Path, mime_type: str = "") -> ParseResult:
        """Parse a file from disk."""
        resolved_path = Path(path)
        return self.parse_bytes(filename=resolved_path.name, mime_type=mime_type, content=resolved_path.read_bytes())

    def parse_text(self, content: str, filename: str = "pasted-requirement.md") -> ParseResult:
        """Wrap manually supplied text into a normalized parse result."""
        return parse_text(content=content, filename=filename, options=self.options)

    def _ensure_allowed_size(self, parse_input: ParseInput) -> None:
        """Reject oversized files before parsing."""
        if len(parse_input.content) > self.options.max_upload_bytes:
            raise ParseLimitError(
                f"Uploaded file is too large. Maximum allowed size is {self.options.max_upload_mb}MB."
            )


def configured_max_upload_mb() -> int:
    """Read upload limit from env with a stable fallback."""
    raw_value = os.getenv("DOCUMENT_MAX_UPLOAD_MB", "20")
    try:
        return int(raw_value)
    except ValueError:
        return 20


def configured_parse_options() -> ParseOptions:
    """Build parse options from environment variables."""
    return ParseOptions(
        max_upload_mb=configured_max_upload_mb(),
        output_format=os.getenv("MARKER_OUTPUT_FORMAT", "markdown"),
        use_llm=parse_bool(os.getenv("MARKER_USE_LLM"), default=True),
        llm_provider=os.getenv("MARKER_LLM_PROVIDER", "qianwen"),
        force_ocr=parse_bool(os.getenv("MARKER_FORCE_OCR"), default=False),
        page_range=os.getenv("MARKER_PAGE_RANGE") or None,
        disable_image_extraction=parse_bool(os.getenv("MARKER_DISABLE_IMAGE_EXTRACTION"), default=False),
        block_correction_prompt=os.getenv("MARKER_BLOCK_CORRECTION_PROMPT") or None,
        openai_api_key=os.getenv("MARKER_OPENAI_API_KEY") or None,
        openai_base_url=os.getenv("MARKER_OPENAI_BASE_URL") or None,
        openai_model=os.getenv("MARKER_OPENAI_MODEL") or None,
    )


def parse_bool(value: str | None, default: bool = False) -> bool:
    """Parse a common environment boolean string."""
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}
