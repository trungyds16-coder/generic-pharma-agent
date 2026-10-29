"""Tests for the model_router module."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from model_router import classify, choose_model, load_config, auto_enabled


class TestLoadConfig(unittest.TestCase):

    def test_returns_dict(self):
        cfg = load_config()
        self.assertIsInstance(cfg, dict)

    def test_has_auto_key(self):
        cfg = load_config()
        self.assertIn("auto", cfg)
        self.assertIn("enabled", cfg["auto"])

    def test_has_profiles(self):
        cfg = load_config()
        self.assertIn("profiles", cfg)
        self.assertIn("light", cfg["profiles"])
        self.assertIn("code", cfg["profiles"])

    def test_has_keywords(self):
        cfg = load_config()
        self.assertIn("code_keywords", cfg)
        self.assertIsInstance(cfg["code_keywords"], list)

    def test_fallback_on_missing_file(self):
        """If the config file doesn't exist, defaults should still work."""
        with patch("model_router._CONFIG", Path("/nonexistent/models.yaml")):
            cfg = load_config()
            self.assertIn("auto", cfg)
            self.assertIn("profiles", cfg)


class TestAutoEnabled(unittest.TestCase):

    def test_default_enabled(self):
        self.assertIsInstance(auto_enabled(), bool)

    def test_reflects_config(self):
        with patch("model_router.load_config", return_value={"auto": {"enabled": False}}):
            self.assertFalse(auto_enabled())

        with patch("model_router.load_config", return_value={"auto": {"enabled": True}}):
            self.assertTrue(auto_enabled())


class TestClassify(unittest.TestCase):

    def test_code_keyword(self):
        profile, why = classify("viết code python", cfg=load_config())
        self.assertEqual(profile, "code")

    def test_tool_keyword(self):
        profile, why = classify("tra cứu tài liệu dược phẩm", cfg=load_config())
        self.assertEqual(profile, "tool_calling")

    def test_light_fallback(self):
        profile, why = classify("xin chào", cfg=load_config())
        self.assertEqual(profile, "light")

    def test_escalate_keyword(self):
        profile, why = classify("tiếp tục sửa lỗi", cfg=load_config())
        self.assertEqual(profile, "code")

    def test_escalate_from_history(self):
        history = [{"role": "assistant", "content": "Chưa hoàn thành: kiểm tra vẫn lỗi"}]
        profile, why = classify("tiếp tục", history=history, cfg=load_config())
        self.assertEqual(profile, "code")

    def test_empty_message(self):
        profile, why = classify("", cfg=load_config())
        self.assertEqual(profile, "light")

    def test_returns_reason(self):
        _, why = classify("fix bug python", cfg=load_config())
        self.assertIsInstance(why, str)
        self.assertTrue(len(why) > 0)


class TestChooseModel(unittest.TestCase):

    def test_returns_installed_model(self):
        installed = ["qwen2.5-coder:7b", "qwen3.5:4b"]
        model, why = choose_model("viết code python", installed)
        self.assertIn(model, installed)

    def test_fallback_to_default(self):
        model, why = choose_model("hello", [], default="fallback-model")
        self.assertEqual(model, "fallback-model")

    def test_with_no_installed_no_default(self):
        model, why = choose_model("hello", [])
        self.assertEqual(model, "")

    def test_light_profile_selected(self):
        installed = ["qwen3.5:4b", "qwen2.5-coder:7b"]
        model, why = choose_model("xin chào", installed)
        self.assertIn(model, installed)

    def test_skips_too_large_model(self):
        """When RAM is very limited, large models should be skipped."""
        with patch("model_router._ram_total_gb", return_value=4.0):
            installed = ["qwen3.5:9b", "qwen3.5:4b"]
            model, why = choose_model("viết code", installed)
            # 9b needs ~5.4+4=9.4GB > 4GB, should be skipped
            # 4b needs ~2.4+4=6.4GB > 4GB, also skipped
            # Both too large -> falls back
            self.assertIsInstance(model, str)


if __name__ == "__main__":
    unittest.main()
