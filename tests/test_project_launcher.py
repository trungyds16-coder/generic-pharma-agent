"""Tests for the project_launcher module."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from project_launcher import _default_icon, ensure_project_launcher, write_project_launcher


class TestDefaultIcon(unittest.TestCase):

    def test_returns_bytes(self):
        ico = _default_icon()
        self.assertIsInstance(ico, bytes)

    def test_valid_ico_header(self):
        ico = _default_icon()
        # ICO files start with reserved=0x0000, type=0x0001
        self.assertEqual(ico[0:2], b'\x00\x00')
        self.assertEqual(ico[2:4], b'\x01\x00')

    def test_nonzero_length(self):
        ico = _default_icon()
        self.assertGreater(len(ico), 100)

    def test_icon_count(self):
        """ICO header byte 4-5 should indicate 1 image."""
        ico = _default_icon()
        count = int.from_bytes(ico[4:6], "little")
        self.assertEqual(count, 1)


class TestEnsureProjectLauncher(unittest.TestCase):

    def test_creates_all_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "my_project"
            project.mkdir()
            runner, shortcut, icon = ensure_project_launcher(project)
            self.assertTrue(runner.is_file(), "run_project.bat not created")
            self.assertTrue(shortcut.is_file(), "create_desktop_shortcut.bat not created")
            self.assertTrue(icon.is_file(), "project.ico not created")

    def test_idempotent(self):
        """Calling ensure_project_launcher twice should not overwrite existing files."""
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "my_project"
            project.mkdir()
            ensure_project_launcher(project)
            # Write custom content to runner
            runner = project / "run_project.bat"
            runner.write_text("custom content", encoding="utf-8")
            ensure_project_launcher(project)
            self.assertEqual(runner.read_text(encoding="utf-8"), "custom content")

    def test_creates_icon_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "deep" / "project"
            ensure_project_launcher(project)
            self.assertTrue((project / "assets" / "icons").is_dir())

    def test_returns_resolved_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "proj"
            project.mkdir()
            runner, shortcut, icon = ensure_project_launcher(project)
            self.assertTrue(runner.is_absolute())
            self.assertTrue(shortcut.is_absolute())
            self.assertTrue(icon.is_absolute())


class TestWriteProjectLauncher(unittest.TestCase):

    def test_writes_runner_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "proj"
            project.mkdir()
            runner = write_project_launcher(project, "python main.py")
            self.assertTrue(runner.is_file())
            content = runner.read_text(encoding="utf-8")
            self.assertIn("python main.py", content)

    def test_rejects_empty_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "proj"
            project.mkdir()
            with self.assertRaises(ValueError):
                write_project_launcher(project, "")

    def test_rejects_multiline_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "proj"
            project.mkdir()
            with self.assertRaises(ValueError):
                write_project_launcher(project, "python main.py\npython other.py")

    def test_creates_supporting_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "proj"
            project.mkdir()
            write_project_launcher(project, "python app.py")
            self.assertTrue((project / "create_desktop_shortcut.bat").is_file())
            self.assertTrue((project / "assets" / "icons" / "project.ico").is_file())

    def test_runner_content_has_bat_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "proj"
            project.mkdir()
            runner = write_project_launcher(project, "python app.py")
            content = runner.read_text(encoding="utf-8")
            self.assertIn("@echo off", content)
            self.assertIn("setlocal", content)
            self.assertIn("pause", content)


if __name__ == "__main__":
    unittest.main()
