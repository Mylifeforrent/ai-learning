"""Optional Marker backend for complex document parsing."""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path
from typing import Any, Callable

from document_parse_agent.errors import DocumentParseError, MarkerUnavailableError
from document_parse_agent.llm_adapters import resolve_marker_llm_config
from document_parse_agent.models import ParseOptions, ParseResult, ParserBackend


MARKER_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".epub",
    ".html",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".tif",
    ".tiff",
}


def supports_marker_file(filename: str) -> bool:
    """Return whether Marker should be used for this filename."""
    return Path(filename).suffix.lower() in MARKER_EXTENSIONS


class MarkerBackend:
    """Local Marker parser backend.

    The marker-pdf dependency is intentionally optional. Importing Marker is delayed
    until this backend is used so projects can depend on the portable agent without
    paying the PyTorch/model installation cost.
    """

    def __init__(
        self,
        options: ParseOptions,
        component_loader: Callable[[], dict[str, Any]] | None = None,
    ) -> None:
        self.options = options
        self._component_loader = component_loader or _load_marker_components

    def parse_bytes(self, filename: str, mime_type: str, content: bytes) -> ParseResult:
        """Parse complex document bytes through Marker."""
        components = self._component_loader()
        PdfConverter = components["PdfConverter"]
        ConfigParser = components["ConfigParser"]
        create_model_dict = components["create_model_dict"]
        text_from_rendered = components["text_from_rendered"]

        config_parser = ConfigParser(self._marker_config())
        converter = PdfConverter(
            config=config_parser.generate_config_dict(),
            artifact_dict=create_model_dict(),
            processor_list=config_parser.get_processors(),
            renderer=config_parser.get_renderer(),
            llm_service=config_parser.get_llm_service(),
        )

        suffix = Path(filename).suffix or ".pdf"
        with tempfile.NamedTemporaryFile(suffix=suffix) as temp_file:
            temp_file.write(content)
            temp_file.flush()
            rendered = converter(temp_file.name)

        text, raw_payload, images = text_from_rendered(rendered)
        content_markdown = text if isinstance(text, str) else str(text)
        content_raw = raw_payload if raw_payload is not None else rendered

        return ParseResult(
            document_id=str(uuid.uuid4()),
            filename=filename,
            mime_type=mime_type or "application/octet-stream",
            backend=ParserBackend.MARKER.value,
            output_format=self.options.output_format,
            content_markdown=content_markdown,
            content_raw=content_raw,
            metadata={
                "byte_count": len(content),
                "marker_output_format": self.options.output_format,
                "use_llm": self.options.use_llm,
                "force_ocr": self.options.force_ocr,
            },
            assets=images or {},
        )

    def _marker_config(self) -> dict[str, Any]:
        """Build Marker ConfigParser input from portable options."""
        config: dict[str, Any] = {
            "output_format": self.options.output_format,
            "use_llm": self.options.use_llm,
            "force_ocr": self.options.force_ocr,
            "disable_image_extraction": self.options.disable_image_extraction,
            **self.options.marker_extra_config,
        }
        if self.options.page_range:
            config["page_range"] = self.options.page_range
        if self.options.block_correction_prompt:
            config["block_correction_prompt"] = self.options.block_correction_prompt
        if self.options.use_llm:
            llm_config = resolve_marker_llm_config(self.options.llm_provider).to_marker_config()
            config.update(llm_config)
        if self.options.openai_api_key:
            config["openai_api_key"] = self.options.openai_api_key
        if self.options.openai_base_url:
            config["openai_base_url"] = self.options.openai_base_url
        if self.options.openai_model:
            config["openai_model"] = self.options.openai_model
        return {key: value for key, value in config.items() if value is not None}


def _load_marker_components() -> dict[str, Any]:
    """Import Marker components lazily."""
    try:
        from marker.config.parser import ConfigParser
        from marker.converters.pdf import PdfConverter
        from marker.models import create_model_dict
        from marker.output import text_from_rendered
    except ImportError as exc:
        raise MarkerUnavailableError(
            "Marker parsing requires the optional dependency marker-pdf. "
            "Install it in a separate parser environment with: "
            "pip install -r requirements/marker.txt"
        ) from exc
    except Exception as exc:
        raise DocumentParseError(f"Failed to initialize Marker components: {exc}") from exc

    return {
        "ConfigParser": ConfigParser,
        "PdfConverter": PdfConverter,
        "create_model_dict": create_model_dict,
        "text_from_rendered": text_from_rendered,
    }
