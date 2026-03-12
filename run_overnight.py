#!/usr/bin/env python3
"""
Overnight Swarm Runner - Bots actively discuss and work through the night.

Features:
- Periodic activity cycles where bots research and share findings
- Natural conversation flow in the sync channel
- Automatic daily sync at configured time
- Continuous operation until Ctrl+C

Usage:
    python run_overnight.py
"""

import asyncio
import signal
import random
import logging
from datetime import datetime, timedelta
from pathlib import Path

from src.swarm.manager import SwarmManager, SwarmConfig
from src.config.settings import load_settings

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(message)s',
    datefmt='%H:%M:%S'
)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('discord').setLevel(logging.WARNING)
logging.getLogger('primp').setLevel(logging.WARNING)

# Activity prompts for each bot - what they do during work cycles
ACTIVITY_PROMPTS = {
    "trend_watcher": [
        "Search for the latest AI news that happened in the last few hours. Share your top 3 findings with the team. Use web_search and report what you actually find.",
        "Look for any breaking news about OpenAI, Anthropic, Google AI, or Meta AI. Share anything interesting you find.",
        "Search for trending AI discussions on Hacker News or Reddit today. What are developers talking about?",
        "Find any new AI model releases or updates from the past 24 hours. Report your findings.",
    ],
    "research": [
        "Search for interesting open source AI projects that are trending on GitHub. Find repos with recent activity and share them.",
        "Look for new research papers on arxiv about LLMs, agents, or RAG systems. Summarize what you find.",
        "Research practical implementations of AI agents. Find tutorials or code examples.",
        "Search for AI tools that could help our team be more productive. What's new?",
    ],
    "innovator": [
        "Based on recent AI trends, brainstorm 3 project ideas we could build this week. Make them specific and actionable.",
        "Think about gaps in the current AI tooling ecosystem. What's missing that we could build?",
        "Come up with a creative project idea that combines two recent AI trends.",
        "Propose an unconventional AI project that most people aren't thinking about.",
    ],
    "data": [
        "Review the ideas shared by other bots in this channel recently. Score the most promising one using FIRE framework (Feasibility, Impact, Risk, Effort).",
        "Analyze what types of AI projects are getting the most attention lately. What does the data suggest we should focus on?",
        "Evaluate the market opportunity for AI agent frameworks. What's the competitive landscape?",
    ],
    "architect": [
        "For any promising project ideas discussed, sketch out a high-level architecture. What components would we need?",
        "Review the technical feasibility of recent proposals. What are the implementation challenges?",
        "Design a simple system architecture for an AI-powered tool. Keep it minimal but complete.",
    ],
    "engineer": [
        "Check our projects directory for any ongoing work. Report status and what needs to be done next.",
        "Review code or implementations shared by the team. Provide technical feedback.",
        "Propose a quick prototype we could build today based on the team's discussions.",
    ],
    "tester": [
        "Think about testing strategies for AI applications. What edge cases should we always check?",
        "Review any proposed projects from a QA perspective. What could go wrong?",
        "Share best practices for testing LLM-based applications.",
    ],
    "devops": [
        "Propose a standard project setup for our AI projects. What should every repo have?",
        "Review deployment considerations for AI applications. What infrastructure do we need?",
        "Share tips on containerizing Python AI applications efficiently.",
    ],
    "writer": [
        "Summarize the team's recent discussions and findings. Create a brief digest.",
        "Document any decisions or insights from the team's work.",
        "Write a brief update on what the team has accomplished in the last few hours.",
    ],
    "coordinator": [
        "Review what the team has discussed and researched. Identify the most promising direction.",
        "Assign priorities based on the team's findings. What should we focus on?",
        "Check in on the team's progress. Who needs support?",
    ],
}

# Conversation starters to make it feel natural
CONVERSATION_STARTERS = [
    "Hey team, I've been looking into something interesting...",
    "Just found something you all should see...",
    "Quick update from my research...",
    "I've been thinking about our next project...",
    "Here's what I discovered...",
    "Wanted to share this with everyone...",
    "This might be relevant to what we're working on...",
]


class OvernightRunner:
    def __init__(self, manager: SwarmManager, channel_id: int):
        self.manager = manager
        self.channel_id = channel_id
        self.running = True
        self.activity_count = 0
        
    async def send_to_channel(self, bot_role: str, message: str):
        """Send a message to the sync channel from a specific bot."""
        bot = self.manager.bots.get(bot_role)
        if bot and bot._bot:
            try:
                await bot.send_to_channel(self.channel_id, message)
                print(f"   📤 {bot.personality.emoji} {bot.personality.name} posted to channel")
            except Exception as e:
                print(f"   ❌ Failed to send: {e}")
    
    async def bot_activity(self, bot_role: str):
        """Have a bot do some activity and share findings."""
        bot = self.manager.bots.get(bot_role)
        if not bot:
            return
            
        prompts = ACTIVITY_PROMPTS.get(bot_role, [])
        if not prompts:
            return
            
        prompt = random.choice(prompts)
        starter = random.choice(CONVERSATION_STARTERS)
        
        print(f"\n{'='*60}")
        print(f"🤖 {bot.personality.emoji} {bot.personality.name} - Activity Cycle")
        print(f"{'='*60}")
        print(f"📋 Task: {prompt[:80]}...")
        
        try:
            # Get the bot to do the activity
            response = await bot.ask(prompt, context="Overnight work cycle - share findings with team")
            
            if response and len(response) > 50:
                # Format and send to channel
                channel_message = f"**{bot.personality.emoji} {bot.personality.name}**\n\n{response[:1900]}"
                await self.send_to_channel(bot_role, channel_message)
                self.activity_count += 1
                
                # Save to swarm directory
                await self._save_activity(bot_role, prompt, response)
                
        except Exception as e:
            print(f"   ❌ Activity failed: {e}")
    
    async def _save_activity(self, bot_role: str, prompt: str, response: str):
        """Save bot activity to their directory."""
        dirs = {
            "trend_watcher": "trends",
            "research": "research", 
            "innovator": "ideas",
            "data": "analysis",
            "architect": "architecture",
            "engineer": "projects",
            "tester": "tests",
            "devops": "devops",
            "writer": "docs",
            "coordinator": "decisions",
        }
        
        subdir = dirs.get(bot_role, bot_role)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filepath = Path.home() / ".wingman" / "swarm" / subdir / f"activity_{timestamp}.md"
        
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            content = f"# Activity Log - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            content += f"**Prompt:** {prompt}\n\n"
            content += f"**Response:**\n{response}\n"
            filepath.write_text(content)
            print(f"   💾 Saved to {filepath.name}")
        except Exception as e:
            print(f"   ⚠️ Save failed: {e}")

    async def run_activity_cycle(self):
        """Run one activity cycle with multiple bots."""
        print(f"\n{'#'*60}")
        print(f"# ACTIVITY CYCLE - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'#'*60}")
        
        # Select 2-4 random bots for this cycle
        active_bots = random.sample(
            list(self.manager.bots.keys()), 
            min(random.randint(2, 4), len(self.manager.bots))
        )
        
        print(f"Active bots this cycle: {active_bots}")
        
        for bot_role in active_bots:
            await self.bot_activity(bot_role)
            # Wait between bot activities for natural feel
            await asyncio.sleep(random.randint(30, 90))
        
        print(f"\n✅ Cycle complete. Total activities: {self.activity_count}")

    async def opening_message(self):
        """Send opening message when bots start working."""
        coordinator = self.manager.bots.get("coordinator")
        if coordinator:
            message = f"""**🧠 Chief - Night Shift Started**

Hey team, I'm kicking off our overnight work session.

📋 **Tonight's Objectives:**
• Pulse: Monitor AI news and trends
• Scout: Deep dive research on promising topics
• Spark: Generate fresh project ideas
• Analyst: Evaluate and score ideas
• Builder: Check ongoing projects
• Everyone: Share interesting findings here

I'll coordinate periodic check-ins throughout the night. Let's discover something great!

⏰ Full daily sync scheduled for 09:00

*Night shift started at {datetime.now().strftime('%H:%M')}*
"""
            await self.send_to_channel("coordinator", message)
            await asyncio.sleep(5)

    async def run(self):
        """Main overnight loop."""
        await self.opening_message()
        
        cycle_count = 0
        while self.running:
            try:
                # Run activity cycle every 20-40 minutes
                cycle_count += 1
                print(f"\n⏰ Starting cycle {cycle_count}...")
                
                await self.run_activity_cycle()
                
                # Wait before next cycle (20-40 minutes)
                wait_time = random.randint(20 * 60, 40 * 60)
                next_cycle = datetime.now() + timedelta(seconds=wait_time)
                print(f"\n💤 Next cycle at {next_cycle.strftime('%H:%M:%S')} ({wait_time//60} minutes)")
                
                # Check for daily sync time during wait
                for _ in range(wait_time // 30):  # Check every 30 seconds
                    if not self.running:
                        break
                    
                    now = datetime.now()
                    # Check if it's daily sync time (9:00 AM)
                    if now.hour == 9 and now.minute < 5:
                        print("\n🔔 Daily sync time! Triggering sync...")
                        await self.manager.trigger_sync()
                        await asyncio.sleep(300)  # Wait 5 min after sync
                    
                    await asyncio.sleep(30)
                    
            except Exception as e:
                print(f"❌ Cycle error: {e}")
                await asyncio.sleep(60)


async def main():
    stop_event = asyncio.Event()
    runner = None
    
    def signal_handler(sig, frame):
        print("\n⏹️ Stopping overnight session...")
        if runner:
            runner.running = False
        stop_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    settings = load_settings()
    config = SwarmConfig(settings)
    config.load_from_dict(settings.swarm.model_dump())
    
    print()
    print("=" * 70)
    print("🌙 WINGMAN OVERNIGHT SESSION")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Model: {settings.agents.defaults.model}")
    print(f"Bots: {len(config.configured_bots)}")
    print(f"Channel: {config.sync_channel_id}")
    print(f"Daily Sync: {config.sync_time}")
    print("=" * 70)
    print()
    print("🔄 Bots will:")
    print("   • Research and share findings every 20-40 minutes")
    print("   • Have natural discussions in Discord")
    print("   • Run full daily sync at 09:00")
    print("   • Save all work to ~/.wingman/swarm/")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 70)
    print()
    
    manager = SwarmManager(config)
    await manager.start()
    
    # Wait for bots to connect
    await asyncio.sleep(15)
    
    print()
    print("✅ ALL BOTS CONNECTED:")
    status = manager.get_status()
    for role, info in status['bots'].items():
        emoji = info.get('emoji', '?')
        name = info.get('name', role)
        print(f"   {emoji} {name}")
    print()
    print("=" * 70)
    print("OVERNIGHT SESSION ACTIVE - Watch Discord for activity")
    print("=" * 70)
    print()
    
    # Start overnight runner
    runner = OvernightRunner(manager, config.sync_channel_id)
    
    try:
        await runner.run()
    except asyncio.CancelledError:
        pass
    finally:
        print("\n📊 Session Summary:")
        print(f"   Total activities: {runner.activity_count}")
        print(f"   Session duration: {datetime.now().strftime('%H:%M')}")
        
        await manager.stop()
        print("👋 Overnight session ended. Goodnight!")


if __name__ == "__main__":
    asyncio.run(main())
