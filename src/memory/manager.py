"""
Memory Manager — read/write workspace memory files.

Manages the persistent markdown memory files that form the agent's
long-term knowledge: AGENTS.md, SOUL.md, IDENTITY.md, USER.md,
MEMORY.md, TOOLS.md, plus daily conversation logs.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

# Memory file names (same as OpenClaw/PicoClaw workspace layout)
MEMORY_FILES = [
    "AGENTS.md",
    "SOUL.md",
    "IDENTITY.md",
    "USER.md",
    "MEMORY.md",
    "TOOLS.md",
]

# Template directory relative to this file
TEMPLATES_DIR = Path(__file__).parent / "templates"


class MemoryManager:
    """
    Manages the agent's persistent memory.

    Workspace layout:
        workspace/
        ├── sessions/           # Per-session chat histories
        ├── memory/             # Daily logs (YYYY-MM-DD.md)
        ├── cron/               # Scheduled jobs
        ├── skills/             # Custom skills
        ├── AGENTS.md           # Behavioral guidelines
        ├── IDENTITY.md         # Who the agent is
        ├── SOUL.md             # Personality
        ├── USER.md             # User preferences
        ├── MEMORY.md           # Long-term curated facts
        └── TOOLS.md            # Tool descriptions
    """

    def __init__(self, workspace_path: Path | None = None):
        settings = get_settings()
        self.workspace = workspace_path or settings.workspace_path
        self.sessions_dir = self.workspace / "sessions"
        self.memory_dir = self.workspace / "memory"
        self.cron_dir = self.workspace / "cron"
        self.skills_dir = self.workspace / "skills"

    def ensure_workspace(self) -> None:
        """Create the workspace directory structure if it doesn't exist."""
        for directory in [
            self.workspace,
            self.sessions_dir,
            self.memory_dir,
            self.cron_dir,
            self.skills_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

        # Copy default templates if memory files don't exist
        for filename in MEMORY_FILES:
            target = self.workspace / filename
            if not target.exists():
                template = TEMPLATES_DIR / filename
                if template.exists():
                    target.write_text(template.read_text())
                    logger.info(f"Created {filename} from template")
                else:
                    target.write_text(f"# {filename.replace('.md', '')}\n\n")
                    logger.info(f"Created empty {filename}")

    def read_file(self, filename: str) -> str:
        """Read a memory file from the workspace."""
        path = self.workspace / filename
        if path.exists():
            return path.read_text()
        return ""

    def write_file(self, filename: str, content: str) -> None:
        """Write content to a memory file."""
        path = self.workspace / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        logger.debug(f"Updated {filename}")

    def append_to_file(self, filename: str, content: str) -> None:
        """Append content to a memory file."""
        path = self.workspace / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a") as f:
            f.write(content)

    def read_all_memory(self) -> dict[str, str]:
        """Read all core memory files and return as a dict."""
        memories = {}
        for filename in MEMORY_FILES:
            content = self.read_file(filename)
            if content.strip():
                memories[filename] = content
        return memories

    # --- Daily logs ---

    def get_daily_log_path(self, date: datetime | None = None) -> Path:
        """Get the path for today's (or a specific date's) conversation log."""
        date = date or datetime.now()
        return self.memory_dir / f"{date.strftime('%Y-%m-%d')}.md"

    def read_daily_log(self, date: datetime | None = None) -> str:
        """Read today's conversation log."""
        path = self.get_daily_log_path(date)
        if path.exists():
            return path.read_text()
        return ""

    def append_daily_log(self, entry: str, date: datetime | None = None) -> None:
        """Append an entry to today's conversation log."""
        path = self.get_daily_log_path(date)
        path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%H:%M:%S")
        with open(path, "a") as f:
            f.write(f"\n[{timestamp}] {entry}\n")

    # --- Sessions ---

    def list_sessions(self) -> list[str]:
        """List all session IDs."""
        if not self.sessions_dir.exists():
            return []
        return sorted([
            f.stem for f in self.sessions_dir.iterdir()
            if f.suffix == ".json"
        ])

    def get_session_path(self, session_id: str) -> Path:
        """Get the path for a session file."""
        return self.sessions_dir / f"{session_id}.json"

    # --- Tools for the agent to use ---

    def memory_update_tool(self, key: str, content: str) -> str:
        """
        Tool: Update a specific memory file.
        The agent can call this to persist information.
        """
        valid_files = {f.replace(".md", "").lower(): f for f in MEMORY_FILES}
        key_lower = key.lower()
        if key_lower in valid_files:
            filename = valid_files[key_lower]
            self.write_file(filename, content)
            return f"✅ Updated {filename}"
        else:
            return f"❌ Unknown memory file '{key}'. Valid: {list(valid_files.keys())}"

    def memory_append_tool(self, key: str, content: str) -> str:
        """
        Tool: Append to a memory file.
        Useful for adding new facts to MEMORY.md.
        """
        valid_files = {f.replace(".md", "").lower(): f for f in MEMORY_FILES}
        key_lower = key.lower()
        if key_lower in valid_files:
            filename = valid_files[key_lower]
            self.append_to_file(filename, f"\n{content}\n")
            return f"✅ Appended to {filename}"
        else:
            return f"❌ Unknown memory file '{key}'. Valid: {list(valid_files.keys())}"

    def memory_read_tool(self, key: str) -> str:
        """
        Tool: Read a specific memory file.
        """
        valid_files = {f.replace(".md", "").lower(): f for f in MEMORY_FILES}
        key_lower = key.lower()
        if key_lower in valid_files:
            filename = valid_files[key_lower]
            content = self.read_file(filename)
            return content if content else f"(empty — {filename} has no content yet)"
        else:
            return f"❌ Unknown memory file '{key}'. Valid: {list(valid_files.keys())}"
