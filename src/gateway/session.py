"""
Session Manager — manage agent sessions with isolation.

Each session has its own message history and can be
persisted/restored. Sessions are identified by unique IDs.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from src.agent.loop import AgentSession
from src.config.settings import get_settings

logger = logging.getLogger(__name__)

# Session timeout in seconds (1 hour)
SESSION_TIMEOUT = 3600
MAX_SESSIONS = 100


class SessionManager:
    """Manages multiple agent sessions with isolation."""

    def __init__(self):
        self._sessions: dict[str, AgentSession] = {}
        self._session_last_used: dict[str, float] = {}

    def get_or_create(self, session_id: str | None = None) -> AgentSession:
        """Get an existing session or create a new one."""
        # Clean up expired sessions first
        self._cleanup_expired_sessions()
        
        if session_id and session_id in self._sessions:
            self._session_last_used[session_id] = time.time()
            return self._sessions[session_id]

        # Check max sessions limit
        if len(self._sessions) >= MAX_SESSIONS:
            # Remove oldest session
            oldest_id = min(self._session_last_used, key=self._session_last_used.get)
            self.remove(oldest_id)
            logger.warning(f"Max sessions reached, removed oldest: {oldest_id}")

        session = AgentSession(session_id=session_id)
        self._sessions[session.session_id] = session
        self._session_last_used[session.session_id] = time.time()
        logger.info(f"Created session: {session.session_id}")
        return session
    
    def _cleanup_expired_sessions(self) -> None:
        """Remove sessions that have been inactive for too long."""
        now = time.time()
        expired = [
            sid for sid, last_used in self._session_last_used.items()
            if now - last_used > SESSION_TIMEOUT
        ]
        for sid in expired:
            self.remove(sid)
            logger.info(f"Cleaned up expired session: {sid}")

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
        self._session_last_used.pop(session_id, None)
        if session:
            session.save_session()
            logger.info(f"Removed session: {session_id}")
