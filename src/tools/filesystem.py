"""
Filesystem tools — read, write, edit, and list files.
"""

from __future__ import annotations

import os
import logging
from pathlib import Path

from src.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

# Directories that should never be accessed
BLOCKED_PATHS = {
    '/etc/passwd', '/etc/shadow', '/etc/sudoers',
    '/root', '/var/log/auth.log', '/etc/ssh',
    '/var/root', '/.Trashes',
}

# Allowed workspace directories (relative to home or current working directory)
ALLOWED_WORKSPACES = {
    Path.home(),
    Path.cwd(),
}

def _is_safe_path(path: Path) -> bool:
    """Check if path is safe to access (no sensitive system files or path traversal)."""
    try:
        resolved = path.resolve(strict=False)
    except Exception:
        return False
    
    resolved_str = str(resolved)
    
    # Block absolute paths to sensitive locations
    for blocked in BLOCKED_PATHS:
        if resolved_str.startswith(blocked):
            return False
    
    # Check for path traversal attempts (../ sequences)
    # After resolving, ensure the path is within allowed workspaces
    path_str = str(path)
    if '..' in path_str.split(os.sep):
        # Verify the resolved path is within allowed boundaries
        is_within_workspace = any(
            resolved.is_relative_to(workspace) 
            for workspace in ALLOWED_WORKSPACES
        )
        if not is_within_workspace:
            logger.warning(f"Path traversal attempt detected: {path} -> {resolved}")
            return False
    
    # Additional check: prevent access to hidden system directories in root
    if resolved_str.startswith('/.'):
        return False
    
    return True


async def read_file(path: str, start_line: int = 0, end_line: int = 0) -> str:
    """
    Read the contents of a file.

    Args:
        path: Absolute or relative path to the file.
        start_line: Start line (1-indexed, 0 = from beginning).
        end_line: End line (1-indexed, 0 = to end).
    """
    try:
        p = Path(path).expanduser().resolve()
        if not _is_safe_path(p):
            return f"❌ Access denied: {path}"
        if not p.exists():
            return f"❌ File not found: {path}"
        if not p.is_file():
            return f"❌ Not a file: {path}"

        content = p.read_text(encoding="utf-8", errors="replace")

        if start_line > 0 or end_line > 0:
            lines = content.split("\n")
            start = max(0, start_line - 1) if start_line > 0 else 0
            end = end_line if end_line > 0 else len(lines)
            content = "\n".join(lines[start:end])

        return content
    except Exception as e:
        return f"❌ Error reading file: {e}"


async def write_file(path: str, content: str) -> str:
    """
    Write content to a file. Creates parent directories if needed.

    Args:
        path: Absolute or relative path to the file.
        content: The content to write.
    """
    try:
        p = Path(path).expanduser().resolve()
        if not _is_safe_path(p):
            return f"❌ Access denied: {path}"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"✅ Wrote {len(content)} bytes to {p}"
    except Exception as e:
        return f"❌ Error writing file: {e}"


async def edit_file(
    path: str,
    target_content: str,
    replacement_content: str,
) -> str:
    """
    Edit a file by replacing target_content with replacement_content.

    Args:
        path: Path to the file.
        target_content: The exact text to find and replace.
        replacement_content: The replacement text.
    """
    try:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return f"❌ File not found: {path}"

        original = p.read_text(encoding="utf-8")

        if target_content not in original:
            return f"❌ Target content not found in {path}. Make sure it matches exactly."

        count = original.count(target_content)
        modified = original.replace(target_content, replacement_content, 1)
        p.write_text(modified, encoding="utf-8")

        return (
            f"✅ Replaced 1 occurrence in {p}"
            + (f" ({count - 1} more occurrence(s) remain)" if count > 1 else "")
        )
    except Exception as e:
        return f"❌ Error editing file: {e}"


async def list_directory(path: str = ".", show_hidden: bool = False) -> str:
    """
    List files and directories at the given path.

    Args:
        path: Directory path to list (default: current directory).
        show_hidden: Whether to show hidden files (default: false).
    """
    try:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return f"❌ Directory not found: {path}"
        if not p.is_dir():
            return f"❌ Not a directory: {path}"

        entries = []
        for item in sorted(p.iterdir()):
            if not show_hidden and item.name.startswith("."):
                continue

            if item.is_dir():
                # Count children
                try:
                    child_count = sum(1 for _ in item.iterdir())
                    entries.append(f"📁 {item.name}/ ({child_count} items)")
                except PermissionError:
                    entries.append(f"📁 {item.name}/ (permission denied)")
            else:
                size = item.stat().st_size
                if size < 1024:
                    size_str = f"{size}B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f}KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f}MB"
                entries.append(f"📄 {item.name} ({size_str})")

        if not entries:
            return f"(empty directory: {p})"

        header = f"📂 {p}\n{'─' * 40}\n"
        return header + "\n".join(entries)
    except Exception as e:
        return f"❌ Error listing directory: {e}"


def register_filesystem_tools(registry: ToolRegistry) -> None:
    """Register filesystem tools with the registry."""
    registry.register(
        name="read_file",
        description="Read the contents of a file. Supports line ranges.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute or relative path to the file",
                },
                "start_line": {
                    "type": "integer",
                    "description": "Start line (1-indexed, 0 = from beginning)",
                    "default": 0,
                },
                "end_line": {
                    "type": "integer",
                    "description": "End line (1-indexed, 0 = to end)",
                    "default": 0,
                },
            },
            "required": ["path"],
        },
        func=read_file,
    )

    registry.register(
        name="write_file",
        description="Write content to a file. Creates the file and parent directories if they don't exist.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to write",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file",
                },
            },
            "required": ["path", "content"],
        },
        func=write_file,
    )

    registry.register(
        name="edit_file",
        description="Edit a file by finding and replacing exact text content.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to edit",
                },
                "target_content": {
                    "type": "string",
                    "description": "The exact text to find in the file",
                },
                "replacement_content": {
                    "type": "string",
                    "description": "The text to replace it with",
                },
            },
            "required": ["path", "target_content", "replacement_content"],
        },
        func=edit_file,
    )

    registry.register(
        name="list_dir",
        description="List files and directories at the given path.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path to list (default: current directory)",
                    "default": ".",
                },
                "show_hidden": {
                    "type": "boolean",
                    "description": "Whether to show hidden files",
                    "default": False,
                },
            },
            "required": [],
        },
        func=list_directory,
    )
