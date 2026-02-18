"""
Tests for core components.
"""

import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import json

from src.core.session import Session, SessionType, SessionManager, SessionConfig, SandboxPolicy
from src.core.protocol import Message, ToolCall, ToolDefinition, WebSocketMessage, MessageType


class TestSession:
    """Tests for Session class."""

    def test_create_main_session(self):
        """Test creating a main session."""
        session = Session.create(SessionType.MAIN)
        assert session.session_id == "main"
        assert session.session_type == SessionType.MAIN
        assert session.config.sandbox_policy == SandboxPolicy.NONE

    def test_create_dm_session(self):
        """Test creating a DM session."""
        session = Session.create(
            SessionType.DM,
            channel="telegram",
            user_id="user123",
        )
        assert session.session_id == "dm:telegram:user123"
        assert session.session_type == SessionType.DM
        assert session.channel == "telegram"
        assert session.user_id == "user123"

    def test_create_group_session(self):
        """Test creating a group session."""
        session = Session.create(
            SessionType.GROUP,
            channel="discord",
            group_id="group456",
        )
        assert "group:discord:group456" == session.session_id
        assert session.session_type == SessionType.GROUP

    def test_add_message(self):
        """Test adding messages to a session."""
        session = Session.create(SessionType.MAIN)
        
        msg = session.add_message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert len(session.messages) == 1
        
        session.add_message(role="assistant", content="Hi there!")
        assert len(session.messages) == 2

    def test_tool_access_control(self):
        """Test tool allowlist/denylist."""
        session = Session.create(SessionType.MAIN)
        
        # Main session should allow all tools
        assert session.is_tool_allowed("bash") is True
        assert session.is_tool_allowed("write_file") is True
        
        # Add to denylist
        session.config.tool_denylist = ["bash"]
        assert session.is_tool_allowed("bash") is False
        assert session.is_tool_allowed("write_file") is True
        
        # Test allowlist
        session.config.tool_denylist = []
        session.config.tool_allowlist = ["read_file", "list_dir"]
        assert session.is_tool_allowed("read_file") is True
        assert session.is_tool_allowed("bash") is False

    def test_session_serialization(self):
        """Test session to_dict and from_dict."""
        session = Session.create(SessionType.DM, channel="test", user_id="user1")
        session.add_message(role="user", content="Test message")
        
        data = session.to_dict()
        restored = Session.from_dict(data)
        
        assert restored.session_id == session.session_id
        assert restored.session_type == session.session_type
        assert len(restored.messages) == 1
        assert restored.messages[0].content == "Test message"

    def test_session_persistence(self):
        """Test saving and loading session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "session.json"
            
            session = Session.create(SessionType.MAIN)
            session.add_message(role="user", content="Hello")
            session.save(path)
            
            assert path.exists()
            
            loaded = Session.load(path)
            assert loaded is not None
            assert loaded.session_id == session.session_id
            assert len(loaded.messages) == 1


class TestSessionManager:
    """Tests for SessionManager."""

    def test_resolve_session(self):
        """Test session resolution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(Path(tmpdir))
            
            # CLI should resolve to main
            session = manager.resolve_session(channel="cli")
            assert session.session_id == "main"
            
            # Same call should return same session
            session2 = manager.resolve_session(channel="cli")
            assert session is session2

    def test_dm_session_resolution(self):
        """Test DM session resolution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(Path(tmpdir))
            
            session = manager.resolve_session(
                channel="telegram",
                user_id="user123",
                is_dm=True,
            )
            assert "dm:telegram:user123" == session.session_id

    def test_list_sessions(self):
        """Test listing sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(Path(tmpdir))
            
            manager.resolve_session(channel="cli")
            manager.resolve_session(channel="telegram", user_id="user1", is_dm=True)
            
            manager.save_all()
            
            sessions = manager.list_sessions()
            assert len(sessions) >= 2


class TestProtocol:
    """Tests for protocol classes."""

    def test_message_creation(self):
        """Test Message creation."""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.tool_calls == []

    def test_tool_call(self):
        """Test ToolCall."""
        tc = ToolCall(
            id="call_123",
            name="read_file",
            arguments={"path": "/tmp/test.txt"},
        )
        assert tc.id == "call_123"
        assert tc.name == "read_file"
        assert tc.arguments["path"] == "/tmp/test.txt"

    def test_tool_definition_formats(self):
        """Test tool definition conversion."""
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool",
            parameters={
                "type": "object",
                "properties": {
                    "arg1": {"type": "string"},
                },
                "required": ["arg1"],
            },
        )
        
        openai_format = tool.to_openai_format()
        assert openai_format["type"] == "function"
        assert openai_format["function"]["name"] == "test_tool"
        
        gemini_format = tool.to_gemini_format()
        assert gemini_format["name"] == "test_tool"

    def test_websocket_message(self):
        """Test WebSocket message serialization."""
        msg = WebSocketMessage(
            type=MessageType.MESSAGE,
            payload={"content": "Hello"},
            request_id="req_123",
        )
        
        json_str = msg.to_json()
        parsed = WebSocketMessage.from_json(json_str)
        
        assert parsed.type == MessageType.MESSAGE
        assert parsed.payload["content"] == "Hello"
        assert parsed.request_id == "req_123"


class TestAgents:
    """Tests for agent system."""

    def test_agent_capability_scoring(self):
        """Test agent can_handle scoring."""
        from src.agents.research import ResearchAgent
        from src.agents.coding.engineer import CodingAgent
        
        research = ResearchAgent()
        coder = CodingAgent()
        
        # Research tasks should score higher for ResearchAgent
        research_task = "Research the latest AI news"
        assert research.can_handle(research_task) > coder.can_handle(research_task)
        
        # Coding tasks should score higher for CodingAgent
        coding_task = "Implement a function to sort an array"
        assert coder.can_handle(coding_task) > research.can_handle(coding_task)

    def test_agent_router(self):
        """Test agent routing."""
        from src.agents.router import AgentRouter
        from src.agents.research import ResearchAgent
        from src.agents.coding.engineer import CodingAgent
        
        router = AgentRouter()
        router.register(ResearchAgent())
        router.register(CodingAgent())
        
        # Test routing
        decision = router.route("Research Python best practices")
        assert decision.agent_name == "research"
        
        decision = router.route("Write a Python function")
        assert decision.agent_name == "engineer"


class TestSkills:
    """Tests for skills system."""

    def test_skill_manager(self):
        """Test skill discovery and management."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir) / "skills"
            
            from src.skills.manager import SkillManager
            manager = SkillManager(skills_dir)
            
            # Create a skill
            skill = manager.create_skill(
                name="test-skill",
                description="A test skill",
                instructions="Do test things",
                triggers=["test", "testing"],
            )
            
            assert skill.name == "test-skill"
            assert skill.description == "A test skill"
            
            # List skills
            skills = manager.list_skills()
            assert "test-skill" in skills
            
            # Find by trigger
            found = manager.find_matching_skill("I need to test something")
            assert found is not None
            assert found.name == "test-skill"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
