#!/usr/bin/env python3
"""
Overnight launcher — two modes.

Default mode (LiveRoom): real-time collaborative conversation between the
10 persona bots in the Discord sync channel. A moderator LLM picks who
speaks next each turn; each bot responds in-persona via its own Discord
identity and can call tools (web_search, files, etc.) as it replies.

Brief mode (--brief): the Night Lab pipeline. One polished Morning Brief
per cycle, written to ~/.wingman/briefs/<date>.md. No Discord needed.

Usage:
    python run_overnight.py                 # LiveRoom, rounds forever
    python run_overnight.py --once          # one LiveRoom round and exit
    python run_overnight.py --turns 6       # shorter rounds (default 12)
    python run_overnight.py --rest 10       # rest minutes between rounds

    python run_overnight.py --brief         # Night Lab pipeline forever
    python run_overnight.py --brief --once  # one Night Lab cycle
    python run_overnight.py --brief --theme "Edge inference"

Stop with Ctrl+C.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from datetime import datetime

from src.config.settings import load_settings
from src.swarm.live_room import LiveRoom
from src.swarm.manager import SwarmConfig, SwarmManager
from src.swarm.night_lab import NightLab

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("discord").setLevel(logging.WARNING)
logging.getLogger("primp").setLevel(logging.WARNING)

log = logging.getLogger("overnight")


# ---------------------------------------------------------------------------
# Night Lab mode (pipeline → Morning Brief file)
# ---------------------------------------------------------------------------

def _brief_banner(settings) -> None:
    cfg = settings.overnight
    log.info("=" * 60)
    log.info("NIGHT LAB — overnight idea pipeline")
    log.info("=" * 60)
    log.info("Started  : %s", datetime.now().isoformat(timespec="seconds"))
    log.info("Provider : %s", cfg.provider)
    log.info("Model    : %s", cfg.model)
    log.info("Interval : %s min", cfg.cycle_minutes)
    log.info("Themes   : %s", ", ".join(cfg.themes))
    log.info("Output   : ~/.wingman/briefs/<date>.md")
    log.info("=" * 60)


async def _run_brief(once: bool, theme: str | None) -> None:
    settings = load_settings()
    _brief_banner(settings)

    lab = NightLab(settings=settings)
    if once:
        path = await lab.run_cycle(theme=theme)
        log.info("One-shot cycle complete → %s", path)
        return
    await lab.run_forever()


# ---------------------------------------------------------------------------
# LiveRoom mode (real-time Discord conversation)
# ---------------------------------------------------------------------------

def _live_banner(config: SwarmConfig, turns: int, rest: int, once: bool) -> None:
    log.info("=" * 60)
    log.info("LIVE ROOM — real-time persona conversation in Discord")
    log.info("=" * 60)
    log.info("Started     : %s", datetime.now().isoformat(timespec="seconds"))
    log.info("Bots        : %d configured", len(config.configured_bots))
    log.info("Channel     : %s", config.sync_channel_id or "(not set)")
    log.info("Turns/round : %d", turns)
    log.info("Rest (min)  : %d", rest)
    log.info("Mode        : %s", "one-shot round" if once else "forever")
    log.info("=" * 60)


async def _run_live(once: bool, turns: int, rest: int) -> None:
    settings = load_settings()
    config = SwarmConfig(settings)
    config.load_from_dict(settings.swarm.model_dump())

    if not config.configured_bots:
        log.error("No Discord tokens configured in settings.swarm.tokens — can't start LiveRoom.")
        log.error("Fall back: python run_overnight.py --brief")
        return
    if not config.sync_channel_id:
        log.error("settings.swarm.sync_channel_id is 0 — set it to your Discord channel ID.")
        return

    _live_banner(config, turns, rest, once)

    manager = SwarmManager(config)
    await manager.start()

    # Wait for Discord connections to stabilize before the moderator asks anyone to speak
    log.info("Waiting 10s for bots to connect to Discord...")
    await asyncio.sleep(10)

    connected = [role for role, bot in manager.bots.items() if bot._bot is not None]
    log.info("Connected bots: %s", connected or "(none)")
    if not connected:
        log.error("No bots connected — aborting LiveRoom.")
        await manager.stop()
        return

    room = LiveRoom(manager=manager, channel_id=config.sync_channel_id, settings=settings)

    try:
        if once:
            await room.run_round(turns=turns)
        else:
            await room.run_forever(turns_per_round=turns, rest_minutes=rest)
    except KeyboardInterrupt:
        log.info("Interrupted — stopping room.")
        room.stop()
    finally:
        log.info("Stopping swarm manager...")
        await manager.stop()
        log.info("Done.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Wingman overnight — LiveRoom (default) or Night Lab pipeline."
    )
    parser.add_argument(
        "--brief",
        action="store_true",
        help="Run the Night Lab pipeline instead of the live Discord room.",
    )
    parser.add_argument("--once", action="store_true", help="Run a single round/cycle and exit")
    # LiveRoom-only
    parser.add_argument("--turns", type=int, default=12, help="Turns per round (LiveRoom)")
    parser.add_argument("--rest", type=int, default=15, help="Rest minutes between rounds (LiveRoom)")
    # Night Lab-only
    parser.add_argument("--theme", type=str, default=None, help="Force a specific theme (--brief)")
    args = parser.parse_args()

    try:
        if args.brief:
            asyncio.run(_run_brief(once=args.once, theme=args.theme))
        else:
            asyncio.run(_run_live(once=args.once, turns=args.turns, rest=args.rest))
    except KeyboardInterrupt:
        log.info("Interrupted — goodnight.")


if __name__ == "__main__":
    main()
