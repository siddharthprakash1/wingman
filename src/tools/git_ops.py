"""
Git operations tool.

Read-only queries (status/diff/log/branch/show) plus commit. All operations
are scoped to a repo path inside the workspace sandbox; network operations
(push/pull/fetch/clone) and destructive ops (reset --hard, push --force,
branch -D) are blocked.
"""

from __future__ import annotations

import asyncio
import logging
import os
import shlex
from pathlib import Path

from src.config.settings import get_settings
from src.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

# git subcommands that modify remotes, destroy history, or reach the network
_BLOCKED_SUBCOMMANDS = {
    "push", "fetch", "pull", "clone", "remote", "submodule",
    "reset", "rebase", "filter-branch", "gc", "prune", "fsck",
    "config",  # avoid clobbering user's git config
}

# destructive flag combos that sneak past subcommand checks
_BLOCKED_FLAG_PATTERNS = [
    "--force", "-f ",
    "--hard",
    "-D",   # git branch -D (force delete)
    "--delete --force",
]


def _workspace_root() -> Path:
    s = get_settings()
    return Path(os.path.expanduser(s.agents.defaults.workspace)).resolve()


def _resolve_repo(repo_path: str) -> tuple[Path, str | None]:
    root = _workspace_root()
    p = Path(os.path.expanduser(repo_path or ".")).resolve()
    try:
        p.relative_to(root)
    except ValueError:
        return p, f"Repo path must be inside workspace: {root}"
    if not p.exists():
        return p, f"Path does not exist: {p}"
    if not (p / ".git").exists():
        return p, f"Not a git repository: {p}"
    return p, None


async def _run_git(args: list[str], cwd: Path, timeout: int = 30) -> str:
    cmdline = " ".join(shlex.quote(a) for a in args)
    for sub in _BLOCKED_SUBCOMMANDS:
        if args and args[0] == sub:
            return f"Blocked: `git {sub}` is not allowed"
    lower = cmdline.lower()
    for bad in _BLOCKED_FLAG_PATTERNS:
        if bad in lower:
            return f"Blocked: dangerous flag `{bad.strip()}` not allowed"

    try:
        proc = await asyncio.create_subprocess_exec(
            "git", *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(cwd),
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        return f"git {args[0] if args else ''} timed out after {timeout}s"
    except Exception as e:
        return f"git failed: {e}"

    out = stdout.decode("utf-8", errors="replace")
    err = stderr.decode("utf-8", errors="replace")
    parts = []
    if out.strip():
        parts.append(out.rstrip())
    if err.strip():
        parts.append(f"[stderr]\n{err.rstrip()}")
    if proc.returncode != 0:
        parts.append(f"[exit {proc.returncode}]")
    return "\n".join(parts) if parts else "(no output)"


async def git_status(repo_path: str = ".") -> str:
    """Show working tree status."""
    p, err = _resolve_repo(repo_path)
    if err:
        return err
    return await _run_git(["status", "--short", "--branch"], cwd=p)


async def git_diff(repo_path: str = ".", staged: bool = False, path: str = "") -> str:
    """Show uncommitted changes. Set staged=True for index diff."""
    p, err = _resolve_repo(repo_path)
    if err:
        return err
    args = ["diff"]
    if staged:
        args.append("--staged")
    if path:
        args.extend(["--", path])
    return await _run_git(args, cwd=p)


async def git_log(repo_path: str = ".", max_entries: int = 20, path: str = "") -> str:
    """Show recent commit history."""
    p, err = _resolve_repo(repo_path)
    if err:
        return err
    args = ["log", f"-n{max_entries}", "--oneline", "--decorate"]
    if path:
        args.extend(["--", path])
    return await _run_git(args, cwd=p)


async def git_branch(repo_path: str = ".") -> str:
    """List branches."""
    p, err = _resolve_repo(repo_path)
    if err:
        return err
    return await _run_git(["branch", "-vv"], cwd=p)


async def git_show(repo_path: str = ".", ref: str = "HEAD") -> str:
    """Show a commit's diff and message."""
    p, err = _resolve_repo(repo_path)
    if err:
        return err
    return await _run_git(["show", "--stat", ref], cwd=p)


async def git_commit(
    repo_path: str,
    message: str,
    paths: list[str] | None = None,
) -> str:
    """
    Stage and commit files. If `paths` is given, only those paths are staged;
    otherwise all modified tracked files are staged.
    """
    p, err = _resolve_repo(repo_path)
    if err:
        return err
    if not message.strip():
        return "Commit message is required"

    # Stage
    if paths:
        add_out = await _run_git(["add", "--", *paths], cwd=p)
    else:
        add_out = await _run_git(["add", "-u"], cwd=p)
    if "Blocked" in add_out or "[exit" in add_out:
        return f"Stage failed:\n{add_out}"

    return await _run_git(["commit", "-m", message], cwd=p)


def register_git_tools(registry: ToolRegistry) -> None:
    registry.register(
        name="git_status",
        description="Show git working tree status for a repo inside the workspace.",
        parameters={
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "Path to the repo (must be inside workspace)",
                    "default": ".",
                }
            },
        },
        func=git_status,
    )
    registry.register(
        name="git_diff",
        description="Show uncommitted git changes. Pass staged=true for the index diff.",
        parameters={
            "type": "object",
            "properties": {
                "repo_path": {"type": "string", "default": "."},
                "staged": {"type": "boolean", "default": False},
                "path": {"type": "string", "default": ""},
            },
        },
        func=git_diff,
    )
    registry.register(
        name="git_log",
        description="Show recent commit history (oneline format).",
        parameters={
            "type": "object",
            "properties": {
                "repo_path": {"type": "string", "default": "."},
                "max_entries": {"type": "integer", "default": 20},
                "path": {"type": "string", "default": ""},
            },
        },
        func=git_log,
    )
    registry.register(
        name="git_branch",
        description="List git branches with upstream tracking info.",
        parameters={
            "type": "object",
            "properties": {"repo_path": {"type": "string", "default": "."}},
        },
        func=git_branch,
    )
    registry.register(
        name="git_show",
        description="Show a commit's full diff and metadata (default: HEAD).",
        parameters={
            "type": "object",
            "properties": {
                "repo_path": {"type": "string", "default": "."},
                "ref": {"type": "string", "default": "HEAD"},
            },
        },
        func=git_show,
    )
    registry.register(
        name="git_commit",
        description=(
            "Stage and commit files. If `paths` is given, stages only those; "
            "otherwise stages all modified tracked files (`git add -u`). "
            "Network and history-rewriting commands are blocked."
        ),
        parameters={
            "type": "object",
            "properties": {
                "repo_path": {"type": "string"},
                "message": {"type": "string"},
                "paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of paths to stage",
                },
            },
            "required": ["repo_path", "message"],
        },
        func=git_commit,
    )
