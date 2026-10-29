"""Configuration module for the Local AI Agent.

Loads settings from config.yaml and optional .env file, validates paths,
and provides a unified Settings interface for the rest of the application.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

# --- Optional python-dotenv support ---
try:
    from dotenv import load_dotenv as _load_dotenv
except ImportError:
    _load_dotenv = None  # type: ignore[assignment]

import yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
CONFIG_YAML = BASE_DIR / "config.yaml"
ENV_FILE = BASE_DIR / ".env"

# Environment variable names we recognise from .env
_ENV_KEYS = (
    "OPENAI_API_KEY",
    "MODEL_NAME",
    "MEMORY_PATH",
    "LOG_LEVEL",
    "OLLAMA_HOST",
)


# ---------------------------------------------------------------------------
# Settings class
# ---------------------------------------------------------------------------
class Settings:
    """Unified configuration object.

    Priority (highest → lowest):
        1. Explicit environment variables
        2. Values in ``.env``
        3. Values in ``config.yaml``
        4. Built-in defaults
    """

    # Built-in defaults (used when neither YAML nor env provide a value)
    _DEFAULTS: dict[str, Any] = {
        "ollama_host": "http://127.0.0.1:11434",
        "ollama_models_dir": str(BASE_DIR / "models"),
        "model": "qwen2.5-coder:7b",
        "workspace_dir": str(BASE_DIR / "workspace"),
        "data_dir": str(BASE_DIR / "data"),
        "max_tool_rounds": 12,
        "python_timeout_sec": 180,
        "num_ctx": 8192,
        "auto_run": True,
        "require_plan": False,
        "claude_timeout_sec": 900,
        "model_keep_alive": "5m",
        "log_level": "INFO",
    }

    def __init__(self) -> None:
        # 1. Load .env (if python-dotenv is available and .env exists)
        if _load_dotenv is not None and ENV_FILE.is_file():
            _load_dotenv(ENV_FILE, override=False)
        elif ENV_FILE.is_file():
            # Fallback: manually parse simple KEY=VALUE lines
            self._manual_load_env(ENV_FILE)

        # 2. Load config.yaml
        self._yaml: dict[str, Any] = {}
        if CONFIG_YAML.is_file():
            try:
                raw = CONFIG_YAML.read_text(encoding="utf-8-sig")
                parsed = yaml.safe_load(raw)
                if isinstance(parsed, dict):
                    self._yaml = parsed
            except Exception as exc:  # noqa: BLE001
                print(f"[config] WARNING: Failed to parse {CONFIG_YAML}: {exc}", file=sys.stderr)

        # 3. Merge env overrides into the mapping
        self._data: dict[str, Any] = {**self._DEFAULTS, **self._yaml}

        # Map recognised env vars → config keys
        _env_to_key = {
            "OLLAMA_HOST": "ollama_host",
            "MODEL_NAME": "model",
            "MEMORY_PATH": "memory_path",
            "LOG_LEVEL": "log_level",
            "OPENAI_API_KEY": "openai_api_key",
        }
        for env_var, cfg_key in _env_to_key.items():
            val = os.environ.get(env_var)
            if val is not None and val != "":
                self._data[cfg_key] = val

        # 4. Validate & ensure critical directories exist
        self._ensure_directory("data_dir")
        self._ensure_directory("workspace_dir")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:
        """Return a config value by *key*, with an optional *default*."""
        return self._data.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def as_dict(self) -> dict[str, Any]:
        """Return a shallow copy of the full config dictionary."""
        return dict(self._data)

    # Convenience attribute access  ─ settings.model, settings.data_dir, …
    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError(f"No config key {name!r}") from None

    def __repr__(self) -> str:
        safe = {k: ("***" if "key" in k.lower() or "secret" in k.lower() else v)
                for k, v in self._data.items()}
        return f"Settings({safe})"

    # ------------------------------------------------------------------
    # Path helpers
    # ------------------------------------------------------------------
    @property
    def base_dir(self) -> Path:
        return BASE_DIR

    @property
    def data_path(self) -> Path:
        return Path(self._data["data_dir"]).resolve()

    @property
    def workspace_path(self) -> Path:
        return Path(self._data["workspace_dir"]).resolve()

    @property
    def logs_dir(self) -> Path:
        return BASE_DIR / "logs"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _ensure_directory(self, key: str) -> None:
        """Create the directory for *key* if it does not exist."""
        raw = self._data.get(key)
        if raw is None:
            return
        p = Path(str(raw)).resolve()
        try:
            p.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            print(
                f"[config] WARNING: Cannot create directory for '{key}' "
                f"({p}): {exc}",
                file=sys.stderr,
            )

    @staticmethod
    def _manual_load_env(path: Path) -> None:
        """Parse a simple .env file when python-dotenv is not installed.

        Only handles ``KEY=VALUE`` and ``KEY="VALUE"`` lines.
        Does **not** override variables already set in the environment.
        """
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("\"'")
                if key and key not in os.environ:
                    os.environ[key] = value
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
settings = Settings()
