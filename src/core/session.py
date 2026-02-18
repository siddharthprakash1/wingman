"""
Session Management - OpenClaw-style session isolation and security boundaries.

Sessions are the fundamental security boundary in the system:
- `main` - Direct CLI/local access, full host permissions
- `dm:<channel>:<id>` - Direct message sessions, isolated per user
- `group:<channel>:<id>` - Group chat sessions, isolated per group

Each session type can have different:
- Tool allowlists
- Sandboxing policies (Docker isolation)
- Memory access permissions
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SessionType(str, Enum):
    """Session types with different security profiles."""
    MAIN = "main"           # Local/CLI - full access
    DM = "dm"               # Direct messages - isolated
    GROUP = "group"         # Group chats - isolated, mention-required
    PROJECT = "project"     # Project-specific sessions
    AGENT = "agent"         # Agent-to-agent sessions


class SandboxPolicy(str, Enum):
    """Sandboxing policies for tool execution."""
    NONE = "none"           # No sandboxing (main session)
    DOCKER = "docker"       # Docker container isolation
    RESTRICTED = "restricted"  # Limited tool access only


@dataclass
class SessionConfig:
    """Configuration for a session type."""
    sandbox_policy: SandboxPolicy = SandboxPolicy.NONE
    tool_allowlist: list[str] = field(default_factory=list)  # Empty = all allowed
    tool_denylist: list[str] = field(default_factory=list)
    max_tool_iterations: int = 25
    require_approval: bool = False  # Require user approval for dangerous ops


# Default configurations per session type
DEFAULT_SESSION_CONFIGS: dict[SessionType, SessionConfig] = {
    SessionType.MAIN: SessionConfig(
        sandbox_policy=SandboxPolicy.NONE,
        tool_allowlist=[],  # All tools allowed
        max_tool_iterations=50,
    ),
    SessionType.DM: SessionConfig(
        sandbox_policy=SandboxPolicy.RESTRICTED,
        tool_denylist=["bash"],  # No shell by default in DMs
        max_tool_iterations=25,
    ),
    SessionType.GROUP: SessionConfig(
        sandbox_policy=SandboxPolicy.RESTRICTED,
        tool_denylist=["bash", "write_file"],
        max_tool_iterations=15,
        require_approval=True,
    ),
    SessionType.PROJECT: SessionConfig(
        sandbox_policy=SandboxPolicy.DOCKER,
        tool_allowlist=[],  # All tools, but in Docker
        max_tool_iterations=100,
    ),
    SessionType.AGENT: SessionConfig(
        sandbox_policy=SandboxPolicy.NONE,
        tool_allowlist=[],
        max_tool_iterations=50,
    ),
}


@dataclass
class SessionMessage:
    """A message in a session."""
    role: str  # user, assistant, tool, system
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    tool_calls: list[dict] = field(default_factory=list)
    tool_call_id: str | None = None
    name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "tool_calls": self.tool_calls,
            "tool_call_id": self.tool_call_id,
            "name": self.name,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionMessage:
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            tool_calls=data.get("tool_calls", []),
            tool_call_id=data.get("tool_call_id"),
            name=data.get("name"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Session:
    """
    A conversation session with security boundaries.
    
    Each session maintains:
    - Unique identifier based on type and context
    - Message history
    - Tool execution permissions
    - Sandboxing configuration
    """
    session_id: str
    session_type: SessionType
    channel: str = "cli"
    user_id: str | None = None
    group_id: str | None = None
    
    messages: list[SessionMessage] = field(default_factory=list)
    config: SessionConfig = field(default_factory=SessionConfig)
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Session-specific context
    context: dict[str, Any] = field(default_factory=dict)
    active_skill: str | None = None
    
    @classmethod
    def create(
        cls,
        session_type: SessionType,
        channel: str = "cli",
        user_id: str | None = None,
        group_id: str | None = None,
    ) -> Session:
        """Create a new session with appropriate ID format."""
        if session_type == SessionType.MAIN:
            session_id = "main"
        elif session_type == SessionType.DM:
            session_id = f"dm:{channel}:{user_id or uuid.uuid4().hex[:8]}"
        elif session_type == SessionType.GROUP:
            session_id = f"group:{channel}:{group_id or uuid.uuid4().hex[:8]}"
        elif session_type == SessionType.PROJECT:
            session_id = f"project:{uuid.uuid4().hex[:8]}"
        elif session_type == SessionType.AGENT:
            session_id = f"agent:{uuid.uuid4().hex[:8]}"
        else:
            session_id = f"session:{uuid.uuid4().hex[:8]}"
        
        config = DEFAULT_SESSION_CONFIGS.get(session_type, SessionConfig())
        
        return cls(
            session_id=session_id,
            session_type=session_type,
            channel=channel,
            user_id=user_id,
            group_id=group_id,
            config=config,
        )

    def add_message(
        self,
        role: str,
        content: str,
        tool_calls: list[dict] | None = None,
        tool_call_id: str | None = None,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SessionMessage:
        """Add a message to the session."""
        msg = SessionMessage(
            role=role,
            content=content,
            tool_calls=tool_calls or [],
            tool_call_id=tool_call_id,
            name=name,
            metadata=metadata or {},
        )
        self.messages.append(msg)
        self.updated_at = datetime.now()
        return msg

    def get_recent_messages(self, limit: int = 50) -> list[SessionMessage]:
        """Get the most recent messages."""
        return self.messages[-limit:]

    def is_tool_allowed(self, tool_name: str) -> bool:
        """Check if a tool is allowed in this session."""
        # Check denylist first
        if tool_name in self.config.tool_denylist:
            return False
        # If allowlist is set, tool must be in it
        if self.config.tool_allowlist:
            return tool_name in self.config.tool_allowlist
        return True

    def to_dict(self) -> dict[str, Any]:
        """Serialize session to dictionary."""
        return {
            "session_id": self.session_id,
            "session_type": self.session_type.value,
            "channel": self.channel,
            "user_id": self.user_id,
            "group_id": self.group_id,
            "messages": [m.to_dict() for m in self.messages],
            "config": {
                "sandbox_policy": self.config.sandbox_policy.value,
                "tool_allowlist": self.config.tool_allowlist,
                "tool_denylist": self.config.tool_denylist,
                "max_tool_iterations": self.config.max_tool_iterations,
                "require_approval": self.config.require_approval,
            },
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "context": self.context,
            "active_skill": self.active_skill,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Session:
        """Deserialize session from dictionary."""
        config_data = data.get("config", {})
        config = SessionConfig(
            sandbox_policy=SandboxPolicy(config_data.get("sandbox_policy", "none")),
            tool_allowlist=config_data.get("tool_allowlist", []),
            tool_denylist=config_data.get("tool_denylist", []),
            max_tool_iterations=config_data.get("max_tool_iterations", 25),
            require_approval=config_data.get("require_approval", False),
        )
        
        return cls(
            session_id=data["session_id"],
            session_type=SessionType(data["session_type"]),
            channel=data.get("channel", "cli"),
            user_id=data.get("user_id"),
            group_id=data.get("group_id"),
            messages=[SessionMessage.from_dict(m) for m in data.get("messages", [])],
            config=config,
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat())),
            context=data.get("context", {}),
            active_skill=data.get("active_skill"),
        )

    def save(self, path: Path) -> None:
        """Save session to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.debug(f"Saved session {self.session_id} to {path}")

    @classmethod
    def load(cls, path: Path) -> Session | None:
        """Load session from file."""
        if not path.exists():
            return None
        try:
            with open(path, "r") as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load session from {path}: {e}")
            return None


class SessionManager:
    """
    Manages all active sessions.
    
    Handles:
    - Session creation and resolution
    - Persistence to disk
    - Session lookup by various identifiers
    """

    def __init__(self, sessions_dir: Path):
        self.sessions_dir = sessions_dir
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self._active_sessions: dict[str, Session] = {}

    def resolve_session(
        self,
        channel: str,
        user_id: str | None = None,
        group_id: str | None = None,
        is_dm: bool = True,
    ) -> Session:
        """
        Resolve or create the appropriate session for a message.
        
        This is the main entry point for session resolution:
        - CLI messages → main session
        - DMs → dm:<channel>:<user_id>
        - Groups → group:<channel>:<group_id>
        """
        if channel == "cli":
            session_id = "main"
            session_type = SessionType.MAIN
        elif is_dm and user_id:
            session_id = f"dm:{channel}:{user_id}"
            session_type = SessionType.DM
        elif group_id:
            session_id = f"group:{channel}:{group_id}"
            session_type = SessionType.GROUP
        else:
            session_id = f"dm:{channel}:{user_id or 'unknown'}"
            session_type = SessionType.DM

        # Check active sessions first
        if session_id in self._active_sessions:
            return self._active_sessions[session_id]

        # Try to load from disk
        session_path = self.sessions_dir / f"{session_id.replace(':', '_')}.json"
        session = Session.load(session_path)
        
        if session is None:
            # Create new session
            session = Session.create(
                session_type=session_type,
                channel=channel,
                user_id=user_id,
                group_id=group_id,
            )
            # Override session_id to match our resolution
            session.session_id = session_id
            logger.info(f"Created new session: {session_id}")
        else:
            logger.info(f"Loaded existing session: {session_id}")

        self._active_sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Session | None:
        """Get a session by ID."""
        if session_id in self._active_sessions:
            return self._active_sessions[session_id]
        
        session_path = self.sessions_dir / f"{session_id.replace(':', '_')}.json"
        session = Session.load(session_path)
        if session:
            self._active_sessions[session_id] = session
        return session

    def save_session(self, session: Session) -> None:
        """Save a session to disk."""
        session_path = self.sessions_dir / f"{session.session_id.replace(':', '_')}.json"
        session.save(session_path)

    def save_all(self) -> None:
        """Save all active sessions."""
        for session in self._active_sessions.values():
            self.save_session(session)

    def list_sessions(self) -> list[str]:
        """List all session IDs."""
        sessions = set(self._active_sessions.keys())
        for path in self.sessions_dir.glob("*.json"):
            session_id = path.stem.replace("_", ":")
            sessions.add(session_id)
        return sorted(sessions)

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]
        
        session_path = self.sessions_dir / f"{session_id.replace(':', '_')}.json"
        if session_path.exists():
            session_path.unlink()
            return True
        return False
