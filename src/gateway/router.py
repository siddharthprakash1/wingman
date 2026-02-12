"""
Message Router — normalize and route messages from different channels.

Converts channel-specific message formats into the internal Message format
and routes them to the appropriate agent session.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from src.gateway.session import SessionManager

logger = logging.getLogger(__name__)


@dataclass
class InboundMessage:
    """A normalized inbound message from any channel."""
    channel: str          # "telegram", "discord", "webchat", "cli"
    user_id: str          # Channel-specific user identifier
    content: str          # The message text
    session_key: str = "" # Key for session routing (default: channel:user_id)
    metadata: dict = None

    def __post_init__(self):
        if not self.session_key:
            self.session_key = f"{self.channel}:{self.user_id}"
        if self.metadata is None:
            self.metadata = {}


class MessageRouter:
    """
    Routes inbound messages to agent sessions.

    Each unique (channel, user_id) pair gets its own session.
    """

    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager

    async def route(self, msg: InboundMessage) -> str:
        """
        Route a message to the appropriate agent session
        and return the response.

        Args:
            msg: The normalized inbound message.

        Returns:
            The agent's response text.
        """
        # Get or create session for this user
        session = self.session_manager.get_or_create(session_id=msg.session_key)

        # Process through agent
        response = await session.process_message(
            user_input=msg.content,
            channel=msg.channel,
        )

        return response
