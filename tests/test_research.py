"""Tests for the research module."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from research import _validate_url, _TextParser, _SearchParser


class TestValidateUrlBlocksLocalhost(unittest.TestCase):

    def test_blocks_localhost(self):
        with self.assertRaises(ValueError):
            _validate_url("http://localhost/secret")

    def test_blocks_localhost_with_port(self):
        with self.assertRaises(ValueError):
            _validate_url("http://localhost:8080/api")

    def test_blocks_localhost_localdomain(self):
        with self.assertRaises(ValueError):
            _validate_url("http://localhost.localdomain/test")

    def test_blocks_dotlocal(self):
        with self.assertRaises(ValueError):
            _validate_url("http://myhost.local/test")


class TestValidateUrlBlocksPrivateIPs(unittest.TestCase):

    def test_blocks_127_0_0_1(self):
        with self.assertRaises(ValueError):
            _validate_url("http://127.0.0.1/test")

    def test_blocks_10_network(self):
        with self.assertRaises(ValueError):
            _validate_url("http://10.0.0.1/test")

    def test_blocks_192_168(self):
        with self.assertRaises(ValueError):
            _validate_url("http://192.168.1.1/test")

    def test_blocks_169_254(self):
        with self.assertRaises(ValueError):
            _validate_url("http://169.254.1.1/test")


class TestValidateUrlAllowsValid(unittest.TestCase):

    def test_allows_https(self):
        result = _validate_url("https://www.google.com")
        self.assertEqual(result.scheme, "https")

    def test_allows_http(self):
        result = _validate_url("http://example.com")
        self.assertEqual(result.scheme, "http")

    def test_rejects_ftp(self):
        with self.assertRaises(ValueError):
            _validate_url("ftp://example.com/file")

    def test_rejects_empty(self):
        with self.assertRaises(ValueError):
            _validate_url("")

    def test_rejects_no_scheme(self):
        with self.assertRaises(ValueError):
            _validate_url("just-a-hostname")


class TestTextParser(unittest.TestCase):

    def test_extracts_text(self):
        parser = _TextParser()
        parser.feed("<html><body><p>Hello World</p></body></html>")
        text = " ".join(parser.parts)
        self.assertIn("Hello World", text)

    def test_skips_script_tags(self):
        parser = _TextParser()
        parser.feed("<html><body><script>var x = 1;</script><p>Visible</p></body></html>")
        text = " ".join(parser.parts)
        self.assertIn("Visible", text)
        self.assertNotIn("var x", text)

    def test_skips_style_tags(self):
        parser = _TextParser()
        parser.feed("<html><body><style>.cls{color:red}</style><p>Content</p></body></html>")
        text = " ".join(parser.parts)
        self.assertIn("Content", text)
        self.assertNotIn("color:red", text)

    def test_extracts_title(self):
        parser = _TextParser()
        parser.feed("<html><head><title>My Page</title></head><body></body></html>")
        self.assertEqual(parser.title, "My Page")

    def test_empty_html(self):
        parser = _TextParser()
        parser.feed("")
        self.assertEqual(parser.parts, [])


class TestSearchParser(unittest.TestCase):

    def test_empty_html(self):
        parser = _SearchParser()
        parser.feed("")
        self.assertEqual(parser.results, [])

    def test_parses_result_link(self):
        html = '<a class="result__a" href="https://example.com">Example Title</a>'
        parser = _SearchParser()
        parser.feed(html)
        self.assertEqual(len(parser.results), 1)
        self.assertEqual(parser.results[0]["url"], "https://example.com")
        self.assertEqual(parser.results[0]["title"], "Example Title")

    def test_multiple_results(self):
        html = (
            '<a class="result__a" href="https://a.com">A</a>'
            '<a class="result__a" href="https://b.com">B</a>'
        )
        parser = _SearchParser()
        parser.feed(html)
        self.assertEqual(len(parser.results), 2)


if __name__ == "__main__":
    unittest.main()
