"""Tests for the monitor module."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from monitor import _Live, render_markdown, latest_code


class TestLiveInit(unittest.TestCase):

    def test_initial_state(self):
        live = _Live()
        self.assertFalse(live.running)
        self.assertEqual(live.model, "")
        self.assertEqual(live.round, 0)
        self.assertEqual(live.phase, "Rảnh")
        self.assertEqual(live.tokens, 0)
        self.assertIsInstance(live.writes, list)
        self.assertEqual(len(live.writes), 0)


class TestLiveStartFinish(unittest.TestCase):

    def test_start_sets_running(self):
        live = _Live()
        live.start("test-model", 5)
        self.assertTrue(live.running)
        self.assertEqual(live.model, "test-model")
        self.assertEqual(live.max_rounds, 5)
        self.assertGreater(live.started, 0)

    def test_finish_clears_running(self):
        live = _Live()
        live.start("test-model", 5)
        live.finish({"rounds": 1, "output_tokens": 100})
        self.assertFalse(live.running)
        self.assertEqual(live.phase, "Xong")
        self.assertEqual(live.last_usage, {"rounds": 1, "output_tokens": 100})

    def test_finish_without_usage(self):
        live = _Live()
        live.start("test-model", 3)
        live.finish(None)
        self.assertFalse(live.running)
        self.assertEqual(live.last_usage, {})

    def test_reset_after_cycle(self):
        live = _Live()
        live.start("m", 3)
        live.begin_round(1)
        live.stream_update("some text", 10)
        live.finish({"rounds": 1})
        live.reset()
        self.assertFalse(live.running)
        self.assertEqual(live.tokens, 0)
        self.assertEqual(live.model, "")


class TestLiveRecordWrite(unittest.TestCase):

    def test_record_write_stores_item(self):
        live = _Live()
        live.record_write("/project/test.py", "print('hi')")
        self.assertEqual(len(live.writes), 1)
        self.assertEqual(live.writes[0]["path"], "/project/test.py")
        self.assertEqual(live.writes[0]["content"], "print('hi')")
        self.assertEqual(live.code_path, "/project/test.py")
        self.assertEqual(live.code_language, ".py")

    def test_record_write_limits_history(self):
        live = _Live()
        for i in range(20):
            live.record_write(f"/project/file{i}.py", f"# file {i}")
        self.assertLessEqual(len(live.writes), 8)

    def test_latest_write(self):
        live = _Live()
        live.record_write("/a.py", "a")
        live.record_write("/b.py", "b")
        w = live.latest_write()
        self.assertEqual(w["path"], "/b.py")

    def test_latest_write_empty(self):
        live = _Live()
        self.assertIsNone(live.latest_write())


class TestLiveStreamCode(unittest.TestCase):

    def test_stream_code_updates_preview(self):
        live = _Live()
        live.stream_code("test.py", "import os\nprint('hi')")
        self.assertEqual(live.code_path, "test.py")
        self.assertEqual(live.code_preview, "import os\nprint('hi')")
        self.assertEqual(live.code_language, ".py")

    def test_stream_code_keeps_previous_path(self):
        live = _Live()
        live.stream_code("first.py", "a")
        live.stream_code("", "b")  # Empty path should keep previous
        self.assertEqual(live.code_path, "first.py")

    def test_stream_code_html(self):
        live = _Live()
        live.stream_code("page.html", "<h1>Hi</h1>")
        self.assertEqual(live.code_language, ".html")


class TestRenderMarkdown(unittest.TestCase):

    def test_returns_string(self):
        result = render_markdown()
        self.assertIsInstance(result, str)

    def test_contains_header(self):
        result = render_markdown()
        self.assertIn("Giám sát", result)


class TestLatestCode(unittest.TestCase):

    def test_returns_tuple_of_three(self):
        result = latest_code()
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)

    def test_label_shown_code_language(self):
        label, code, lang = latest_code()
        self.assertIsInstance(label, str)
        self.assertIsInstance(code, str)
        self.assertIsInstance(lang, str)


if __name__ == "__main__":
    unittest.main()
