"""Tests for the documents module."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from documents import create_html_report, read_document, fill_html_template


class TestCreateHtmlReport(unittest.TestCase):

    def test_creates_report_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "report.html"
            sections = json.dumps({"Giới thiệu": "Đây là nội dung giới thiệu.", "Chi tiết": ["mục 1", "mục 2"]})
            result = create_html_report(str(out), "Test Report", sections)
            self.assertTrue(out.is_file())
            self.assertIn("report", result.lower() if result else "")

    def test_report_contains_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "report.html"
            sections = json.dumps({"Section": "Content"})
            create_html_report(str(out), "My Title", sections)
            html = out.read_text(encoding="utf-8")
            self.assertIn("My Title", html)

    def test_report_contains_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "report.html"
            sections = json.dumps({"Overview": "Some overview text"})
            create_html_report(str(out), "Title", sections)
            html = out.read_text(encoding="utf-8")
            self.assertIn("Overview", html)
            self.assertIn("Some overview text", html)

    def test_report_with_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "report.html"
            sections = json.dumps({"Intro": "text"})
            sources = json.dumps([{"url": "https://example.com", "title": "Example"}])
            create_html_report(str(out), "Title", sections, sources)
            html = out.read_text(encoding="utf-8")
            self.assertIn("https://example.com", html)

    def test_invalid_sections_json_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "report.html"
            with self.assertRaises(ValueError):
                create_html_report(str(out), "Title", "not valid json!!!")

    def test_sections_must_be_dict(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "report.html"
            with self.assertRaises(ValueError):
                create_html_report(str(out), "Title", '["a list"]')


class TestReadDocument(unittest.TestCase):

    def test_read_text_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "doc.txt"
            f.write_text("Hello document content", encoding="utf-8")
            result = read_document(str(f))
            self.assertIn("Hello document content", result)
            self.assertIn("Tài liệu:", result)

    def test_read_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            read_document("/nonexistent/file.txt")

    def test_read_truncates_long_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "long.txt"
            f.write_text("x" * 50000, encoding="utf-8")
            result = read_document(str(f), max_chars=100)
            self.assertIn("đã rút gọn", result)


class TestFillHtmlTemplate(unittest.TestCase):

    def test_invalid_template_raises(self):
        """fill_html_template should raise if template has no matching placeholders."""
        with tempfile.TemporaryDirectory() as tmp:
            template = Path(tmp) / "template.html"
            template.write_text("<html><body>No placeholders here</body></html>", encoding="utf-8")
            output = Path(tmp) / "output.html"
            with self.assertRaises(ValueError):
                fill_html_template(str(template), str(output), '{"key": "value"}')

    def test_missing_template_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                fill_html_template(str(Path(tmp) / "no.html"), str(Path(tmp) / "out.html"), '{}')

    def test_successful_fill(self):
        with tempfile.TemporaryDirectory() as tmp:
            template = Path(tmp) / "template.html"
            template.write_text("<html><body>{{name}}</body></html>", encoding="utf-8")
            output = Path(tmp) / "output.html"
            result = fill_html_template(str(template), str(output), '{"name": "Test"}')
            self.assertTrue(output.is_file())
            html = output.read_text(encoding="utf-8")
            self.assertIn("Test", html)
            self.assertNotIn("{{name}}", html)


if __name__ == "__main__":
    unittest.main()
