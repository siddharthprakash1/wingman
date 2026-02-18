"""
Channel Adapters - Messaging platform integrations.

Each adapter normalizes platform-specific APIs into a common interface.
"""

from src.channels.base import (
    ChannelAdapter,
    ChannelConfig,
    InboundMessage,
    OutboundMessage,
    Attachment,
    AccessPolicy,
    CLIAdapter,
)

__all__ = [
    "ChannelAdapter",
    "ChannelConfig", 
    "InboundMessage",
    "OutboundMessage",
    "Attachment",
    "AccessPolicy",
    "CLIAdapter",
]
