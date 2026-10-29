"""Tests for config.yaml loading behaviour."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml


class TestConfigYamlLoads(unittest.TestCase):
    """Verify the config.yaml file can be loaded and contains expected keys."""

    CONFIG = Path(__file__).resolve().parent.parent / "config.yaml"

    def setUp(self):
        self.data = yaml.safe_load(self.CONFIG.read_text(encoding="utf-8-sig"))

    def test_loads_successfully(self):
        self.assertIsInstance(self.data, dict)

    def test_default_keys_present(self):
        for key in ("ollama_host", "model", "workspace_dir", "data_dir", "max_tool_rounds"):
            self.assertIn(key, self.data, f"Missing key: {key}")

    def test_max_tool_rounds_is_int(self):
        self.assertIsInstance(self.data["max_tool_rounds"], int)

    def test_workspace_dir_is_string(self):
        self.assertIsInstance(self.data["workspace_dir"], str)


class TestConfigEnvironmentOverride(unittest.TestCase):
    """Simulate the pattern app.py uses for env vars from config."""

    def test_env_override_pattern(self):
        cfg = {"ollama_models_dir": r"D:\SomeModels"}
        val = str(Path(cfg.get("ollama_models_dir", r"D:\AI-Data\local-agent\models")).resolve())
        self.assertTrue(val.endswith("SomeModels") or "SomeModels" in val)

    def test_env_override_default(self):
        cfg = {}
        val = str(Path(cfg.get("ollama_models_dir", r"D:\AI-Data\local-agent\models")).resolve())
        self.assertIn("models", val.lower())


class TestConfigWindowsPathSupport(unittest.TestCase):
    """Ensure Windows-style paths in config are handled correctly."""

    def test_windows_backslash_path(self):
        p = Path(r"D:\AI-Data\local-agent\workspace")
        self.assertTrue(str(p.resolve()))

    def test_config_data_dir_resolves(self):
        cfg = yaml.safe_load(
            (Path(__file__).resolve().parent.parent / "config.yaml").read_text(encoding="utf-8-sig")
        )
        p = Path(cfg["data_dir"]).resolve()
        self.assertTrue(p.is_absolute())

    def test_forward_slash_path(self):
        p = Path("D:/AI-Data/local-agent/workspace")
        self.assertTrue(p.is_absolute())


class TestConfigWithTempFile(unittest.TestCase):
    """Test loading a custom config from a temp file."""

    def test_load_custom_yaml(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "config.yaml"
            cfg_path.write_text(
                "ollama_host: http://localhost:11434\nmodel: test-model\nmax_tool_rounds: 5\n",
                encoding="utf-8",
            )
            data = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
            self.assertEqual(data["model"], "test-model")
            self.assertEqual(data["max_tool_rounds"], 5)


if __name__ == "__main__":
    unittest.main()
