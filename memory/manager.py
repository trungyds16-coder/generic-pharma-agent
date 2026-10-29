"""Memory management subsystem for the Local AI Agent.

Handles persistent chat records, task state checkpoints, usage statistics,
and project priority sources. Fully compatible with Windows file paths.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


class MemoryManager:
    """Manages agent persistent state, chat history, and memory checkpoints."""

    def __init__(self, base_dir: Path | str | None = None) -> None:
        self.base_dir = Path(base_dir).resolve() if base_dir else Path.cwd().resolve()
        self.data_dir = self.base_dir / "data"
        self.usage_file = self.data_dir / "usage.json"
        self.ensure_dirs()

    def ensure_dirs(self) -> None:
        """Ensure necessary storage directories exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "cache").mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _now() -> str:
        return datetime.now().astimezone().isoformat(timespec="seconds")

    def read_json(self, path: Path, default: Any = None) -> Any:
        """Safely read and parse a JSON file."""
        try:
            if not path.is_file():
                return default
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return default

    def write_json(self, path: Path, value: Any) -> None:
        """Safely write data to a JSON file, creating parent directories."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")

    # --- Chat history memory ---
    def get_chat_file(self, project_dir: Path, chat_id: str) -> Path:
        return project_dir / ".agent" / "chats" / f"{chat_id}.json"

    def list_chats(self, project_dir: Path) -> list[dict[str, Any]]:
        folder = project_dir / ".agent" / "chats"
        if not folder.is_dir():
            return []
        records = []
        for file in folder.glob("*.json"):
            rec = self.read_json(file, None)
            if isinstance(rec, dict) and rec.get("id"):
                records.append(rec)
        return sorted(records, key=lambda row: row.get("created_at", ""), reverse=True)

    def create_chat(self, project_dir: Path, title: str = "Cuộc trò chuyện mới") -> dict[str, Any]:
        chat_id = str(uuid.uuid4())
        record = {
            "id": chat_id,
            "title": title,
            "created_at": self._now(),
            "updated_at": self._now(),
            "messages": [],
            "turns": [],
            "usage": {"prompt_tokens": 0, "output_tokens": 0, "total_tokens": 0},
        }
        self.write_json(self.get_chat_file(project_dir, chat_id), record)
        return record

    def save_chat(self, project_dir: Path, record: dict[str, Any], history: list[dict[str, Any]]) -> dict[str, Any]:
        record["messages"] = history
        record["updated_at"] = self._now()
        self.write_json(self.get_chat_file(project_dir, record["id"]), record)
        return record

    # --- Checkpoints ---
    def save_checkpoint(self, project_dir: Path, state: str, model: str, chat_id: str, last_reply: str) -> None:
        checkpoint_path = project_dir / ".agent" / "checkpoint.json"
        data = {
            "updated_at": self._now(),
            "state": state,
            "model": model,
            "chat_id": chat_id,
            "last_reply": last_reply[-2000:],
        }
        self.write_json(checkpoint_path, data)

    def get_checkpoint(self, project_dir: Path) -> dict[str, Any]:
        return self.read_json(project_dir / ".agent" / "checkpoint.json", {})

    # --- Global Usage Stats ---
    def get_usage(self) -> dict[str, int]:
        return self.read_json(self.usage_file, {"prompt_tokens": 0, "output_tokens": 0, "total_tokens": 0})

    def update_usage(self, prompt_tokens: int, output_tokens: int) -> dict[str, int]:
        current = self.get_usage()
        current["prompt_tokens"] = current.get("prompt_tokens", 0) + prompt_tokens
        current["output_tokens"] = current.get("output_tokens", 0) + output_tokens
        current["total_tokens"] = current["prompt_tokens"] + current["output_tokens"]
        self.write_json(self.usage_file, current)
        return current
