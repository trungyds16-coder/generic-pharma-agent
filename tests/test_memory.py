"""Unit tests for the memory management subsystem."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from memory import MemoryManager


class TestMemoryManager(unittest.TestCase):

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.tmp.name)
        self.memory = MemoryManager(base_dir=self.base_dir)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_ensure_dirs_creates_structure(self) -> None:
        self.assertTrue(self.memory.data_dir.is_dir())
        self.assertTrue((self.memory.data_dir / "cache").is_dir())

    def test_write_and_read_json(self) -> None:
        test_file = self.base_dir / "sub" / "data.json"
        data = {"key": "value", "count": 42}
        self.memory.write_json(test_file, data)
        self.assertTrue(test_file.is_file())

        loaded = self.memory.read_json(test_file)
        self.assertEqual(loaded, data)

    def test_read_json_nonexistent_returns_default(self) -> None:
        nonexistent = self.base_dir / "missing.json"
        res = self.memory.read_json(nonexistent, default={"fallback": True})
        self.assertEqual(res, {"fallback": True})

    def test_create_and_list_chats(self) -> None:
        project_dir = self.base_dir / "project1"
        chat = self.memory.create_chat(project_dir, title="Chat 1")
        self.assertIn("id", chat)
        self.assertEqual(chat["title"], "Chat 1")

        chats = self.memory.list_chats(project_dir)
        self.assertEqual(len(chats), 1)
        self.assertEqual(chats[0]["id"], chat["id"])

    def test_save_chat_history(self) -> None:
        project_dir = self.base_dir / "project1"
        chat = self.memory.create_chat(project_dir, title="Test")
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]
        saved = self.memory.save_chat(project_dir, chat, history)
        self.assertEqual(saved["messages"], history)

    def test_checkpoint_roundtrip(self) -> None:
        project_dir = self.base_dir / "project1"
        self.memory.save_checkpoint(
            project_dir,
            state="completed",
            model="qwen2.5-coder:7b",
            chat_id="test-chat",
            last_reply="Finished work",
        )
        cp = self.memory.get_checkpoint(project_dir)
        self.assertEqual(cp.get("state"), "completed")
        self.assertEqual(cp.get("model"), "qwen2.5-coder:7b")
        self.assertEqual(cp.get("chat_id"), "test-chat")

    def test_usage_tracking(self) -> None:
        u1 = self.memory.get_usage()
        self.assertEqual(u1.get("total_tokens", 0), 0)

        self.memory.update_usage(prompt_tokens=100, output_tokens=50)
        u2 = self.memory.get_usage()
        self.assertEqual(u2["prompt_tokens"], 100)
        self.assertEqual(u2["output_tokens"], 50)
        self.assertEqual(u2["total_tokens"], 150)


if __name__ == "__main__":
    unittest.main()
