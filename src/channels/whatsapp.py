"""
WhatsApp Channel — connect the agent to WhatsApp via Twilio.

Supports text messages, media (images, audio, documents), and
interactive message handling through the Twilio WhatsApp API.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.config.settings import Settings

logger = logging.getLogger(__name__)


async def start_whatsapp_bot(settings: "Settings") -> None:
    """
    Start the WhatsApp bot using Twilio API.
    
    Requires:
    - Twilio account SID and auth token
    - WhatsApp sandbox number or approved WhatsApp Business number
    - Webhook endpoint for receiving messages
    
    Configuration:
    - TWILIO_ACCOUNT_SID
    - TWILIO_AUTH_TOKEN  
    - TWILIO_WHATSAPP_NUMBER (e.g., whatsapp:+14155238886)
    """
    try:
        from twilio.rest import Client
        from twilio.twiml.messaging_response import MessagingResponse
    except ImportError:
        logger.error(
            "Twilio SDK not installed. "
            "Install with: pip install twilio"
        )
        return
    
    # Get Twilio credentials from settings
    account_sid = settings.channels.whatsapp.account_sid
    auth_token = settings.channels.whatsapp.auth_token
    whatsapp_number = settings.channels.whatsapp.number
    
    if not all([account_sid, auth_token, whatsapp_number]):
        logger.warning("WhatsApp channel not fully configured")
        return
    
    # Initialize Twilio client
    client = Client(account_sid, auth_token)
    
    from src.agent.loop import AgentSession
    
    # Session management (phone number -> session)
    sessions: dict[str, AgentSession] = {}
    
    async def handle_incoming_message(from_number: str, body: str, media_urls: list[str] | None = None) -> str:
        """
        Handle incoming WhatsApp message.
        
        Args:
            from_number: Sender's WhatsApp number
            body: Message text content
            media_urls: List of media URLs (images, audio, documents)
            
        Returns:
            Response text to send back
        """
        # Get or create session
        if from_number not in sessions:
            sessions[from_number] = AgentSession(
                session_id=f"whatsapp:{from_number}",
                settings=settings,
            )
        
        session = sessions[from_number]
        
        try:
            # Process media if present
            if media_urls:
                media_context = f"\n[User sent {len(media_urls)} media file(s): {', '.join(media_urls)}]"
                body = (body or "") + media_context
            
            response = await session.process_message(body, channel="whatsapp")
            return response
        
        except Exception as e:
            logger.error(f"WhatsApp handler error: {e}")
            return f"❌ Error processing message: {e}"
    
    async def send_message(to_number: str, message: str, media_url: str | None = None) -> None:
        """
        Send WhatsApp message via Twilio.
        
        Args:
            to_number: Recipient's WhatsApp number (with whatsapp: prefix)
            message: Text message to send
            media_url: Optional media URL to attach
        """
        try:
            message_params = {
                "from_": whatsapp_number,
                "to": to_number if to_number.startswith("whatsapp:") else f"whatsapp:{to_number}",
                "body": message,
            }
            
            if media_url:
                message_params["media_url"] = [media_url]
            
            client.messages.create(**message_params)
            logger.info(f"Sent WhatsApp message to {to_number}")
        
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
    
    # Note: WhatsApp integration requires a webhook server
    # The actual webhook server is implemented in src/gateway/server.py
    # This module provides the message handling logic
    
    logger.info("WhatsApp bot initialized (webhook mode)")
    logger.info(f"WhatsApp number: {whatsapp_number}")
    logger.info("Configure webhook URL in Twilio console: https://console.twilio.com")
    
    # Store handlers globally for webhook access
    global _whatsapp_handlers
    _whatsapp_handlers = {
        "handle_message": handle_incoming_message,
        "send_message": send_message,
        "client": client,
        "sessions": sessions,
    }
    
    return _whatsapp_handlers


# Global handlers for webhook access
_whatsapp_handlers: dict = {}


def get_whatsapp_handlers():
    """Get WhatsApp message handlers for webhook integration."""
    return _whatsapp_handlers
