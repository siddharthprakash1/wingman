"""
Cron tool — schedule and manage recurring tasks.

Uses a simple JSON-based job store in the workspace.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from src.config.settings import get_settings
from src.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


def _get_cron_db() -> Path:
    """Get the path to the cron jobs database."""
    settings = get_settings()
    workspace = settings.workspace_path
    cron_dir = workspace / "cron"
    cron_dir.mkdir(parents=True, exist_ok=True)
    return cron_dir / "jobs.json"


def _load_jobs() -> list[dict[str, Any]]:
    """Load all cron jobs from the database."""
    db = _get_cron_db()
    if db.exists():
        try:
            return json.loads(db.read_text())
        except json.JSONDecodeError:
            return []
    return []


def _save_jobs(jobs: list[dict[str, Any]]) -> None:
    """Save jobs to the database."""
    db = _get_cron_db()
    db.write_text(json.dumps(jobs, indent=2, default=str))


async def cron_add(
    name: str,
    schedule: str,
    command: str,
    description: str = "",
) -> str:
    """
    Add a new scheduled task.

    Args:
        name: A short name for the task.
        schedule: Cron expression (e.g. "0 9 * * *" for daily at 9am, or natural language like "every hour").
        command: The command or action to execute.
        description: Optional description of what this task does.
    """
    jobs = _load_jobs()

    job = {
        "id": str(uuid.uuid4())[:8],
        "name": name,
        "schedule": schedule,
        "command": command,
        "description": description,
        "created_at": datetime.now().isoformat(),
        "enabled": True,
        "last_run": None,
    }

    jobs.append(job)
    _save_jobs(jobs)

    return f"✅ Scheduled task '{name}' (id: {job['id']})\n  Schedule: {schedule}\n  Command: {command}"


async def cron_list() -> str:
    """List all scheduled tasks."""
    jobs = _load_jobs()
    if not jobs:
        return "No scheduled tasks. Use cron_add to create one."

    output = "📅 Scheduled Tasks\n" + "─" * 40 + "\n\n"
    for job in jobs:
        status = "🟢" if job.get("enabled", True) else "🔴"
        output += f"{status} **{job['name']}** (id: {job['id']})\n"
        output += f"   Schedule: {job['schedule']}\n"
        output += f"   Command: {job['command']}\n"
        if job.get("description"):
            output += f"   Description: {job['description']}\n"
        if job.get("last_run"):
            output += f"   Last run: {job['last_run']}\n"
        output += "\n"

    return output


async def cron_remove(job_id: str) -> str:
    """
    Remove a scheduled task by its ID.

    Args:
        job_id: The ID of the task to remove.
    """
    jobs = _load_jobs()
    original_count = len(jobs)
    jobs = [j for j in jobs if j.get("id") != job_id]

    if len(jobs) == original_count:
        return f"❌ No task found with id: {job_id}"

    _save_jobs(jobs)
    return f"✅ Removed task {job_id}"


def register_cron_tools(registry: ToolRegistry) -> None:
    """Register cron tools with the registry."""
    registry.register(
        name="cron_add",
        description="Schedule a new recurring task with a cron expression or natural language schedule.",
        parameters={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Short name for the task",
                },
                "schedule": {
                    "type": "string",
                    "description": "Cron expression (e.g. '0 9 * * *') or natural language (e.g. 'every hour')",
                },
                "command": {
                    "type": "string",
                    "description": "The command or action to execute",
                },
                "description": {
                    "type": "string",
                    "description": "Optional description of the task",
                    "default": "",
                },
            },
            "required": ["name", "schedule", "command"],
        },
        func=cron_add,
    )

    registry.register(
        name="cron_list",
        description="List all scheduled tasks.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
        func=cron_list,
    )

    registry.register(
        name="cron_remove",
        description="Remove a scheduled task by its ID.",
        parameters={
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "The ID of the task to remove",
                },
            },
            "required": ["job_id"],
        },
        func=cron_remove,
    )
