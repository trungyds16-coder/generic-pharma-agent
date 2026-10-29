"""Tests for the agent module (pure functions only, no Ollama calls)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# agent imports LIVE from monitor; keep the original instance intact
import monitor
_orig_live = monitor.LIVE


from agent import (
    _classify_request,
    _tool_args,
    _parse_text_tools,
    _norm_path,
    _looks_like_asking,
    _looks_unexecuted,
    _clip,
    _with_footer,
    MAX_TOOL_RESULT_CHARS,
)


class TestClassifyRequest(unittest.TestCase):

    def test_code_request(self):
        modes = _classify_request("viết chương trình python tính BMI")
        self.assertIn("code/project", modes)

    def test_web_research_request(self):
        modes = _classify_request("tìm kiếm trên web về pubchem aspirin")
        self.assertIn("web research", modes)

    def test_document_request(self):
        modes = _classify_request("tạo báo cáo HTML tổng quan")
        self.assertIn("document/report", modes)

    def test_pdf_conversion(self):
        modes = _classify_request("chuyển pdf sang html")
        self.assertIn("PDF conversion", modes)

    def test_chat_fallback(self):
        modes = _classify_request("xin chào")
        self.assertEqual(modes, ["chat/help"])

    def test_empty_input(self):
        modes = _classify_request("")
        self.assertEqual(modes, ["chat/help"])

    def test_multi_mode(self):
        modes = _classify_request("viết code python và tìm kiếm web")
        self.assertIn("code/project", modes)
        self.assertIn("web research", modes)


class TestToolArgs(unittest.TestCase):

    def test_dict_input(self):
        from types import SimpleNamespace
        tc = SimpleNamespace(function=SimpleNamespace(arguments={"path": "test.py"}))
        result = _tool_args(tc)
        self.assertEqual(result, {"path": "test.py"})

    def test_json_string_input(self):
        from types import SimpleNamespace
        tc = SimpleNamespace(function=SimpleNamespace(arguments='{"path": "test.py"}'))
        result = _tool_args(tc)
        self.assertEqual(result, {"path": "test.py"})

    def test_empty_string(self):
        from types import SimpleNamespace
        tc = SimpleNamespace(function=SimpleNamespace(arguments=""))
        result = _tool_args(tc)
        self.assertEqual(result, {})

    def test_invalid_json(self):
        from types import SimpleNamespace
        tc = SimpleNamespace(function=SimpleNamespace(arguments="not json"))
        result = _tool_args(tc)
        self.assertEqual(result, {})

    def test_none_input(self):
        from types import SimpleNamespace
        tc = SimpleNamespace(function=SimpleNamespace(arguments=None))
        result = _tool_args(tc)
        self.assertEqual(result, {})


class TestParseTextTools(unittest.TestCase):

    def test_empty_content(self):
        self.assertEqual(_parse_text_tools(""), [])

    def test_none_content(self):
        self.assertEqual(_parse_text_tools(None), [])

    def test_valid_tool_call(self):
        content = '{"name": "list_dir", "arguments": {"path": "."}}'
        result = _parse_text_tools(content)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "list_dir")
        self.assertEqual(result[0][1], {"path": "."})

    def test_unknown_tool_ignored(self):
        content = '{"name": "hack_the_planet", "arguments": {}}'
        result = _parse_text_tools(content)
        self.assertEqual(len(result), 0)

    def test_multiple_tools(self):
        content = (
            'I will: {"name": "read_file", "arguments": {"path": "a.py"}} '
            'and {"name": "write_file", "arguments": {"path": "b.py", "content": "pass"}}'
        )
        result = _parse_text_tools(content)
        self.assertEqual(len(result), 2)

    def test_no_arguments_key_ignored(self):
        content = '{"name": "list_dir"}'
        result = _parse_text_tools(content)
        self.assertEqual(len(result), 0)


class TestNormPath(unittest.TestCase):

    def test_backslash_to_forward(self):
        self.assertEqual(_norm_path(r"src\main.py"), "src/main.py")

    def test_strips_quotes(self):
        self.assertEqual(_norm_path('"test.py"'), "test.py")

    def test_strips_python_prefix(self):
        self.assertEqual(_norm_path("python test.py"), "test.py")
        self.assertEqual(_norm_path("python.exe test.py"), "test.py")
        self.assertEqual(_norm_path("py test.py"), "test.py")

    def test_empty_input(self):
        self.assertEqual(_norm_path(""), "")

    def test_none_input(self):
        self.assertEqual(_norm_path(None), "")


class TestLooksLikeAsking(unittest.TestCase):

    def test_question_mark(self):
        self.assertTrue(_looks_like_asking("Bạn muốn tôi làm gì?"))

    def test_asking_phrase_vi(self):
        self.assertTrue(_looks_like_asking("Bạn có muốn tiếp tục"))

    def test_asking_phrase_en(self):
        self.assertTrue(_looks_like_asking("Would you like me to continue?"))

    def test_empty_string(self):
        self.assertFalse(_looks_like_asking(""))

    def test_none_input(self):
        self.assertFalse(_looks_like_asking(None))

    def test_normal_statement(self):
        self.assertFalse(_looks_like_asking("Tôi đã hoàn thành xong"))


class TestLooksUnexecuted(unittest.TestCase):

    def test_code_fences(self):
        self.assertTrue(_looks_unexecuted("```python\nprint('hi')\n```"))

    def test_tool_call_json(self):
        self.assertTrue(_looks_unexecuted('Here is: "name": "write_file"'))

    def test_plain_text(self):
        self.assertFalse(_looks_unexecuted("Đã hoàn thành"))

    def test_empty(self):
        self.assertFalse(_looks_unexecuted(""))

    def test_none(self):
        self.assertFalse(_looks_unexecuted(None))


class TestClip(unittest.TestCase):

    def test_short_text_unchanged(self):
        self.assertEqual(_clip("hello"), "hello")

    def test_long_text_clipped(self):
        long_text = "x" * (MAX_TOOL_RESULT_CHARS + 100)
        result = _clip(long_text)
        self.assertIn("...[đã cắt bớt]", result)
        self.assertTrue(len(result) < len(long_text))

    def test_exact_limit_unchanged(self):
        exact = "x" * MAX_TOOL_RESULT_CHARS
        self.assertEqual(_clip(exact), exact)

    def test_non_string_input(self):
        result = _clip(12345)
        self.assertEqual(result, "12345")


class TestWithFooter(unittest.TestCase):

    def test_no_actions(self):
        result = _with_footer("Done", [])
        self.assertEqual(result, "Done")

    def test_with_actions(self):
        result = _with_footer("Result", ["step 1", "step 2"])
        self.assertIn("---", result)
        self.assertIn("Đã thực hiện", result)
        self.assertIn("- step 1", result)
        self.assertIn("- step 2", result)

    def test_empty_text_with_actions(self):
        result = _with_footer("", ["action"])
        self.assertIn("Đã xong các thao tác sau", result)
        self.assertIn("- action", result)

    def test_none_text_with_actions(self):
        result = _with_footer(None, ["action"])
        self.assertIn("Đã xong các thao tác sau", result)


if __name__ == "__main__":
    unittest.main()
