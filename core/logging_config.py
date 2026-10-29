"""Professional logging system for the Local AI Agent.

Provides coloured console output, rotating file handlers, and a simple
``get_logger(name)`` / ``setup_logging()`` API.

Usage::

    from core.logging_config import setup_logging, get_logger

    setup_logging()           # call once at startup
    log = get_logger(__name__)
    log.info("Ready")
"""
from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"
APP_LOG = LOGS_DIR / "app.log"
ERROR_LOG = LOGS_DIR / "error.log"

MAX_BYTES = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_INITIALISED = False


# ---------------------------------------------------------------------------
# Optional colour support via *colorama*
# ---------------------------------------------------------------------------
def _try_init_colorama() -> bool:
    """Return ``True`` if colorama is available and initialised."""
    try:
        import colorama  # type: ignore[import-untyped]
        colorama.init(autoreset=True)
        return True
    except ImportError:
        return False


# ---------------------------------------------------------------------------
# Coloured console formatter
# ---------------------------------------------------------------------------
class _ColourFormatter(logging.Formatter):
    """Formatter that injects ANSI colour codes per log level."""

    _COLOURS = {
        logging.DEBUG:    "\033[36m",   # cyan
        logging.INFO:     "\033[32m",   # green
        logging.WARNING:  "\033[33m",   # yellow
        logging.ERROR:    "\033[31m",   # red
        logging.CRITICAL: "\033[1;31m", # bold red
    }
    _RESET = "\033[0m"

    def __init__(self, fmt: str, datefmt: str | None = None, *, use_colour: bool = True) -> None:
        super().__init__(fmt, datefmt)
        self._use_colour = use_colour

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        if self._use_colour:
            colour = self._COLOURS.get(record.levelno, "")
            return f"{colour}{msg}{self._RESET}"
        return msg


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def setup_logging(level: int | str | None = None) -> None:
    """Initialise the root logger with console + file handlers.

    Call this **once** at application startup (idempotent – repeated calls
    are harmless).

    Parameters
    ----------
    level:
        Override log level.  Falls back to the ``LOG_LEVEL`` environment
        variable, then to ``INFO``.
    """
    global _INITIALISED  # noqa: PLW0603
    if _INITIALISED:
        return

    # Determine effective level
    if level is None:
        level = os.environ.get("LOG_LEVEL", "INFO").upper()
    if isinstance(level, str):
        level = getattr(logging, level, logging.INFO)

    # Ensure logs/ directory exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(level)

    # --- Console handler ---------------------------------------------------
    has_colour = _try_init_colorama()
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(
        _ColourFormatter(_LOG_FORMAT, _DATE_FORMAT, use_colour=has_colour)
    )
    root.addHandler(console)

    # --- Rotating app.log ---------------------------------------------------
    file_handler = RotatingFileHandler(
        str(APP_LOG),
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
    root.addHandler(file_handler)

    # --- Rotating error.log (ERROR+ only) -----------------------------------
    error_handler = RotatingFileHandler(
        str(ERROR_LOG),
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
    root.addHandler(error_handler)

    # Quieten noisy third-party loggers
    for noisy in ("httpx", "httpcore", "urllib3", "gradio", "uvicorn.access"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _INITIALISED = True
    logging.getLogger("local_agent.startup").debug("Logging initialised (level=%s)", logging.getLevelName(level))


def get_logger(name: str) -> logging.Logger:
    """Return a named logger.

    If ``setup_logging()`` has not been called yet, it is called
    automatically with default settings so that callers always get a
    usable logger.
    """
    if not _INITIALISED:
        setup_logging()
    return logging.getLogger(name)
