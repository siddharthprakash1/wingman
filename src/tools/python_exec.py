"""
python_exec tool — run short Python snippets in a subprocess.

Executes in the workspace directory with a hard timeout. Not a persistent
REPL — every call is isolated. Use for quick data crunches, calculations,
one-off scripts.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

from src.config.settings import get_settings
from src.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


def _workspace_cwd() -> Path:
    s = get_settings()
    p = Path(os.path.expanduser(s.agents.defaults.workspace)).resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


async def python_exec(code: str, timeout: int = 30) -> str:
    """
    Run a Python snippet via `python -c` in the workspace directory.

    Args:
        code: Python source to execute.
        timeout: Max seconds (default 30, hard cap 300).
    """
    timeout = max(1, min(int(timeout), 300))
    cwd = _workspace_cwd()

    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-c", code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(cwd),
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
    except Exception as e:
        return f"Failed to spawn python: {e}"

    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        try:
            proc.kill()
        except Exception:
            pass
        return f"python_exec timed out after {timeout}s"

    out = stdout.decode("utf-8", errors="replace")
    err = stderr.decode("utf-8", errors="replace")
    parts = []
    if out:
        parts.append(out.rstrip())
    if err:
        parts.append(f"[stderr]\n{err.rstrip()}")
    if proc.returncode != 0:
        parts.append(f"[exit {proc.returncode}]")
    return "\n".join(parts) if parts else "(no output)"


def register_python_exec_tools(registry: ToolRegistry) -> None:
    registry.register(
        name="python_exec",
        description=(
            "Run a Python snippet in a fresh subprocess (no shared state "
            "between calls). Runs inside the workspace directory with a "
            "hard timeout. Good for calculations, data transformation, "
            "quick scripts. For persistent state, write to a file and re-read."
        ),
        parameters={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python source code. Use print() to emit output.",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Max seconds (default 30, max 300)",
                    "default": 30,
                },
            },
            "required": ["code"],
        },
        func=python_exec,
    )
