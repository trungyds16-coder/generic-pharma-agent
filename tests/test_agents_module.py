"""Unit tests for the agents wrapper module."""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from agents import LocalAgent, SYSTEM, DEFAULT_OPTIONS


class TestLocalAgentModule(unittest.TestCase):

    def test_init_defaults(self) -> None:
        agent = LocalAgent(model="test-model")
        self.assertEqual(agent.model, "test-model")
        self.assertEqual(agent.host, "http://127.0.0.1:11434")
        self.assertEqual(agent.max_rounds, 12)
        self.assertEqual(agent.system_prompt, SYSTEM)

    def test_custom_options(self) -> None:
        agent = LocalAgent(model="custom", host="http://localhost:11435", max_rounds=5)
        self.assertEqual(agent.model, "custom")
        self.assertEqual(agent.host, "http://localhost:11435")
        self.assertEqual(agent.max_rounds, 5)

    @patch("agents.local_agent.run_turn")
    def test_run_delegates_to_run_turn(self, mock_run_turn: MagicMock) -> None:
        mock_run_turn.return_value = ("Done", {"rounds": 1})
        agent = LocalAgent(model="test-model")
        messages = [{"role": "user", "content": "hi"}]

        reply, usage = agent.run(messages)
        self.assertEqual(reply, "Done")
        self.assertEqual(usage["rounds"], 1)
        mock_run_turn.assert_called_once()


if __name__ == "__main__":
    unittest.main()
