"""Autonomous Local AI Agent coordinator.

Provides high-level agent encapsulation over the Ollama-powered tool execution loop.
"""
from __future__ import annotations

from typing import Any, Callable

import ollama

from agent import DEFAULT_OPTIONS, SYSTEM, run_turn
from tools import WorkspaceTools


class LocalAgent:
    """High-level AI Agent interface for executing autonomous turns."""

    def __init__(
        self,
        model: str,
        client: ollama.Client | None = None,
        host: str = "http://127.0.0.1:11434",
        max_rounds: int = 12,
        system_prompt: str = SYSTEM,
        keep_alive: str = "5m",
    ) -> None:
        self.model = model
        self.host = host
        self.client = client or ollama.Client(host=host)
        self.max_rounds = max_rounds
        self.system_prompt = system_prompt
        self.keep_alive = keep_alive

    def run(
        self,
        messages: list[dict[str, Any]],
        tools: WorkspaceTools | None = None,
        on_progress: Callable[[str], None] | None = None,
        options: dict[str, Any] | None = None,
        auto_run: bool = True,
    ) -> tuple[str, dict[str, Any]]:
        """Execute a multi-round tool-augmented turn."""
        opts = {**DEFAULT_OPTIONS, **(options or {})}
        return run_turn(
            messages=messages,
            model=self.model,
            tools=tools,
            client=self.client,
            max_rounds=self.max_rounds,
            on_progress=on_progress,
            options=opts,
            auto_run=auto_run,
            keep_alive=self.keep_alive,
        )
