from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from document_parse_agent import MarkerUnavailableError
from test_case_multi_agents.api import app


class DocumentParseApiTests(unittest.TestCase):
    def test_parse_stream_returns_final_for_markdown(self) -> None:
        client = TestClient(app)
        response = client.post(
            "/api/documents/parse/stream",
            files={"file": ("requirements.md", b"# Login\n\nUsers can log in.", "text/markdown")},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('"event": "file_read_done"', response.text)
        self.assertIn('"event": "parse_done"', response.text)
        self.assertIn('"event": "final"', response.text)
        self.assertIn('"backend": "local_text"', response.text)
        self.assertIn('"parser": "local_text"', response.text)

    def test_parse_stream_returns_clear_marker_error(self) -> None:
        client = TestClient(app)

        def missing_marker() -> dict[str, object]:
            raise MarkerUnavailableError("Install it with: pip install -r requirements/marker.txt")

        with patch("document_parse_agent.backends.marker._load_marker_components", missing_marker):
            response = client.post(
                "/api/documents/parse/stream",
                files={"file": ("contract.pdf", b"%PDF-1.4", "application/pdf")},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn('"event": "error"', response.text)
        self.assertIn("MarkerUnavailableError", response.text)
        self.assertIn("requirements/marker.txt", response.text)


if __name__ == "__main__":
    unittest.main()
