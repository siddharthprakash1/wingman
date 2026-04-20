"""
SQLite tool — query/exec/schema on workspace-local DB files.

DB paths must live inside the workspace sandbox. Uses stdlib sqlite3 (no deps).
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from pathlib import Path
from typing import Any

from src.config.settings import get_settings
from src.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


def _workspace_root() -> Path:
    return Path(os.path.expanduser(get_settings().agents.defaults.workspace)).resolve()


def _resolve_db(db_path: str) -> tuple[Path, str | None]:
    root = _workspace_root()
    p = Path(os.path.expanduser(db_path)).resolve()
    try:
        p.relative_to(root)
    except ValueError:
        return p, f"DB path must be inside workspace: {root}"
    return p, None


def _rows_to_json(cur: sqlite3.Cursor) -> list[dict[str, Any]]:
    cols = [c[0] for c in cur.description] if cur.description else []
    return [dict(zip(cols, row, strict=False)) for row in cur.fetchall()]


async def sqlite_query(db_path: str, sql: str, params: list[Any] | None = None) -> str:
    """Run a read-only SELECT / PRAGMA / EXPLAIN query and return JSON rows."""
    p, err = _resolve_db(db_path)
    if err:
        return err

    stripped = sql.strip().lower()
    if not (stripped.startswith("select") or stripped.startswith("pragma")
            or stripped.startswith("explain") or stripped.startswith("with")):
        return "sqlite_query only accepts SELECT/PRAGMA/EXPLAIN/WITH. Use sqlite_exec for writes."

    try:
        conn = sqlite3.connect(str(p))
        try:
            cur = conn.execute(sql, params or [])
            rows = _rows_to_json(cur)
            return json.dumps({"rows": rows, "count": len(rows)}, indent=2, default=str)
        finally:
            conn.close()
    except sqlite3.Error as e:
        return f"SQL error: {e}"


async def sqlite_exec(db_path: str, sql: str, params: list[Any] | None = None) -> str:
    """Run a write statement (INSERT/UPDATE/DELETE/CREATE/DROP) in a transaction."""
    p, err = _resolve_db(db_path)
    if err:
        return err

    try:
        conn = sqlite3.connect(str(p))
        try:
            with conn:
                cur = conn.execute(sql, params or [])
            return json.dumps({
                "rows_affected": cur.rowcount,
                "last_insert_rowid": cur.lastrowid,
            }, indent=2)
        finally:
            conn.close()
    except sqlite3.Error as e:
        return f"SQL error: {e}"


async def sqlite_schema(db_path: str, table: str = "") -> str:
    """Show schema for all tables (or one named table)."""
    p, err = _resolve_db(db_path)
    if err:
        return err
    try:
        conn = sqlite3.connect(str(p))
        try:
            if table:
                cur = conn.execute(
                    "SELECT name, sql FROM sqlite_master WHERE type IN ('table','view','index') AND name=?",
                    (table,),
                )
            else:
                cur = conn.execute(
                    "SELECT name, type, sql FROM sqlite_master WHERE type IN ('table','view','index') ORDER BY type, name"
                )
            rows = _rows_to_json(cur)
            return json.dumps(rows, indent=2, default=str) if rows else "(empty schema)"
        finally:
            conn.close()
    except sqlite3.Error as e:
        return f"SQL error: {e}"


def register_sqlite_tools(registry: ToolRegistry) -> None:
    registry.register(
        name="sqlite_query",
        description=(
            "Run a read-only SELECT/PRAGMA/EXPLAIN/WITH query against a SQLite "
            "database inside the workspace. Returns JSON rows."
        ),
        parameters={
            "type": "object",
            "properties": {
                "db_path": {"type": "string", "description": "Path to the .sqlite/.db file (inside workspace)"},
                "sql": {"type": "string", "description": "Read-only SQL statement"},
                "params": {
                    "type": "array",
                    "items": {"type": ["string", "number", "boolean", "null"]},
                    "description": "Optional bound parameters",
                },
            },
            "required": ["db_path", "sql"],
        },
        func=sqlite_query,
    )
    registry.register(
        name="sqlite_exec",
        description=(
            "Execute a write SQL statement (INSERT/UPDATE/DELETE/CREATE/DROP/etc.) "
            "inside a transaction. Returns rows_affected and last_insert_rowid."
        ),
        parameters={
            "type": "object",
            "properties": {
                "db_path": {"type": "string"},
                "sql": {"type": "string"},
                "params": {
                    "type": "array",
                    "items": {"type": ["string", "number", "boolean", "null"]},
                },
            },
            "required": ["db_path", "sql"],
        },
        func=sqlite_exec,
    )
    registry.register(
        name="sqlite_schema",
        description="Show the CREATE statements for all tables/views/indexes in a SQLite DB.",
        parameters={
            "type": "object",
            "properties": {
                "db_path": {"type": "string"},
                "table": {"type": "string", "description": "Optional single-table filter", "default": ""},
            },
            "required": ["db_path"],
        },
        func=sqlite_schema,
    )
