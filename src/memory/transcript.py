"""
JSONL Transcript Logger.

Logs every event (user messages, tool calls, assistant responses)
as JSON Lines for a complete audit trail.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TranscriptLogger:
    """
    Append-only JSONL logger for conversation transcripts.

    Each line is a JSON object with:
    - timestamp: ISO 8601
    - type: "user_message" | "assistant_message" | "tool_call" | "tool_result" | "error"
    - content: the actual content
    - metadata: optional extra info
    """

    def __init__(self, session_dir: Path, session_id: str):
        self.session_dir = session_dir
        self.session_id = session_id
        self.log_path = session_dir / f"{session_id}.jsonl"
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def _write_event(self, event_type: str, content: Any, metadata: dict | None = None) -> None:
        """Write a single event to the JSONL log."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "session_id": self.session_id,
            "content": content,
        }
        if metadata:
            event["metadata"] = metadata

        try:
            with open(self.log_path, "a") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to write transcript: {e}")

    def log_user_message(self, message: str, channel: str = "cli") -> None:
        """Log a user message."""
        self._write_event("user_message", message, {"channel": channel})

    def log_assistant_message(self, message: str, model: str = "") -> None:
        """Log an assistant response."""
        self._write_event("assistant_message", message, {"model": model})

    def log_tool_call(self, tool_name: str, arguments: dict) -> None:
        """Log a tool call from the assistant."""
        self._write_event("tool_call", {
            "name": tool_name,
            "arguments": arguments,
        })

    def log_tool_result(self, tool_name: str, result: str, success: bool = True) -> None:
        """Log the result of a tool execution."""
        self._write_event("tool_result", {
            "name": tool_name,
            "result": result,
            "success": success,
        })

    def log_error(self, error: str, context: str = "") -> None:
        """Log an error event."""
        self._write_event("error", error, {"context": context})

    def read_transcript(self) -> list[dict]:
        """Read all events from the transcript."""
        events = []
        if self.log_path.exists():
            with open(self.log_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            events.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        return events

    def get_recent_events(self, count: int = 50) -> list[dict]:
        """Get the most recent N events."""
        events = self.read_transcript()
        return events[-count:]
