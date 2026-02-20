"""
Slack Channel — connect the agent to Slack workspaces.

Supports slash commands, interactive components, and threaded conversations
through the Slack Bolt framework.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.config.settings import Settings

logger = logging.getLogger(__name__)


async def start_slack_bot(settings: "Settings") -> None:
    """
    Start the Slack bot using Slack Bolt framework.
    
    Requires:
    - Slack bot token (SLACK_BOT_TOKEN)
    - Slack app token for Socket Mode (SLACK_APP_TOKEN)
    - Slack signing secret (SLACK_SIGNING_SECRET)
    
    Features:
    - Slash commands (/wingman, /ask)
    - Direct messages
    - App mentions (@WingmanBot)
    - Threaded conversations
    - Interactive components (buttons, menus)
    """
    try:
        from slack_bolt.async_app import AsyncApp
        from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
    except ImportError:
        logger.error(
            "Slack Bolt SDK not installed. "
            "Install with: pip install slack-bolt"
        )
        return
    
    bot_token = settings.channels.slack.bot_token
    app_token = settings.channels.slack.app_token
    
    if not all([bot_token, app_token]):
        logger.warning("Slack channel not fully configured")
        return
    
    # Initialize Slack app
    app = AsyncApp(token=bot_token)
    
    from src.agent.loop import AgentSession
    
    # Session management (user_id -> session)
    sessions: dict[str, AgentSession] = {}
    
    def get_session(user_id: str) -> AgentSession:
        """Get or create session for user."""
        if user_id not in sessions:
            sessions[user_id] = AgentSession(
                session_id=f"slack:{user_id}",
                settings=settings,
            )
        return sessions[user_id]
    
    # Slash command: /wingman
    @app.command("/wingman")
    async def handle_wingman_command(ack, command, say):
        """Handle /wingman slash command."""
        await ack()
        
        user_id = command["user_id"]
        text = command.get("text", "").strip()
        
        if not text:
            await say(
                "👋 Hi! I'm Wingman, your AI assistant.\n"
                "Use `/wingman <your message>` to chat with me!"
            )
            return
        
        session = get_session(user_id)
        
        try:
            # Show typing indicator
            response = await session.process_message(text, channel="slack")
            
            # Send response
            await say({
                "text": response,
                "response_type": "in_channel",  # Visible to everyone
            })
        
        except Exception as e:
            logger.error(f"Slack command error: {e}")
            await say(f"❌ Error: {e}")
    
    # App mentions: @WingmanBot
    @app.event("app_mention")
    async def handle_app_mention(event, say):
        """Handle @mentions of the bot."""
        user_id = event["user"]
        text = event["text"]
        thread_ts = event.get("thread_ts") or event["ts"]
        
        # Remove bot mention from text
        text = text.split(">", 1)[-1].strip()
        
        if not text:
            return
        
        session = get_session(user_id)
        
        try:
            response = await session.process_message(text, channel="slack")
            
            # Reply in thread
            await say({
                "text": response,
                "thread_ts": thread_ts,
            })
        
        except Exception as e:
            logger.error(f"Slack mention error: {e}")
            await say({
                "text": f"❌ Error: {e}",
                "thread_ts": thread_ts,
            })
    
    # Direct messages
    @app.event("message")
    async def handle_message(event, say):
        """Handle direct messages to the bot."""
        # Ignore bot messages and threaded replies
        if event.get("bot_id") or event.get("thread_ts"):
            return
        
        # Only handle DMs (channel type is 'im')
        channel_type = event.get("channel_type")
        if channel_type != "im":
            return
        
        user_id = event["user"]
        text = event.get("text", "").strip()
        
        if not text:
            return
        
        session = get_session(user_id)
        
        try:
            response = await session.process_message(text, channel="slack")
            await say(response)
        
        except Exception as e:
            logger.error(f"Slack DM error: {e}")
            await say(f"❌ Error: {e}")
    
    # Interactive components (buttons, etc.)
    @app.action("button_click")
    async def handle_button_click(ack, body, say):
        """Handle button clicks."""
        await ack()
        
        user_id = body["user"]["id"]
        action_value = body["actions"][0]["value"]
        
        session = get_session(user_id)
        
        try:
            response = await session.process_message(
                f"[Button clicked: {action_value}]",
                channel="slack"
            )
            await say(response)
        
        except Exception as e:
            logger.error(f"Slack button error: {e}")
            await say(f"❌ Error: {e}")
    
    # Start Socket Mode handler
    handler = AsyncSocketModeHandler(app, app_token)
    
    logger.info("Slack bot starting...")
    await handler.start_async()
