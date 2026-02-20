"""
Security Audit Logging System.

Tracks security-related events: workspace violations, blocked commands,
path traversal attempts, and other security incidents.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AuditSeverity(str, Enum):
    """Security event severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AuditEvent:
    """A security audit event."""
    
    def __init__(
        self,
        event_type: str,
        severity: AuditSeverity,
        message: str,
        details: dict[str, Any] | None = None,
        session_id: str | None = None,
    ):
        self.timestamp = datetime.now()
        self.event_type = event_type
        self.severity = severity
        self.message = message
        self.details = details or {}
        self.session_id = session_id
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details,
            "session_id": self.session_id,
        }


class SecurityAudit:
    """
    Security audit logging system.
    
    Logs all security events to a JSONL file and provides query capabilities.
    """
    
    def __init__(self, audit_dir: Path | None = None):
        if audit_dir is None:
            audit_dir = Path.home() / ".wingman" / "security"
        
        self.audit_dir = Path(audit_dir)
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.audit_file = self.audit_dir / "audit.jsonl"
        
        # Queue for async writes
        self._write_queue: asyncio.Queue | None = None
        self._writer_task = None
        self._start_writer()
    
    def _start_writer(self) -> None:
        """Start background writer task."""
        try:
            loop = asyncio.get_event_loop()
            self._write_queue = asyncio.Queue()
            if not self._writer_task or self._writer_task.done():
                self._writer_task = loop.create_task(self._write_worker())
        except RuntimeError:
            pass
    
    async def _write_worker(self) -> None:
        """Background worker for writing audit events."""
        while True:
            try:
                event = await self._write_queue.get()
                if event is None:
                    break
                
                try:
                    with open(self.audit_file, "a") as f:
                        f.write(json.dumps(event, ensure_ascii=False) + "\n")
                except Exception as e:
                    logger.error(f"Failed to write audit event: {e}")
                finally:
                    self._write_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Audit writer error: {e}")
    
    def log_event(self, event: AuditEvent) -> None:
        """Log a security event."""
        event_dict = event.to_dict()
        
        # Also log to standard logger based on severity
        if event.severity == AuditSeverity.CRITICAL:
            logger.error(f"SECURITY: {event.message}")
        elif event.severity == AuditSeverity.WARNING:
            logger.warning(f"SECURITY: {event.message}")
        else:
            logger.info(f"SECURITY: {event.message}")
        
        # Queue for async write
        try:
            if self._write_queue and self._writer_task and not self._writer_task.done():
                self._write_queue.put_nowait(event_dict)
            else:
                # Fallback to sync write
                with open(self.audit_file, "a") as f:
                    f.write(json.dumps(event_dict, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
    
    def log_workspace_violation(
        self, 
        path: str, 
        action: str,
        session_id: str | None = None,
    ) -> None:
        """Log a workspace boundary violation."""
        event = AuditEvent(
            event_type="workspace_violation",
            severity=AuditSeverity.WARNING,
            message=f"Workspace violation: {action} attempted on {path}",
            details={"path": path, "action": action},
            session_id=session_id,
        )
        self.log_event(event)
    
    def log_blocked_command(
        self,
        command: str,
        reason: str,
        session_id: str | None = None,
    ) -> None:
        """Log a blocked shell command."""
        event = AuditEvent(
            event_type="blocked_command",
            severity=AuditSeverity.WARNING,
            message=f"Command blocked: {command[:100]}",
            details={"command": command, "reason": reason},
            session_id=session_id,
        )
        self.log_event(event)
    
    def log_path_traversal(
        self,
        attempted_path: str,
        resolved_path: str,
        session_id: str | None = None,
    ) -> None:
        """Log a path traversal attempt."""
        event = AuditEvent(
            event_type="path_traversal",
            severity=AuditSeverity.CRITICAL,
            message=f"Path traversal attempt: {attempted_path} -> {resolved_path}",
            details={"attempted": attempted_path, "resolved": resolved_path},
            session_id=session_id,
        )
        self.log_event(event)
    
    def read_events(
        self,
        limit: int = 100,
        severity: AuditSeverity | None = None,
        event_type: str | None = None,
    ) -> list[dict]:
        """Read audit events with optional filters."""
        events = []
        
        if not self.audit_file.exists():
            return events
        
        with open(self.audit_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    event = json.loads(line)
                    
                    # Apply filters
                    if severity and event.get("severity") != severity.value:
                        continue
                    if event_type and event.get("event_type") != event_type:
                        continue
                    
                    events.append(event)
                except json.JSONDecodeError:
                    continue
        
        return events[-limit:]
    
    async def flush(self) -> None:
        """Wait for all queued events to be written."""
        if self._write_queue:
            await self._write_queue.join()
    
    def close(self) -> None:
        """Close the audit logger."""
        if self._write_queue:
            try:
                self._write_queue.put_nowait(None)
            except:
                pass
        
        if self._writer_task and not self._writer_task.done():
            self._writer_task.cancel()


# Global audit instance
_audit: SecurityAudit | None = None


def get_audit() -> SecurityAudit:
    """Get the global security audit instance."""
    global _audit
    if _audit is None:
        _audit = SecurityAudit()
    return _audit
