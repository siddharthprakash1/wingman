"""
Swarm Manager — Lifecycle management for the multi-bot Discord swarm.

Handles:
- Starting/stopping all bots
- Scheduling daily sync-ups via the heartbeat system
- Shared memory management
- Bot-to-bot communication
- Integration with the gateway and CLI
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, TYPE_CHECKING

from src.config.settings import Settings, get_settings
from src.core.heartbeat import HeartbeatSystem, HeartbeatInterval, get_heartbeat
from src.swarm.bots import (
    BotRole, BotPersonality, SwarmBot, PERSONALITIES,
)
from src.swarm.sync import DailySyncOrchestrator

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Default shared memory directory
DEFAULT_SWARM_DIR = Path.home() / ".wingman" / "swarm"


class SwarmConfig:
    """Configuration for the bot swarm, loaded from settings or env."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._load_from_settings()

    def _load_from_settings(self) -> None:
        """Load swarm config from settings."""
        # Bot tokens come from the swarm config section
        swarm_cfg = getattr(self.settings, "_swarm_config", None)

        self.enabled: bool = False
        self.sync_channel_id: int = 0
        self.sync_time: str = "09:00"  # HH:MM in 24h format
        self.swarm_dir: Path = DEFAULT_SWARM_DIR

        # Token mapping: role -> discord bot token
        self.tokens: dict[str, str] = {
            # Original core team
            "research": "",
            "engineer": "",
            "writer": "",
            "data": "",
            "coordinator": "",
            # New specialized agents
            "trend_watcher": "",
            "architect": "",
            "tester": "",
            "devops": "",
            "innovator": "",
        }

    def load_from_dict(self, data: dict[str, Any]) -> None:
        """Load configuration from a dictionary."""
        self.enabled = data.get("enabled", False)
        self.sync_channel_id = int(data.get("sync_channel_id", 0))
        self.sync_time = data.get("sync_time", "09:00")
        if "swarm_dir" in data:
            self.swarm_dir = Path(data["swarm_dir"]).expanduser()
        tokens = data.get("tokens", {})
        for role in self.tokens:
            if role in tokens:
                self.tokens[role] = tokens[role]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "enabled": self.enabled,
            "sync_channel_id": self.sync_channel_id,
            "sync_time": self.sync_time,
            "swarm_dir": str(self.swarm_dir),
            "tokens": self.tokens,
        }

    @property
    def configured_bots(self) -> list[str]:
        """List roles that have tokens configured."""
        return [role for role, token in self.tokens.items() if token]


class SwarmManager:
    """
    Manages the full lifecycle of the Discord bot swarm.

    Usage:
        manager = SwarmManager(config)
        await manager.start()      # Start all bots
        await manager.trigger_sync()  # Manual sync
        await manager.stop()       # Graceful shutdown
    """

    def __init__(self, config: SwarmConfig):
        self.config = config
        self.settings = config.settings
        self.swarm_dir = config.swarm_dir

        # Ensure shared directories
        self.swarm_dir.mkdir(parents=True, exist_ok=True)

        # Bot instances
        self.bots: dict[str, SwarmBot] = {}

        # Sync orchestrator (initialized after bots start)
        self.sync_orchestrator: DailySyncOrchestrator | None = None

        # Bot tasks (asyncio)
        self._bot_tasks: dict[str, asyncio.Task] = {}
        self._running = False

        # Initialize bots from config
        self._init_bots()

    def _init_bots(self) -> None:
        """Create SwarmBot instances for each configured role."""
        for role_str, token in self.config.tokens.items():
            if not token:
                logger.debug(f"Skipping {role_str} bot (no token)")
                continue

            try:
                role = BotRole(role_str)
            except ValueError:
                logger.warning(f"Unknown bot role: {role_str}")
                continue

            personality = PERSONALITIES.get(role)
            if not personality:
                logger.warning(f"No personality defined for role: {role_str}")
                continue

            bot = SwarmBot(
                personality=personality,
                token=token,
                settings=self.settings,
                swarm_dir=self.swarm_dir,
                sync_channel_id=self.config.sync_channel_id,
            )
            self.bots[role_str] = bot
            logger.info(f"Initialized swarm bot: {personality.emoji} {personality.name} ({role_str})")

    async def start(self) -> None:
        """Start all configured bots and schedule the daily sync."""
        if self._running:
            logger.warning("Swarm already running")
            return

        if not self.bots:
            logger.warning("No bots configured. Add tokens to swarm config.")
            return

        self._running = True
        logger.info(f"Starting swarm with {len(self.bots)} bots: {list(self.bots.keys())}")

        # Start each bot in its own task
        for role, bot in self.bots.items():
            task = asyncio.create_task(
                self._run_bot_with_restart(role, bot),
                name=f"swarm-{role}",
            )
            self._bot_tasks[role] = task

        # Wait a bit for bots to connect
        await asyncio.sleep(5)

        # Initialize sync orchestrator
        if self.config.sync_channel_id:
            self.sync_orchestrator = DailySyncOrchestrator(
                bots=self.bots,
                sync_channel_id=self.config.sync_channel_id,
                swarm_dir=self.swarm_dir,
            )

            # Register daily sync as a heartbeat task
            self._schedule_daily_sync()

        logger.info("Swarm fully started")

    async def _run_bot_with_restart(self, role: str, bot: SwarmBot) -> None:
        """Run a bot with automatic restart on failure."""
        max_retries = 5
        retry_delay = 10

        for attempt in range(max_retries):
            try:
                await bot.start()
            except Exception as e:
                if not self._running:
                    return  # Intentional shutdown
                logger.error(
                    f"Bot {role} crashed (attempt {attempt + 1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    delay = retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Restarting {role} bot in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Bot {role} failed after {max_retries} attempts")

    def _schedule_daily_sync(self) -> None:
        """Schedule the daily sync-up using the heartbeat system."""
        heartbeat = get_heartbeat()

        async def daily_sync_task():
            """Check if it's time for the daily sync."""
            now = datetime.now()
            target_time = self.config.sync_time.split(":")
            target_hour = int(target_time[0])
            target_minute = int(target_time[1]) if len(target_time) > 1 else 0

            # Check if we're within 5 minutes of the target time
            if now.hour == target_hour and abs(now.minute - target_minute) <= 5:
                # Check if we already synced today
                last_sync = self.sync_orchestrator.get_last_sync() if self.sync_orchestrator else None
                if last_sync and last_sync["date"] == now.strftime("%Y-%m-%d"):
                    return  # Already synced today

                logger.info("Daily sync time! Starting sync-up...")
                await self.trigger_sync()

        heartbeat.register_task(
            name="swarm_daily_sync",
            func=daily_sync_task,
            interval=HeartbeatInterval.SLOW,  # Check every 5 minutes
            enabled=True,
        )

        if not heartbeat._running:
            heartbeat.start()

        logger.info(f"Daily sync scheduled for {self.config.sync_time}")

    async def trigger_sync(self) -> dict[str, Any]:
        """Manually trigger a sync-up meeting."""
        if not self.sync_orchestrator:
            return {"status": "error", "reason": "No sync orchestrator (missing sync_channel_id)"}
        return await self.sync_orchestrator.run_sync()

    async def stop(self) -> None:
        """Gracefully stop all bots."""
        self._running = False
        logger.info("Stopping swarm...")

        # Stop all bots
        for role, bot in self.bots.items():
            try:
                await bot.stop()
            except Exception as e:
                logger.error(f"Error stopping {role} bot: {e}")

        # Cancel all tasks
        for role, task in self._bot_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self._bot_tasks.clear()
        logger.info("Swarm stopped")

    async def ask_bot(self, role: str, question: str, context: str = "") -> str:
        """Ask a specific bot a question programmatically."""
        bot = self.bots.get(role)
        if not bot:
            return f"❌ No bot with role '{role}'. Available: {list(self.bots.keys())}"
        return await bot.ask(question, context)

    def get_status(self) -> dict[str, Any]:
        """Get the status of all bots in the swarm."""
        status = {
            "running": self._running,
            "swarm_dir": str(self.swarm_dir),
            "sync_channel_id": self.config.sync_channel_id,
            "sync_time": self.config.sync_time,
            "bots": {},
        }

        for role, bot in self.bots.items():
            p = bot.personality
            status["bots"][role] = {
                "name": p.name,
                "emoji": p.emoji,
                "running": bot.is_running,
                "discord_user": str(bot.bot_user) if bot.bot_user else None,
            }

        # Last sync info
        if self.sync_orchestrator:
            last = self.sync_orchestrator.get_last_sync()
            status["last_sync"] = last["date"] if last else None
        else:
            status["last_sync"] = None

        return status

    def list_recent_syncs(self, limit: int = 10) -> list[dict[str, str]]:
        """List recent sync summaries."""
        if not self.sync_orchestrator:
            return []
        return self.sync_orchestrator.list_syncs(limit)


# ---------------------------------------------------------------------------
# Global instance
# ---------------------------------------------------------------------------

_swarm_manager: SwarmManager | None = None


def get_swarm_manager() -> SwarmManager | None:
    """Get the global swarm manager instance."""
    return _swarm_manager


def create_swarm_manager(config: SwarmConfig) -> SwarmManager:
    """Create and set the global swarm manager."""
    global _swarm_manager
    _swarm_manager = SwarmManager(config)
    return _swarm_manager
