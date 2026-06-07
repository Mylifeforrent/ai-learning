"""Shared models for portable document parsing."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class ParserBackend(str, Enum):
    """Supported parser backend identifiers."""

    PLAIN_TEXT = "plain_text"
    LOCAL_TEXT = "local_text"
    LOCAL_CSV = "local_csv"
    LOCAL_XLSX = "local_xlsx"
    MARKER = "marker"


@dataclass(frozen=True)
class ParseWarning:
    """A non-fatal parse warning."""

    message: str
    code: str = "warning"
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return asdict(self)


@dataclass(frozen=True)
class ParseOptions:
    """Runtime options for a document parsing agent."""

    max_upload_mb: int = 20
    max_table_rows: int = 200
    output_format: str = "markdown"
    use_llm: bool = True
    llm_provider: str = "qianwen"
    force_ocr: bool = False
    page_range: str | None = None
    disable_image_extraction: bool = False
    block_correction_prompt: str | None = None
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str | None = None
    marker_extra_config: dict[str, Any] = field(default_factory=dict)

    @property
    def max_upload_bytes(self) -> int:
        """Return upload size limit in bytes."""
        return self.max_upload_mb * 1024 * 1024


@dataclass(frozen=True)
class ParseInput:
    """Input payload for parsing file bytes."""

    filename: str
    content: bytes
    mime_type: str = ""

    @property
    def suffix(self) -> str:
        """Return the lower-case file suffix."""
        return Path(self.filename).suffix.lower()


@dataclass(frozen=True)
class ParseResult:
    """Normalized parse result for downstream agent workflows."""

    document_id: str
    filename: str
    mime_type: str
    backend: str
    output_format: str
    content_markdown: str
    content_raw: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[ParseWarning] = field(default_factory=list)
    parse_quality_score: float | None = None
    assets: dict[str, Any] = field(default_factory=dict)

    @property
    def parser(self) -> str:
        """Backward-compatible alias used by the current frontend payload."""
        return self.backend

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation with compatibility aliases."""
        payload = asdict(self)
        payload["warnings"] = [warning.message for warning in self.warnings]
        payload["warning_details"] = [warning.to_dict() for warning in self.warnings]
        payload["parser"] = self.backend
        return json_safe(payload)


def json_safe(value: Any) -> Any:
    """Convert common non-JSON values to safe representations."""
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, bytes):
        return f"<bytes:{len(value)}>"
    return str(value)
