"""Backward-compatible tools module.

Re-exports WorkspaceTools and schemas from the tools package.
"""
from __future__ import annotations

from tools.workspace_tools import (
    SCHEMAS,
    WorkspaceTools,
    _BLOCKED,
    _normalize_python_source,
    _schema,
)

__all__ = [
    "SCHEMAS",
    "WorkspaceTools",
    "_BLOCKED",
    "_normalize_python_source",
    "_schema",
]
