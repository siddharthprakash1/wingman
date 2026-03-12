#!/usr/bin/env python3
"""
Run the Wingman Discord Bot Swarm.

This script starts all 10 bots and keeps them running until you press Ctrl+C.
Shows verbose backend logging so you can see what's happening.

Usage:
    python run_swarm.py
"""

import asyncio
import signal
import sys
import logging
from datetime import datetime

from src.swarm.manager import SwarmManager, SwarmConfig
from src.config.settings import load_settings

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)

# Reduce noise from some libraries
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('discord').setLevel(logging.WARNING)
logging.getLogger('primp').setLevel(logging.WARNING)


def main():
    stop_event = asyncio.Event()

    def signal_handler(sig, frame):
        print("\n⏹️  Stopping swarm...")
        stop_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    async def run_swarm():
        settings = load_settings()
        config = SwarmConfig(settings)
        config.load_from_dict(settings.swarm.model_dump())

        print()
        print("=" * 70)
        print("🐝 WINGMAN DISCORD BOT SWARM - VERBOSE MODE")
        print("=" * 70)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Model: {settings.agents.defaults.model}")
        print(f"Bots: {len(config.configured_bots)}")
        print(f"Sync Channel: {config.sync_channel_id}")
        print(f"Daily Sync Time: {config.sync_time}")
        print("=" * 70)
        print()
        print("📋 VERBOSE LOGGING ENABLED - You'll see:")
        print("   - When bots receive messages")
        print("   - Tool calls (web_search, etc.)")
        print("   - LLM responses")
        print("   - Errors and issues")
        print()

        manager = SwarmManager(config)
        await manager.start()

        # Wait for bots to connect
        await asyncio.sleep(10)

        print()
        print("✅ ALL BOTS CONNECTED!")
        print()
        status = manager.get_status()
        for role, info in status['bots'].items():
            emoji = info.get('emoji', '?')
            name = info.get('name', role)
            user = info.get('discord_user') or 'connecting...'
            print(f"   {emoji} {name}: {user}")
        print()
        print("-" * 70)
        print("TEST COMMANDS:")
        print("   📡 @Pulse - AI news         💡 @Spark - Brainstorm ideas")
        print("   🔬 @Scout - Research        📊 @Analyst - Score ideas")
        print("   🏗️ @Blueprint - Design      💻 @Builder - Build code")
        print("   🧪 @Validator - Test        🚀 @Deploy - DevOps")
        print("   📝 @Scribe - Documentation  🧠 @Chief - Coordinator")
        print()
        print("SLASH COMMANDS:")
        print("   /trends, /digest, /research, /brainstorm, /innovate")
        print("   /design, /build, /test, /setup, /deploy, /score, /sync")
        print("-" * 70)
        print()
        print("🎯 Press Ctrl+C to stop the swarm")
        print()
        print("=" * 70)
        print("BACKEND LOGS (watch for bot activity):")
        print("=" * 70)
        print()

        # Wait until stop signal
        await stop_event.wait()

        print()
        print("Stopping bots...")
        await manager.stop()
        print("👋 Swarm stopped. Goodbye!")

    asyncio.run(run_swarm())


if __name__ == "__main__":
    main()
