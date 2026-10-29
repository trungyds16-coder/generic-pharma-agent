"""Main entry point for the Local AI Agent.

Startup flow:
1. Load configuration & environment variables.
2. Initialize memory modules.
3. Load workspace tools and schemas.
4. Initialize the AI Agent.
5. Perform startup validation and launch web interface.
"""
from __future__ import annotations

import argparse
import signal
import sys
import urllib.error
import urllib.request
from pathlib import Path


def _check_ollama(host: str, timeout: float = 3.0) -> bool:
    """Return True if the Ollama API at host is reachable."""
    url = host.rstrip("/") + "/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=timeout):
            return True
    except (urllib.error.URLError, OSError):
        return False


def _graceful_shutdown(signum: int, frame: object) -> None:
    """Handle SIGINT / SIGTERM for a clean exit."""
    from core.logging_config import get_logger
    log = get_logger("local_agent.main")
    log.info("Received signal %s – shutting down gracefully...", signal.Signals(signum).name)
    sys.exit(0)


def main() -> None:
    """Application bootstrap: logging -> config -> memory -> tools -> agent -> launch."""
    parser = argparse.ArgumentParser(description="Local AI Agent - Windows 11")
    parser.add_argument("--check-only", action="store_true", help="Run startup validation and exit without starting UI")
    parser.add_argument("--port", type=int, default=7860, help="Web UI port (default: 7860)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")
    args = parser.parse_args()

    # Step 0: Initialize Logging System
    from core.logging_config import get_logger, setup_logging
    setup_logging()
    log = get_logger("local_agent.main")
    log.info("=" * 60)
    log.info("Starting Local AI Agent (Windows 11 Production Ready)")
    log.info("=" * 60)

    # Step 1: Load Configuration & Environment
    log.info("[1/5] Loading configuration and environment variables...")
    from config import settings
    log.info("  * Base Directory: %s", settings.base_dir)
    log.info("  * Data Directory: %s", settings.data_path)
    log.info("  * Workspace Directory: %s", settings.workspace_path)
    log.info("  * Active Model: %s", settings.get("model"))
    log.info("  * Ollama Host: %s", settings.get("ollama_host"))

    # Step 2: Initialize Memory Modules
    log.info("[2/5] Initializing memory system...")
    from memory import MemoryManager
    memory = MemoryManager(base_dir=settings.base_dir)
    memory.ensure_dirs()
    usage = memory.get_usage()
    log.info("  * Memory storage verified at: %s", memory.data_dir)
    log.info("  * Historical token usage: %d prompt, %d output (%d total)",
             usage.get("prompt_tokens", 0), usage.get("output_tokens", 0), usage.get("total_tokens", 0))

    # Step 3: Load Tools
    log.info("[3/5] Loading workspace tools...")
    from tools import SCHEMAS, WorkspaceTools
    tools = WorkspaceTools(root=settings.workspace_path)
    log.info("  * Registered tool schemas: %d tools available", len(SCHEMAS))
    log.info("  * Tools workspace bound to: %s", tools.root)

    # Step 4: Initialize AI Agent
    log.info("[4/5] Initializing AI Agent...")
    from agents import LocalAgent
    agent = LocalAgent(
        model=settings.get("model", "qwen2.5-coder:7b"),
        host=settings.get("ollama_host", "http://127.0.0.1:11434"),
        max_rounds=int(settings.get("max_tool_rounds", 12)),
        keep_alive=str(settings.get("model_keep_alive", "5m")),
    )
    log.info("  * Agent initialized with model: %s", agent.model)

    # Step 5: Startup Validation
    log.info("[5/5] Performing startup validation...")
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    ollama_ok = _check_ollama(agent.host)
    if ollama_ok:
        log.info("  [OK] Ollama API service is running and reachable.")
    else:
        log.warning("  [WARN] Ollama API at %s is NOT reachable. Please ensure Ollama is running.", agent.host)

    if args.check_only:
        log.info("Startup check passed successfully (--check-only requested). Exiting.")
        return

    # Register signal handlers
    signal.signal(signal.SIGINT, _graceful_shutdown)
    signal.signal(signal.SIGTERM, _graceful_shutdown)

    # Launch Application
    log.info("Launching Gradio UI on port %d...", args.port)
    try:
        from app import demo
        demo.launch(
            server_name="127.0.0.1",
            server_port=args.port,
            inbrowser=not args.no_browser,
        )
    except KeyboardInterrupt:
        log.info("Application stopped by user.")
    except Exception:
        log.exception("Fatal error during application launch")
        sys.exit(1)


if __name__ == "__main__":
    main()
