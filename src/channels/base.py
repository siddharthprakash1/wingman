"""
Channel Adapter Base - Common interface for all messaging platforms.

All channel adapters implement this interface to normalize:
1. Authentication
2. Inbound message parsing
3. Access control
4. Outbound message formatting
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Callable


class AccessPolicy(str, Enum):
    """Access control policies for channels."""
    OPEN = "open"           # Accept all messages
    PAIRING = "pairing"     # Require pairing/approval
    ALLOWLIST = "allowlist" # Only from allowlist
    DISABLED = "disabled"   # Reject all


@dataclass
class ChannelConfig:
    """Configuration for a channel adapter."""
    enabled: bool = False
    token: str = ""
    allow_from: list[str] = field(default_factory=list)
    dm_policy: AccessPolicy = AccessPolicy.PAIRING
    group_policy: AccessPolicy = AccessPolicy.ALLOWLIST
    require_mention_in_groups: bool = True
    max_message_length: int = 4096


@dataclass
class InboundMessage:
    """
    Normalized inbound message from any channel.
    
    This is the common format that all adapters produce.
    """
    channel: str                    # telegram, discord, whatsapp, etc.
    message_id: str                 # Platform-specific message ID
    content: str                    # Text content
    
    # Sender info
    user_id: str                    # Platform user ID
    username: str | None = None     # Display name
    
    # Context
    is_dm: bool = True              # True for DMs, False for groups
    group_id: str | None = None     # Group/channel ID if not DM
    group_name: str | None = None   # Group name
    
    # Reply context
    reply_to_message_id: str | None = None
    reply_to_content: str | None = None
    
    # Attachments
    attachments: list[Attachment] = field(default_factory=list)
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    raw_data: dict[str, Any] = field(default_factory=dict)
    
    # Mentions
    mentions_bot: bool = False      # Was the bot @mentioned?


@dataclass
class Attachment:
    """A message attachment (image, file, etc.)."""
    type: str               # image, audio, video, document
    url: str | None = None  # URL to download
    data: bytes | None = None  # Raw data if available
    filename: str | None = None
    mime_type: str | None = None
    size: int = 0


@dataclass
class OutboundMessage:
    """
    Message to send through a channel.
    """
    content: str
    reply_to: str | None = None     # Message ID to reply to
    attachments: list[Attachment] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class ChannelAdapter(ABC):
    """
    Abstract base class for all channel adapters.
    
    Each adapter handles:
    1. Authentication with the platform
    2. Parsing inbound messages
    3. Access control
    4. Formatting and sending outbound messages
    """

    def __init__(self, config: ChannelConfig):
        self.config = config
        self._message_handler: Callable[[InboundMessage], Any] | None = None
        self._running = False

    @property
    @abstractmethod
    def name(self) -> str:
        """Channel name (e.g., 'telegram', 'discord')."""
        ...

    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate with the platform.
        Returns True if successful.
        """
        ...

    @abstractmethod
    async def start(self) -> None:
        """
        Start listening for messages.
        Should run until stop() is called.
        """
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop listening for messages."""
        ...

    @abstractmethod
    async def send_message(
        self,
        target_id: str,
        message: OutboundMessage,
    ) -> bool:
        """
        Send a message to a user or group.
        
        Args:
            target_id: User ID or group ID
            message: The message to send
            
        Returns:
            True if sent successfully
        """
        ...

    @abstractmethod
    async def send_typing_indicator(self, target_id: str) -> None:
        """Send a typing indicator."""
        ...

    def on_message(self, handler: Callable[[InboundMessage], Any]) -> None:
        """Register a message handler."""
        self._message_handler = handler

    async def _handle_message(self, message: InboundMessage) -> None:
        """Internal message handler that applies access control."""
        # Check if enabled
        if not self.config.enabled:
            return
        
        # Apply access control
        if not self._check_access(message):
            return
        
        # Call registered handler
        if self._message_handler:
            await self._message_handler(message)

    def _check_access(self, message: InboundMessage) -> bool:
        """Check if a message passes access control."""
        # Check allowlist
        if self.config.allow_from:
            if message.user_id not in self.config.allow_from:
                if message.username not in self.config.allow_from:
                    return False
        
        # Check policy
        if message.is_dm:
            policy = self.config.dm_policy
        else:
            policy = self.config.group_policy
            # Check mention requirement for groups
            if self.config.require_mention_in_groups and not message.mentions_bot:
                return False
        
        if policy == AccessPolicy.DISABLED:
            return False
        
        if policy == AccessPolicy.ALLOWLIST:
            if not self.config.allow_from:
                return False
            if message.user_id not in self.config.allow_from:
                if message.username not in self.config.allow_from:
                    return False
        
        return True

    def format_response(self, text: str) -> str:
        """
        Format a response for this channel.
        Override to handle platform-specific markdown.
        """
        return text

    def chunk_message(self, text: str) -> list[str]:
        """
        Split a message into chunks that fit platform limits.
        """
        max_len = self.config.max_message_length
        if len(text) <= max_len:
            return [text]
        
        chunks = []
        current = ""
        
        for line in text.split("\n"):
            if len(current) + len(line) + 1 > max_len:
                if current:
                    chunks.append(current)
                current = line
            else:
                current = f"{current}\n{line}" if current else line
        
        if current:
            chunks.append(current)
        
        return chunks


class CLIAdapter(ChannelAdapter):
    """
    CLI adapter for local terminal interaction.
    This is the 'main' session channel.
    """

    def __init__(self, config: ChannelConfig | None = None):
        super().__init__(config or ChannelConfig(enabled=True))
        self._input_queue: list[str] = []

    @property
    def name(self) -> str:
        return "cli"

    async def authenticate(self) -> bool:
        return True  # CLI is always authenticated

    async def start(self) -> None:
        self._running = True
        # CLI doesn't have a listener loop - messages come via process_input

    async def stop(self) -> None:
        self._running = False

    async def send_message(self, target_id: str, message: OutboundMessage) -> bool:
        print(message.content)
        return True

    async def send_typing_indicator(self, target_id: str) -> None:
        pass  # No typing indicator for CLI

    async def process_input(self, text: str, user_id: str = "local") -> None:
        """Process input from CLI."""
        message = InboundMessage(
            channel="cli",
            message_id=f"cli_{datetime.now().timestamp()}",
            content=text,
            user_id=user_id,
            is_dm=True,
        )
        await self._handle_message(message)
