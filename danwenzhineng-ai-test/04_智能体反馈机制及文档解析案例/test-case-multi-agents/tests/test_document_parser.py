from __future__ import annotations

import unittest

from openpyxl import Workbook

from document_parse_agent import ParseLimitError, UnsupportedDocumentError
from test_case_multi_agents.document_parser import parse_uploaded_document


class DocumentParserTests(unittest.TestCase):
    def test_markdown_preserves_text(self) -> None:
        parsed = parse_uploaded_document(
            filename="requirements.md",
            mime_type="text/markdown",
            content="# Login\n\nUsers can log in.".encode("utf-8"),
        )

        self.assertEqual(parsed.backend, "local_text")
        self.assertEqual(parsed.parser, "local_text")
        self.assertIn("Users can log in.", parsed.content_markdown)

    def test_csv_renders_markdown_table_with_chinese_content(self) -> None:
        parsed = parse_uploaded_document(
            filename="cases.csv",
            mime_type="text/csv",
            content="功能,规则\n登录,密码不能为空\n".encode("utf-8"),
        )

        self.assertEqual(parsed.backend, "local_csv")
        self.assertIn("| 功能 | 规则 |", parsed.content_markdown)
        self.assertIn("| 登录 | 密码不能为空 |", parsed.content_markdown)

    def test_xlsx_renders_each_sheet(self) -> None:
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Login"
        worksheet.append(["Field", "Rule"])
        worksheet.append(["Email", "Required"])

        from io import BytesIO

        buffer = BytesIO()
        workbook.save(buffer)

        parsed = parse_uploaded_document(
            filename="requirements.xlsx",
            mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            content=buffer.getvalue(),
        )

        self.assertEqual(parsed.backend, "local_xlsx")
        self.assertIn("## Sheet: Login", parsed.content_markdown)
        self.assertIn("| Field | Rule |", parsed.content_markdown)

    def test_unsupported_extension_returns_clear_error(self) -> None:
        with self.assertRaises(UnsupportedDocumentError) as context:
            parse_uploaded_document(
                filename="requirements.json",
                mime_type="application/json",
                content=b"{}",
            )

        self.assertIn("Unsupported file type", str(context.exception))

    def test_oversized_upload_is_rejected(self) -> None:
        with self.assertRaises(ParseLimitError) as context:
            parse_uploaded_document(
                filename="requirements.txt",
                mime_type="text/plain",
                content=b"x" * (21 * 1024 * 1024),
            )

        self.assertIn("too large", str(context.exception))


if __name__ == "__main__":
    unittest.main()
