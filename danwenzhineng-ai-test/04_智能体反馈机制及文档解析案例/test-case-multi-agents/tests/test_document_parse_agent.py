from __future__ import annotations

import unittest
import os
from io import BytesIO

from openpyxl import Workbook

from document_parse_agent import (
    DocumentParseAgent,
    MarkerUnavailableError,
    ParseOptions,
)
from document_parse_agent.backends.marker import MarkerBackend
from document_parse_agent.events import parse_done, parse_final, parse_warning


class DocumentParseAgentTests(unittest.TestCase):
    def test_parse_text_returns_portable_result(self) -> None:
        result = DocumentParseAgent().parse_text("Users can reset their password from email.")

        self.assertEqual(result.backend, "plain_text")
        self.assertEqual(result.output_format, "markdown")
        self.assertEqual(result.to_dict()["parser"], "plain_text")
        self.assertIn("reset their password", result.content_markdown)

    def test_csv_escapes_pipe_and_keeps_empty_cells(self) -> None:
        result = DocumentParseAgent().parse_bytes(
            filename="rules.csv",
            mime_type="text/csv",
            content="Feature,Rule,Note\nSearch,A|B,\n".encode("utf-8"),
        )

        self.assertIn("| Search | A\\|B |  |", result.content_markdown)

    def test_xlsx_empty_sheet_and_formula_result_metadata(self) -> None:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Rules"
        sheet.append(["Field", "Rule"])
        sheet.append(["Total", 3])
        workbook.create_sheet("Empty")
        buffer = BytesIO()
        workbook.save(buffer)

        result = DocumentParseAgent().parse_bytes(
            filename="rules.xlsx",
            mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            content=buffer.getvalue(),
        )

        self.assertIn("## Sheet: Rules", result.content_markdown)
        self.assertIn("## Sheet: Empty", result.content_markdown)
        self.assertEqual(result.metadata["sheet_count"], 2)

    def test_table_row_limit_emits_structured_warning(self) -> None:
        csv_content = "A,B\n" + "\n".join(f"{index},value" for index in range(5))
        agent = DocumentParseAgent(ParseOptions(max_table_rows=3))

        result = agent.parse_bytes(filename="long.csv", mime_type="text/csv", content=csv_content.encode("utf-8"))

        self.assertEqual(result.warnings[0].code, "row_limit")
        self.assertIn("only the first 3 rows", result.warnings[0].message)
        self.assertIn("warning_details", result.to_dict())

    def test_marker_unavailable_error_is_actionable(self) -> None:
        def missing_marker() -> dict[str, object]:
            raise MarkerUnavailableError("Install it with: pip install -r requirements/marker.txt")

        backend = MarkerBackend(options=ParseOptions(), component_loader=missing_marker)

        with self.assertRaises(MarkerUnavailableError) as context:
            backend.parse_bytes(filename="doc.pdf", mime_type="application/pdf", content=b"%PDF-1.4")

        self.assertIn("requirements/marker.txt", str(context.exception))

    def test_marker_backend_passes_config_to_converter(self) -> None:
        captured: dict[str, object] = {}

        class FakeConfigParser:
            def __init__(self, config: dict[str, object]) -> None:
                captured["config"] = config

            def generate_config_dict(self) -> dict[str, object]:
                return {"generated": True}

            def get_processors(self) -> list[object]:
                return ["processor"]

            def get_renderer(self) -> str:
                return "renderer"

            def get_llm_service(self) -> str:
                return "llm"

        class FakeConverter:
            def __init__(self, **kwargs: object) -> None:
                captured["converter_kwargs"] = kwargs

            def __call__(self, filepath: str) -> dict[str, str]:
                captured["filepath_suffix"] = filepath[-4:]
                return {"rendered": "ok"}

        def fake_text_from_rendered(rendered: object) -> tuple[str, dict[str, object], dict[str, object]]:
            return "# Parsed by Marker", {"rendered": rendered}, {"image.png": "asset"}

        def fake_components() -> dict[str, object]:
            return {
                "ConfigParser": FakeConfigParser,
                "PdfConverter": FakeConverter,
                "create_model_dict": lambda: {"model": "dict"},
                "text_from_rendered": fake_text_from_rendered,
            }

        options = ParseOptions(
            output_format="json",
            use_llm=True,
            llm_provider="deepseek",
            force_ocr=True,
            page_range="0-2",
            openai_api_key="key",
            openai_base_url="https://example.test/v1",
            openai_model="gpt-test",
        )
        result = MarkerBackend(options=options, component_loader=fake_components).parse_bytes(
            filename="doc.pdf",
            mime_type="application/pdf",
            content=b"%PDF-1.4",
        )

        config = captured["config"]
        self.assertIsInstance(config, dict)
        self.assertEqual(config["output_format"], "json")
        self.assertEqual(config["use_llm"], True)
        self.assertEqual(config["force_ocr"], True)
        self.assertEqual(config["page_range"], "0-2")
        self.assertEqual(config["llm_service"], "marker.services.openai.OpenAIService")
        self.assertEqual(config["openai_base_url"], "https://example.test/v1")
        self.assertEqual(config["openai_model"], "gpt-test")
        self.assertEqual(config["openai_api_key"], "key")
        self.assertEqual(result.backend, "marker")
        self.assertIn("Parsed by Marker", result.content_markdown)

    def test_parse_events_are_reusable_payloads(self) -> None:
        result = DocumentParseAgent().parse_text("Users can export reports as CSV files.")

        self.assertEqual(parse_warning("careful")["event"], "warning")
        self.assertEqual(parse_done(result)["parsed_document"]["backend"], "plain_text")
        self.assertTrue(parse_final(result)["awaiting_parse_confirmation"])

    @unittest.skipUnless(os.getenv("RUN_MARKER_INTEGRATION") == "1", "Set RUN_MARKER_INTEGRATION=1 to run Marker.")
    def test_marker_integration_with_synthetic_pdf(self) -> None:
        try:
            from reportlab.pdfgen import canvas
        except ImportError as exc:
            self.skipTest(f"reportlab is not installed: {exc}")

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer)
        pdf.drawString(72, 720, "Login users can authenticate with email and password.")
        pdf.save()

        result = DocumentParseAgent().parse_bytes(
            filename="synthetic.pdf",
            mime_type="application/pdf",
            content=buffer.getvalue(),
        )

        self.assertEqual(result.backend, "marker")
        self.assertIn("email", result.content_markdown.lower())


if __name__ == "__main__":
    unittest.main()
