"""
Telegram Channel — connect the agent to Telegram.

Listens for messages on Telegram and routes them
through the agent loop.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.config.settings import Settings

logger = logging.getLogger(__name__)


async def start_telegram_bot(settings: "Settings") -> None:
    """
    Start the Telegram bot.

    Requires python-telegram-bot and a valid bot token
    configured in settings.channels.telegram.token.
    """
    try:
        from telegram import Update
        from telegram.ext import (
            Application,
            CommandHandler,
            MessageHandler,
            filters,
        )
    except ImportError:
        logger.error(
            "python-telegram-bot not installed. "
            "Install with: pip install python-telegram-bot"
        )
        return

    token = settings.channels.telegram.token
    if not token:
        logger.warning("Telegram bot token not configured")
        return

    from src.agent.loop import AgentSession

    # One session per user
    sessions: dict[int, AgentSession] = {}

    async def handle_start(update: Update, context):
        """Handle /start command."""
        await update.message.reply_text(
            "🦞 *OpenClaw Mine* — Your personal AI assistant!\n\n"
            "Send me a message and I'll help you out.",
            parse_mode="Markdown",
        )

    async def handle_message(update: Update, context):
        """Handle incoming messages."""
        user_id = update.effective_user.id
        text = update.message.text

        if not text:
            return

        # Get or create session
        if user_id not in sessions:
            sessions[user_id] = AgentSession(
                session_id=f"telegram:{user_id}",
                settings=settings,
            )

        session = sessions[user_id]

        try:
            # Show typing indicator
            await update.message.chat.send_action("typing")

            response = await session.process_message(text, channel="telegram")

            # Split long messages (Telegram limit: 4096 chars)
            if len(response) <= 4096:
                await update.message.reply_text(response)
            else:
                for i in range(0, len(response), 4096):
                    await update.message.reply_text(response[i:i + 4096])

        except Exception as e:
            logger.error(f"Telegram handler error: {e}")
            await update.message.reply_text(f"❌ Error: {e}")

    # Build and run the bot
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", handle_start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Telegram bot starting...")
    await application.run_polling()
