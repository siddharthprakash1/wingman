"""
Multi-Agent Session Tools - Enable agent-to-agent communication.

Allows agents to spawn child sessions, delegate tasks, and coordinate
work across multiple specialized agents (OpenClaw pattern).
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from src.core.session import SessionManager
from src.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


# Global session manager for inter-agent communication
_global_session_manager: SessionManager | None = None


def _get_session_manager() -> SessionManager:
    """Get or create the global session manager."""
    global _global_session_manager
    if _global_session_manager is None:
        _global_session_manager = SessionManager()
    return _global_session_manager


async def sessions_create(
    purpose: str,
    agent_type: str = "general",
    parent_session_id: str | None = None,
) -> str:
    """
    Create a new agent session for delegated work.

    Args:
        purpose: Description of what this session should accomplish.
        agent_type: Type of agent to use (research, coding, writer, etc.).
        parent_session_id: Optional parent session ID for tracking hierarchy.

    Returns:
        JSON with session_id and status.
    """
    try:
        import json
        
        manager = _get_session_manager()
        
        # Generate session ID
        session_id = f"sub_{uuid.uuid4().hex[:8]}"
        
        # Create session
        session = manager.get_or_create(session_id)
        
        # Store metadata about this being a child session
        session.metadata = {
            "purpose": purpose,
            "agent_type": agent_type,
            "parent_session_id": parent_session_id,
            "is_child_session": True,
        }
        
        logger.info(f"Created child session {session_id} for {agent_type} agent: {purpose}")
        
        return json.dumps({
            "success": True,
            "session_id": session_id,
            "purpose": purpose,
            "agent_type": agent_type,
        }, indent=2)
    
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
        })


async def sessions_message(
    session_id: str,
    message: str,
    wait_for_response: bool = True,
    timeout: int = 60,
) -> str:
    """
    Send a message to another agent session and optionally wait for response.

    Args:
        session_id: The target session ID.
        message: The message to send.
        wait_for_response: Whether to wait for agent response (default: True).
        timeout: Maximum time to wait for response in seconds (default: 60).

    Returns:
        JSON with the agent's response or status.
    """
    try:
        import json
        
        manager = _get_session_manager()
        session = manager.get_session(session_id)
        
        if not session:
            return json.dumps({
                "success": False,
                "error": f"Session {session_id} not found",
            })
        
        if wait_for_response:
            # Process message and get response
            try:
                response = await asyncio.wait_for(
                    session.process_message(message, channel="inter_agent"),
                    timeout=timeout
                )
                
                return json.dumps({
                    "success": True,
                    "session_id": session_id,
                    "response": response,
                }, indent=2)
            
            except asyncio.TimeoutError:
                return json.dumps({
                    "success": False,
                    "error": f"Response timeout after {timeout}s",
                })
        else:
            # Fire and forget
            asyncio.create_task(session.process_message(message, channel="inter_agent"))
            
            return json.dumps({
                "success": True,
                "session_id": session_id,
                "message": "Message sent (async, no response awaited)",
            })
    
    except Exception as e:
        logger.error(f"Failed to send message to session {session_id}: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
        })


async def sessions_list(parent_session_id: str | None = None) -> str:
    """
    List all active sessions, optionally filtered by parent.

    Args:
        parent_session_id: Optional parent session ID to filter by.

    Returns:
        JSON array of session information.
    """
    try:
        import json
        
        manager = _get_session_manager()
        all_sessions = manager.list_sessions()
        
        sessions_info = []
        for sid in all_sessions:
            session = manager.get_session(sid)
            if not session:
                continue
            
            metadata = getattr(session, 'metadata', {})
            
            # Filter by parent if specified
            if parent_session_id and metadata.get('parent_session_id') != parent_session_id:
                continue
            
            sessions_info.append({
                "session_id": sid,
                "purpose": metadata.get("purpose", ""),
                "agent_type": metadata.get("agent_type", "general"),
                "is_child": metadata.get("is_child_session", False),
                "parent_session_id": metadata.get("parent_session_id"),
            })
        
        return json.dumps({
            "success": True,
            "sessions": sessions_info,
            "count": len(sessions_info),
        }, indent=2)
    
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
        })


async def sessions_close(session_id: str) -> str:
    """
    Close a session and clean up resources.

    Args:
        session_id: The session ID to close.

    Returns:
        JSON with status.
    """
    try:
        import json
        
        manager = _get_session_manager()
        session = manager.get_session(session_id)
        
        if not session:
            return json.dumps({
                "success": False,
                "error": f"Session {session_id} not found",
            })
        
        # Save session state before closing
        manager.save_session(session_id)
        
        # Remove from active sessions
        manager._sessions.pop(session_id, None)
        
        logger.info(f"Closed session {session_id}")
        
        return json.dumps({
            "success": True,
            "session_id": session_id,
            "message": "Session closed and saved",
        })
    
    except Exception as e:
        logger.error(f"Failed to close session {session_id}: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
        })


def register_session_tools(registry: ToolRegistry) -> None:
    """Register multi-agent session tools."""
    
    registry.register(
        name="sessions_create",
        description="Create a new agent session to delegate work to a specialized agent",
        parameters={
            "type": "object",
            "properties": {
                "purpose": {
                    "type": "string",
                    "description": "What this agent session should accomplish",
                },
                "agent_type": {
                    "type": "string",
                    "description": "Type of agent (research, coding, writer, data, browser, etc.)",
                    "enum": ["general", "research", "coding", "writer", "data", "browser", "system"],
                    "default": "general",
                },
                "parent_session_id": {
                    "type": "string",
                    "description": "Optional parent session ID for tracking",
                },
            },
            "required": ["purpose"],
        },
        func=sessions_create,
    )
    
    registry.register(
        name="sessions_message",
        description="Send a message to another agent session and get its response",
        parameters={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Target session ID",
                },
                "message": {
                    "type": "string",
                    "description": "Message to send to the agent",
                },
                "wait_for_response": {
                    "type": "boolean",
                    "description": "Wait for agent response (default: true)",
                    "default": True,
                },
                "timeout": {
                    "type": "integer",
                    "description": "Max wait time in seconds (default: 60)",
                    "default": 60,
                },
            },
            "required": ["session_id", "message"],
        },
        func=sessions_message,
    )
    
    registry.register(
        name="sessions_list",
        description="List all active agent sessions, optionally filtered by parent",
        parameters={
            "type": "object",
            "properties": {
                "parent_session_id": {
                    "type": "string",
                    "description": "Optional parent session ID to filter by",
                },
            },
        },
        func=sessions_list,
    )
    
    registry.register(
        name="sessions_close",
        description="Close an agent session and clean up resources",
        parameters={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session ID to close",
                },
            },
            "required": ["session_id"],
        },
        func=sessions_close,
    )
