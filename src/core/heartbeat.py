"""
Autonomous Heartbeat System (inspired by PicoClaw).

Enables background task execution with configurable intervals for:
- Periodic memory consolidation
- Scheduled reminders and notifications
- Background data synchronization
- Health monitoring and auto-recovery
- Autonomous agent behaviors
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)


class HeartbeatInterval(str, Enum):
    """Predefined heartbeat intervals."""
    FAST = "fast"        # 5 seconds
    NORMAL = "normal"     # 30 seconds
    SLOW = "slow"        # 5 minutes
    HOURLY = "hourly"    # 1 hour
    DAILY = "daily"      # 24 hours
    CUSTOM = "custom"    # Custom interval


# Interval mapping to seconds
INTERVAL_SECONDS = {
    HeartbeatInterval.FAST: 5,
    HeartbeatInterval.NORMAL: 30,
    HeartbeatInterval.SLOW: 300,
    HeartbeatInterval.HOURLY: 3600,
    HeartbeatInterval.DAILY: 86400,
}


@dataclass
class HeartbeatTask:
    """A scheduled background task."""
    
    name: str
    interval: HeartbeatInterval | int  # Enum or custom seconds
    func: Callable[[], Coroutine[Any, Any, None]]
    enabled: bool = True
    last_run: datetime | None = None
    next_run: datetime | None = None
    run_count: int = 0
    error_count: int = 0
    last_error: str | None = None
    
    def get_interval_seconds(self) -> int:
        """Get interval in seconds."""
        if isinstance(self.interval, int):
            return self.interval
        return INTERVAL_SECONDS.get(self.interval, 30)
    
    def should_run(self) -> bool:
        """Check if task should run now."""
        if not self.enabled:
            return False
        if self.next_run is None:
            return True
        return datetime.now() >= self.next_run
    
    def schedule_next(self) -> None:
        """Schedule the next run."""
        interval = self.get_interval_seconds()
        self.next_run = datetime.now() + timedelta(seconds=interval)


class HeartbeatSystem:
    """
    Autonomous heartbeat system for background task execution.
    
    Manages periodic tasks with configurable intervals, error handling,
    and graceful shutdown.
    """
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.tasks: dict[str, HeartbeatTask] = {}
        self._worker_task: asyncio.Task | None = None
        self._running = False
    
    def register_task(
        self,
        name: str,
        func: Callable[[], Coroutine[Any, Any, None]],
        interval: HeartbeatInterval | int = HeartbeatInterval.NORMAL,
        enabled: bool = True,
    ) -> None:
        """Register a background task."""
        task = HeartbeatTask(
            name=name,
            interval=interval,
            func=func,
            enabled=enabled,
        )
        task.schedule_next()
        self.tasks[name] = task
        logger.info(f"Registered heartbeat task: {name} ({interval})")
    
    def unregister_task(self, name: str) -> None:
        """Unregister a task."""
        if name in self.tasks:
            del self.tasks[name]
            logger.info(f"Unregistered heartbeat task: {name}")
    
    def enable_task(self, name: str) -> None:
        """Enable a task."""
        if name in self.tasks:
            self.tasks[name].enabled = True
    
    def disable_task(self, name: str) -> None:
        """Disable a task."""
        if name in self.tasks:
            self.tasks[name].enabled = False
    
    async def _run_task(self, task: HeartbeatTask) -> None:
        """Execute a single task with error handling."""
        try:
            logger.debug(f"Running heartbeat task: {task.name}")
            await task.func()
            task.last_run = datetime.now()
            task.run_count += 1
            task.schedule_next()
        except Exception as e:
            task.error_count += 1
            task.last_error = str(e)
            logger.error(f"Heartbeat task {task.name} failed: {e}")
            task.schedule_next()
    
    async def _worker(self) -> None:
        """Main worker loop that executes tasks."""
        logger.info("Heartbeat system started")
        while self._running:
            try:
                tasks_to_run = [
                    task for task in self.tasks.values()
                    if task.should_run()
                ]
                if tasks_to_run:
                    await asyncio.gather(*[
                        self._run_task(task) for task in tasks_to_run
                    ])
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat worker error: {e}")
                await asyncio.sleep(5)
        logger.info("Heartbeat system stopped")
    
    def start(self) -> None:
        """Start the heartbeat system."""
        if not self.enabled:
            logger.info("Heartbeat system disabled by configuration")
            return
        if self._running:
            logger.warning("Heartbeat system already running")
            return
        self._running = True
        try:
            loop = asyncio.get_event_loop()
            self._worker_task = loop.create_task(self._worker())
        except RuntimeError:
            logger.error("No event loop available for heartbeat system")
    
    def stop(self) -> None:
        """Stop the heartbeat system."""
        self._running = False
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
    
    def get_status(self) -> dict[str, Any]:
        """Get system status and task information."""
        return {
            "enabled": self.enabled,
            "running": self._running,
            "task_count": len(self.tasks),
            "tasks": {
                name: {
                    "enabled": task.enabled,
                    "interval": str(task.interval),
                    "run_count": task.run_count,
                    "error_count": task.error_count,
                    "last_run": task.last_run.isoformat() if task.last_run else None,
                    "next_run": task.next_run.isoformat() if task.next_run else None,
                    "last_error": task.last_error,
                }
                for name, task in self.tasks.items()
            },
        }


# Global heartbeat instance
_heartbeat: HeartbeatSystem | None = None


def get_heartbeat() -> HeartbeatSystem:
    """Get the global heartbeat system instance."""
    global _heartbeat
    if _heartbeat is None:
        _heartbeat = HeartbeatSystem()
    return _heartbeat


async def memory_consolidation_task() -> None:
    """Periodically consolidate memory and optimize vector store."""
    logger.debug("Running memory consolidation task")


async def health_check_task() -> None:
    """Check system health and provider availability."""
    logger.debug("Running health check task")


async def session_cleanup_task() -> None:
    """Clean up expired sessions."""
    from src.core.session import SessionManager
    logger.debug("Running session cleanup task")
    manager = SessionManager()
    manager.cleanup_expired_sessions()


def register_default_tasks(heartbeat: HeartbeatSystem) -> None:
    """Register default background tasks."""
    heartbeat.register_task(
        name="session_cleanup",
        func=session_cleanup_task,
        interval=HeartbeatInterval.SLOW,
    )
    heartbeat.register_task(
        name="memory_consolidation",
        func=memory_consolidation_task,
        interval=HeartbeatInterval.HOURLY,
        enabled=False,
    )
    heartbeat.register_task(
        name="health_check",
        func=health_check_task,
        interval=HeartbeatInterval.SLOW,
        enabled=False,
    )
