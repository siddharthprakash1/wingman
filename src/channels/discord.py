"""
Discord Channel — connect the agent to Discord.

Listens for messages mentioning the bot and routes them
through the agent loop.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.config.settings import Settings

logger = logging.getLogger(__name__)


async def start_discord_bot(settings: "Settings") -> None:
    """
    Start the Discord bot.

    Requires discord.py and a valid bot token
    configured in settings.channels.discord.token.
    """
    try:
        import discord
        from discord.ext import commands
    except ImportError:
        logger.error(
            "discord.py not installed. "
            "Install with: pip install discord.py"
        )
        return

    token = settings.channels.discord.token
    if not token:
        logger.warning("Discord bot token not configured")
        return

    from src.agent.loop import AgentSession

    # One session per channel+user combo
    sessions: dict[str, AgentSession] = {}

    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        logger.info(f"Discord bot connected as {bot.user}")

    @bot.event
    async def on_message(message: discord.Message):
        if message.author == bot.user:
            return

        # Only respond to mentions or DMs
        if not (
            bot.user.mentioned_in(message) or
            isinstance(message.channel, discord.DMChannel)
        ):
            return

        # Remove the mention from the text
        text = message.content
        if bot.user:
            text = text.replace(f"<@{bot.user.id}>", "").strip()
            text = text.replace(f"<@!{bot.user.id}>", "").strip()

        if not text:
            return

        # Get or create session
        session_key = f"discord:{message.channel.id}:{message.author.id}"
        if session_key not in sessions:
            sessions[session_key] = AgentSession(
                session_id=session_key,
                settings=settings,
            )

        session = sessions[session_key]

        try:
            async with message.channel.typing():
                response = await session.process_message(text, channel="discord")

            # Split long messages (Discord limit: 2000 chars)
            if len(response) <= 2000:
                await message.reply(response)
            else:
                for i in range(0, len(response), 2000):
                    if i == 0:
                        await message.reply(response[i:i + 2000])
                    else:
                        await message.channel.send(response[i:i + 2000])

        except Exception as e:
            logger.error(f"Discord handler error: {e}")
            await message.reply(f"❌ Error: {e}")

    logger.info("Discord bot starting...")
    await bot.start(token)
