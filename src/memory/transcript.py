"""
JSONL Transcript Logger.

Logs every event (user messages, tool calls, assistant responses)
as JSON Lines for a complete audit trail.
"""

from __future__ import annotations

import asyncio
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
    
    Uses a write queue to prevent concurrent write corruption.
    """

    def __init__(self, session_dir: Path, session_id: str):
        self.session_dir = session_dir
        self.session_id = session_id
        self.log_path = session_dir / f"{session_id}.jsonl"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Queue for serializing writes to prevent file corruption
        self._write_queue: asyncio.Queue | None = None
        self._writer_task = None
        self._start_writer()

    def _start_writer(self) -> None:
        """Start the background writer task."""
        try:
            loop = asyncio.get_event_loop()
            self._write_queue = asyncio.Queue()
            if not self._writer_task or self._writer_task.done():
                self._writer_task = loop.create_task(self._write_worker())
        except RuntimeError:
            # No event loop running, writes will be synchronous
            pass
    
    async def _write_worker(self) -> None:
        """Background worker that processes the write queue."""
        while True:
            try:
                event = await self._write_queue.get()
                if event is None:  # Shutdown signal
                    break
                
                try:
                    with open(self.log_path, "a") as f:
                        f.write(json.dumps(event, ensure_ascii=False) + "\n")
                except Exception as e:
                    logger.error(f"Failed to write transcript: {e}")
                finally:
                    self._write_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Writer worker error: {e}")

    def _write_event(self, event_type: str, content: Any, metadata: dict | None = None) -> None:
        """Queue a single event to be written to the JSONL log."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "session_id": self.session_id,
            "content": content,
        }
        if metadata:
            event["metadata"] = metadata

        try:
            # Try to queue for async write
            if self._write_queue and self._writer_task and not self._writer_task.done():
                self._write_queue.put_nowait(event)
            else:
                # Fallback to synchronous write if no event loop
                with open(self.log_path, "a") as f:
                    f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to queue/write transcript: {e}")

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
    
    async def flush(self) -> None:
        """Wait for all queued writes to complete."""
        if self._write_queue:
            await self._write_queue.join()
    
    def close(self) -> None:
        """Close the transcript logger and stop the writer task."""
        if self._write_queue:
            try:
                self._write_queue.put_nowait(None)  # Shutdown signal
            except:
                pass
        
        if self._writer_task and not self._writer_task.done():
            self._writer_task.cancel()
