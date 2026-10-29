"""Tests for the tools module."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools import _normalize_python_source, _schema, WorkspaceTools


class TestNormalizePythonSource(unittest.TestCase):

    def test_removes_markdown_fences(self):
        raw = '```python\nprint("hello")\n```'
        content, notes = _normalize_python_source(Path("test.py"), raw)
        self.assertNotIn("```", content)
        self.assertIn("print", content)
        self.assertTrue(any("fences" in n.lower() or "Markdown" in n for n in notes))

    def test_no_change_for_non_py(self):
        raw = '```python\nprint("hello")\n```'
        content, notes = _normalize_python_source(Path("test.txt"), raw)
        self.assertEqual(content, raw)
        self.assertEqual(notes, [])

    def test_escaped_newlines_converted(self):
        raw = r'import os\ndef hello():\n    print("hi")'
        content, notes = _normalize_python_source(Path("test.py"), raw)
        self.assertIn("\n", content)
        self.assertTrue(any("newline" in n.lower() or "line break" in n.lower() for n in notes))

    def test_repairs_markdown_name_guard(self):
        raw = 'if **name** == "**main**":\n    pass\n'
        content, notes = _normalize_python_source(Path("test.py"), raw)
        self.assertIn('__name__', content)
        self.assertIn('__main__', content)

    def test_clean_source_unchanged(self):
        raw = 'print("hello")\n'
        content, notes = _normalize_python_source(Path("test.py"), raw)
        self.assertEqual(content, raw)
        self.assertEqual(notes, [])


class TestSchema(unittest.TestCase):

    def test_basic_schema_structure(self):
        s = _schema("test_tool", "A test tool", {"arg1": {"type": "string"}}, ["arg1"])
        self.assertEqual(s["type"], "function")
        self.assertEqual(s["function"]["name"], "test_tool")
        self.assertEqual(s["function"]["description"], "A test tool")
        self.assertIn("arg1", s["function"]["parameters"]["properties"])
        self.assertEqual(s["function"]["parameters"]["required"], ["arg1"])

    def test_schema_without_required(self):
        s = _schema("t", "desc", {"a": {"type": "string"}})
        self.assertNotIn("required", s["function"]["parameters"])


class TestWorkspaceToolsInit(unittest.TestCase):

    def test_creates_root_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            tools = WorkspaceTools(root)
            self.assertTrue(root.exists())
            self.assertTrue(root.is_dir())

    def test_root_is_resolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            tools = WorkspaceTools(root)
            self.assertEqual(tools.root, root.resolve())

    def test_chat_id_sanitized(self):
        with tempfile.TemporaryDirectory() as tmp:
            tools = WorkspaceTools(Path(tmp), chat_id="abc/../../etc")
            # Only alphanumeric, hyphens, underscores should remain
            self.assertNotIn("/", tools.chat_id)
            self.assertNotIn(".", tools.chat_id)


class TestSafePathValidation(unittest.TestCase):

    def test_allows_path_inside_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            tools = WorkspaceTools(Path(tmp))
            p = tools._safe("hello.py")
            self.assertTrue(str(p).startswith(str(tools.root)))

    def test_rejects_path_outside_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            tools = WorkspaceTools(Path(tmp))
            with self.assertRaises(ValueError):
                tools._safe(r"C:\Windows\system32\notepad.exe")

    def test_allows_editable_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            ext = Path(tmp) / "external.txt"
            ext.write_text("x", encoding="utf-8")
            tools = WorkspaceTools(Path(tmp) / "project", editable_file=ext)
            p = tools._safe(str(ext), allow_editable_file=True)
            self.assertEqual(p, ext.resolve())


class TestListDir(unittest.TestCase):

    def test_list_dir_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            subdir = Path(tmp) / "project"
            subdir.mkdir()
            tools = WorkspaceTools(subdir)
            result = tools.list_dir(".")
            self.assertEqual(result, "(empty)")

    def test_list_dir_with_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            root.mkdir()
            (root / "hello.py").write_text("pass", encoding="utf-8")
            (root / "readme.md").write_text("# Hi", encoding="utf-8")
            tools = WorkspaceTools(root)
            result = tools.list_dir(".")
            self.assertIn("hello.py", result)
            self.assertIn("readme.md", result)

    def test_list_dir_not_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            tools = WorkspaceTools(Path(tmp))
            result = tools.list_dir("nonexistent")
            self.assertIn("Not found", result)


class TestWriteAndReadFile(unittest.TestCase):

    def test_write_and_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            root.mkdir()
            tools = WorkspaceTools(root)
            write_result = tools.write_file("test.txt", "Hello World")
            self.assertIn("Wrote", write_result)
            read_result = tools.read_file("test.txt")
            self.assertEqual(read_result, "Hello World")

    def test_write_python_checks_syntax(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            root.mkdir()
            tools = WorkspaceTools(root)
            result = tools.write_file("good.py", "print('hello')\n")
            self.assertIn("hợp lệ", result)

    def test_write_python_reports_syntax_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            root.mkdir()
            tools = WorkspaceTools(root)
            result = tools.write_file("bad.py", "def broken(\n")
            self.assertIn("lỗi", result)

    def test_write_creates_subdirectories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            root.mkdir()
            tools = WorkspaceTools(root)
            tools.write_file("sub/dir/file.txt", "nested")
            self.assertTrue((root / "sub" / "dir" / "file.txt").is_file())


class TestDispatch(unittest.TestCase):

    def test_unknown_tool(self):
        with tempfile.TemporaryDirectory() as tmp:
            tools = WorkspaceTools(Path(tmp))
            result = tools.dispatch("nonexistent_tool", {})
            self.assertIn("Unknown tool", result)

    def test_dispatch_list_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            root.mkdir()
            (root / "a.txt").write_text("x", encoding="utf-8")
            tools = WorkspaceTools(root)
            result = tools.dispatch("list_dir", {"path": "."})
            self.assertIn("a.txt", result)

    def test_dispatch_catches_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            tools = WorkspaceTools(Path(tmp))
            result = tools.dispatch("read_file", {"path": r"C:\Windows\system32\config"})
            self.assertTrue(result.startswith("Error:"))


if __name__ == "__main__":
    unittest.main()
