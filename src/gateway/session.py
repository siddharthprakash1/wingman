"""
Session Manager — manage agent sessions with isolation.

Each session has its own message history and can be
persisted/restored. Sessions are identified by unique IDs.
"""

from __future__ import annotations

import logging
from typing import Any

from src.agent.loop import AgentSession
from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages multiple agent sessions with isolation."""

    def __init__(self):
        self._sessions: dict[str, AgentSession] = {}

    def get_or_create(self, session_id: str | None = None) -> AgentSession:
        """Get an existing session or create a new one."""
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]

        session = AgentSession(session_id=session_id)
        self._sessions[session.session_id] = session
        logger.info(f"Created session: {session.session_id}")
        return session

    def get(self, session_id: str) -> AgentSession | None:
        """Get an existing session by ID."""
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[dict[str, Any]]:
        """List all active sessions with metadata."""
        return [
            {
                "session_id": sid,
                "message_count": len(session.messages),
                "model": session.settings.agents.defaults.model,
            }
            for sid, session in self._sessions.items()
        ]

    def remove(self, session_id: str) -> None:
        """Remove and save a session."""
        session = self._sessions.pop(session_id, None)
        if session:
            session.save_session()
            logger.info(f"Removed session: {session_id}")
