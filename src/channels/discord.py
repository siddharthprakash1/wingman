"""
Discord Channel - connect the agent to Discord.

Supports slash commands, rich embeds, and interactive components
for an enhanced Discord bot experience.
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

    # Slash command: /ask
    @bot.tree.command(name="ask", description="Ask Wingman AI a question")
    async def ask_command(interaction: discord.Interaction, question: str):
        """Slash command for asking questions."""
        await interaction.response.defer()

        session_key = f"discord:{interaction.channel_id}:{interaction.user.id}"
        if session_key not in sessions:
            sessions[session_key] = AgentSession(
                session_id=session_key,
                settings=settings,
            )

        session = sessions[session_key]

        try:
            response = await session.process_message(question, channel="discord")

            embed = discord.Embed(
                description=response[:4096],
                color=discord.Color.blue()
            )
            embed.set_author(
                name="Wingman AI",
                icon_url=bot.user.avatar.url if bot.user.avatar else None
            )
            embed.set_footer(text=f"Requested by {interaction.user.name}")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Discord slash command error: {e}")
            await interaction.followup.send(f"Error: {e}")

    # Slash command: /help
    @bot.tree.command(name="help", description="Show Wingman AI help")
    async def help_command(interaction: discord.Interaction):
        """Show bot help information."""
        embed = discord.Embed(
            title="Wingman AI Help",
            description="I'm Wingman, your AI assistant!",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Commands",
            value="`/ask <question>` - Ask a question\n`/help` - Show this help",
            inline=False
        )
        embed.set_footer(text="Powered by Wingman AI")
        await interaction.response.send_message(embed=embed)

    @bot.event
    async def on_ready():
        logger.info(f"Discord bot connected as {bot.user}")
        try:
            synced = await bot.tree.sync()
            logger.info(f"Synced {len(synced)} slash command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

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

        text = message.content
        if bot.user:
            text = text.replace(f"<@{bot.user.id}>", "").strip()
            text = text.replace(f"<@!{bot.user.id}>", "").strip()

        if not text:
            return

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
            await message.reply(f"Error: {e}")

    logger.info("Discord bot starting...")
    await bot.start(token)
