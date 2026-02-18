"""
macOS System Tools — Control apps, Notes, Reminders, and Music.
"""

from __future__ import annotations

import logging
import subprocess
from typing import Optional

from src.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


# ==================== APPLICATION CONTROL ====================

def open_application(app_name: str) -> str:
    """
    Open a macOS application.

    Args:
        app_name: Application name (e.g., "Safari", "Notes", "Music").
    """
    try:
        subprocess.run(['open', '-a', app_name], check=True)
        return f"Opened {app_name}"
    except Exception as e:
        return f"Error opening {app_name}: {e}"


def close_application(app_name: str, force: bool = False) -> str:
    """
    Close a macOS application.

    Args:
        app_name: Application name.
        force: Force quit if True.
    """
    try:
        if force:
            subprocess.run(['killall', app_name], check=False)
        else:
            script = f'tell application "{app_name}" to quit'
            subprocess.run(['osascript', '-e', script], check=True)
        return f"Closed {app_name}"
    except Exception as e:
        return f"Error closing {app_name}: {e}"


def list_running_apps() -> str:
    """List all running applications."""
    try:
        result = subprocess.run(
            ['osascript', '-e', 'tell application "System Events" to get name of every process whose background only is false'],
            capture_output=True,
            text=True,
            check=True
        )
        apps = [app.strip() for app in result.stdout.split(',')]
        return f"Running apps ({len(apps)}): {', '.join(sorted(apps))}"
    except Exception as e:
        return f"Error listing apps: {e}"


# ==================== APPLE NOTES ====================

def create_note(title: str, content: str, folder: str = "Notes") -> str:
    """
    Create a new note in Apple Notes.

    Args:
        title: Note title.
        content: Note content.
        folder: Folder name (default: Notes).
    """
    try:
        title_escaped = title.replace('"', '\\"')
        content_escaped = content.replace('"', '\\"')
        
        script = f'''
        tell application "Notes"
            tell folder "{folder}"
                make new note with properties {{name:"{title_escaped}", body:"{content_escaped}"}}
            end tell
        end tell
        '''
        subprocess.run(['osascript', '-e', script], check=True)
        return f"Created note '{title}' in {folder}"
    except Exception as e:
        return f"Error creating note: {e}"


def search_notes(query: str, limit: int = 5) -> str:
    """
    Search Apple Notes.

    Args:
        query: Search query.
        limit: Maximum results (default 5).
    """
    try:
        script = f'''
        tell application "Notes"
            set noteList to {{}}
            set allNotes to every note
            repeat with aNote in allNotes
                set noteBody to body of aNote as text
                set noteName to name of aNote as text
                if noteBody contains "{query}" or noteName contains "{query}" then
                    set end of noteList to noteName
                end if
            end repeat
            return noteList
        end tell
        '''
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            check=True
        )
        notes = [n.strip() for n in result.stdout.split(',') if n.strip()][:limit]
        if not notes:
            return f"No notes found containing '{query}'"
        return f"Found {len(notes)} notes:\n" + "\n".join(f"- {n}" for n in notes)
    except Exception as e:
        return f"Error searching notes: {e}"


# ==================== REMINDERS ====================

def create_reminder(title: str, list_name: str = "Reminders") -> str:
    """
    Create a reminder in Apple Reminders.

    Args:
        title: Reminder title.
        list_name: List name (default: Reminders).
    """
    try:
        title_escaped = title.replace('"', '\\"')
        script = f'''
        tell application "Reminders"
            tell list "{list_name}"
                make new reminder with properties {{name:"{title_escaped}"}}
            end tell
        end tell
        '''
        subprocess.run(['osascript', '-e', script], check=True)
        return f"Created reminder '{title}' in list '{list_name}'"
    except Exception as e:
        return f"Error creating reminder: {e}"


# ==================== REGISTRATION ====================

def register_macos_tools(registry: ToolRegistry):
    """Register macOS tools."""
    registry.register(
        name="open_app",
        description="Open a macOS application",
        parameters={
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "Application name (e.g., 'Safari', 'Notes', 'Music')",
                },
            },
            "required": ["app_name"],
        },
        func=open_application,
    )
    registry.register(
        name="close_app",
        description="Close a macOS application",
        parameters={
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "Application name to close",
                },
                "force": {
                    "type": "boolean",
                    "description": "Force quit if True (default: False)",
                    "default": False,
                },
            },
            "required": ["app_name"],
        },
        func=close_application,
    )
    registry.register(
        name="list_running_apps",
        description="List all running applications on macOS",
        parameters={
            "type": "object",
            "properties": {},
        },
        func=list_running_apps,
    )
    registry.register(
        name="create_note",
        description="Create a new note in Apple Notes",
        parameters={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Note title",
                },
                "content": {
                    "type": "string",
                    "description": "Note content",
                },
                "folder": {
                    "type": "string",
                    "description": "Folder name (default: 'Notes')",
                    "default": "Notes",
                },
            },
            "required": ["title", "content"],
        },
        func=create_note,
    )
    registry.register(
        name="search_notes",
        description="Search Apple Notes by query",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results (default: 5)",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
        func=search_notes,
    )
    registry.register(
        name="create_reminder",
        description="Create a task in Apple Reminders",
        parameters={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Reminder title",
                },
                "list_name": {
                    "type": "string",
                    "description": "List name (default: 'Reminders')",
                    "default": "Reminders",
                },
            },
            "required": ["title"],
        },
        func=create_reminder,
    )
