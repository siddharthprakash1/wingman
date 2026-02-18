"""
Agent Runtime - The core execution environment for AI agents.

This is the heart of the system, responsible for:
1. Session resolution
2. Context assembly (system prompt composition)
3. LLM invocation with streaming
4. Tool execution with sandboxing
5. State persistence

Separated from the Gateway to allow different deployment models.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Callable

from src.core.session import Session, SessionManager, SessionType
from src.core.protocol import Message, ToolCall, LLMResponse, AgentEvent
from src.config.settings import Settings, get_settings
from src.providers.manager import ProviderManager
from src.tools.registry import ToolRegistry, create_default_registry

logger = logging.getLogger(__name__)


class AgentRuntime:
    """
    The Agent Runtime executes the AI loop.
    
    For each turn:
    1. Resolve session (main/dm/group based on context)
    2. Build system prompt from workspace files + memory
    3. Stream tokens from LLM
    4. Execute tool calls (with sandboxing based on session)
    5. Persist updated state
    """

    def __init__(
        self,
        settings: Settings | None = None,
        workspace_path: Path | None = None,
    ):
        self.settings = settings or get_settings()
        self.workspace = workspace_path or self.settings.workspace_path
        
        # Core components
        self.session_manager = SessionManager(self.workspace / "sessions")
        self.provider_manager = ProviderManager(self.settings)
        self.tool_registry = create_default_registry()
        
        # Event handlers for streaming updates
        self._event_handlers: list[Callable[[AgentEvent], None]] = []
        
        # Processed request IDs for idempotency
        self._processed_requests: set[str] = set()

    def on_event(self, handler: Callable[[AgentEvent], None]) -> None:
        """Register an event handler for agent events."""
        self._event_handlers.append(handler)

    def _emit_event(self, event_type: str, data: dict, session_id: str | None = None) -> None:
        """Emit an event to all registered handlers."""
        event = AgentEvent(
            event_type=event_type,
            data=data,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
        )
        for handler in self._event_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")

    def _build_system_prompt(self, session: Session) -> str:
        """
        Build the system prompt by composing workspace files.
        
        Composition order (following OpenClaw):
        1. AGENTS.md - Core behavioral rules
        2. SOUL.md - Personality/tone
        3. IDENTITY.md - Who the agent is
        4. USER.md - User preferences
        5. TOOLS.md - Tool usage conventions
        6. MEMORY.md - Long-term curated facts
        7. Active skill (if any)
        8. Current context (date, time, platform)
        """
        sections: list[str] = []
        
        # 1. Identity
        identity_path = self.workspace / "IDENTITY.md"
        if identity_path.exists():
            content = identity_path.read_text().strip()
            if content:
                sections.append(f"## Your Identity\n\n{content}")
        
        # 2. Soul/Personality
        soul_path = self.workspace / "SOUL.md"
        if soul_path.exists():
            content = soul_path.read_text().strip()
            if content:
                sections.append(f"## Your Personality\n\n{content}")
        
        # 3. Agent guidelines
        agents_path = self.workspace / "AGENTS.md"
        if agents_path.exists():
            content = agents_path.read_text().strip()
            if content:
                sections.append(f"## Guidelines\n\n{content}")
        
        # 4. User preferences
        user_path = self.workspace / "USER.md"
        if user_path.exists():
            content = user_path.read_text().strip()
            if content:
                sections.append(f"## About the User\n\n{content}")
        
        # 5. Tools description
        tools_path = self.workspace / "TOOLS.md"
        if tools_path.exists():
            content = tools_path.read_text().strip()
            if content:
                sections.append(f"## Your Tools\n\n{content}")
        
        # 6. Long-term memory
        memory_path = self.workspace / "MEMORY.md"
        if memory_path.exists():
            content = memory_path.read_text().strip()
            if content:
                sections.append(f"## Long-Term Memory\n\n{content}")
        
        # 7. Active skill
        if session.active_skill:
            skill_path = self.workspace / "skills" / session.active_skill / "SKILL.md"
            if skill_path.exists():
                content = skill_path.read_text().strip()
                if content:
                    sections.append(f"## Active Skill: {session.active_skill}\n\n{content}")
        
        # 8. Today's conversation log
        today = datetime.now().strftime("%Y-%m-%d")
        log_path = self.workspace / "memory" / f"{today}.md"
        if log_path.exists():
            content = log_path.read_text().strip()
            if content:
                # Only include last 50 lines to avoid bloat
                lines = content.split("\n")[-50:]
                sections.append(f"## Today's Activity Log\n\n" + "\n".join(lines))
        
        # 9. Current context
        now = datetime.now()
        context = (
            f"## Current Context\n\n"
            f"- **Date**: {now.strftime('%A, %B %d, %Y')}\n"
            f"- **Time**: {now.strftime('%I:%M %p')}\n"
            f"- **Session**: {session.session_id}\n"
            f"- **Channel**: {session.channel}\n"
        )
        sections.append(context)
        
        # 10. Tool usage instructions
        tool_instructions = (
            "## Tool Usage\n\n"
            "You have access to tools. Use them when needed to answer questions, "
            "execute tasks, or gather information. Always explain what you're doing "
            "and why before using a tool. After using a tool, interpret the result "
            "for the user.\n\n"
            "Use `memory_append` to save important facts about the user for future sessions."
        )
        sections.append(tool_instructions)
        
        return "\n\n---\n\n".join(sections)

    def _convert_session_messages(self, session: Session) -> list[Message]:
        """Convert session messages to LLM message format."""
        messages = []
        for msg in session.get_recent_messages(limit=50):
            tool_calls = []
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_calls.append(ToolCall(
                        id=tc.get("id", ""),
                        name=tc.get("name", ""),
                        arguments=tc.get("arguments", {}),
                    ))
            
            messages.append(Message(
                role=msg.role,
                content=msg.content,
                tool_calls=tool_calls,
                tool_call_id=msg.tool_call_id,
                name=msg.name,
            ))
        return messages

    async def process_message(
        self,
        user_input: str,
        channel: str = "cli",
        user_id: str | None = None,
        group_id: str | None = None,
        request_id: str | None = None,
    ) -> str:
        """
        Process a user message through the full agent loop.
        
        This is the main entry point for message processing.
        Returns the final text response.
        """
        # Idempotency check
        if request_id and request_id in self._processed_requests:
            logger.warning(f"Duplicate request: {request_id}")
            return "(duplicate request ignored)"
        
        # Resolve session
        is_dm = group_id is None
        session = self.session_manager.resolve_session(
            channel=channel,
            user_id=user_id,
            group_id=group_id,
            is_dm=is_dm,
        )
        
        self._emit_event("agent_start", {"session_id": session.session_id}, session.session_id)
        
        # Add user message to session
        session.add_message(role="user", content=user_input)
        
        # Log to daily log
        self._append_daily_log(f"User ({channel}): {user_input[:200]}")
        
        # Build system prompt
        system_prompt = self._build_system_prompt(session)
        system_msg = Message(role="system", content=system_prompt)
        
        # Get conversation history
        history_messages = self._convert_session_messages(session)
        full_messages = [system_msg] + history_messages
        
        # Get filtered tool definitions based on session permissions
        all_tools = self.tool_registry.get_definitions()
        allowed_tools = [t for t in all_tools if session.is_tool_allowed(t.name)]
        
        # Agent loop
        max_iterations = session.config.max_tool_iterations
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Agent loop iteration {iteration}/{max_iterations}")
            
            try:
                response = await self.provider_manager.chat(
                    messages=full_messages,
                    tools=allowed_tools,
                    temperature=self.settings.agents.defaults.temperature,
                    max_tokens=self.settings.agents.defaults.max_tokens,
                )
            except Exception as e:
                error_msg = f"LLM call failed: {e}"
                logger.error(error_msg)
                return f"❌ {error_msg}"
            
            # Handle tool calls
            if response.has_tool_calls:
                # Add assistant message with tool calls
                assistant_msg = Message(
                    role="assistant",
                    content=response.content,
                    tool_calls=response.tool_calls,
                )
                full_messages.append(assistant_msg)
                session.add_message(
                    role="assistant",
                    content=response.content,
                    tool_calls=[tc.to_dict() for tc in response.tool_calls],
                )
                
                # Execute each tool
                for tool_call in response.tool_calls:
                    self._emit_event(
                        "tool_call",
                        {"name": tool_call.name, "arguments": tool_call.arguments},
                        session.session_id,
                    )
                    
                    # Security check
                    if not session.is_tool_allowed(tool_call.name):
                        result = f"❌ Tool '{tool_call.name}' is not allowed in this session."
                    else:
                        result = await self.tool_registry.execute(tool_call)
                    
                    self._emit_event(
                        "tool_result",
                        {"name": tool_call.name, "result": result[:500]},
                        session.session_id,
                    )
                    
                    # Add tool result
                    tool_msg = Message(
                        role="tool",
                        content=result,
                        tool_call_id=tool_call.id,
                        name=tool_call.name,
                    )
                    full_messages.append(tool_msg)
                    session.add_message(
                        role="tool",
                        content=result,
                        tool_call_id=tool_call.id,
                        name=tool_call.name,
                    )
                
                # Continue loop for LLM to process tool results
                continue
            
            else:
                # No tool calls - final response
                final_response = response.content.strip()
                
                # Add to session
                session.add_message(role="assistant", content=final_response)
                
                # Log
                self._append_daily_log(f"Assistant: {final_response[:200]}")
                
                # Save session
                self.session_manager.save_session(session)
                
                # Mark request as processed
                if request_id:
                    self._processed_requests.add(request_id)
                
                self._emit_event(
                    "agent_complete",
                    {"response": final_response[:500]},
                    session.session_id,
                )
                
                return final_response
        
        # Max iterations reached
        timeout_msg = f"⚠️ Reached maximum tool iterations ({max_iterations})."
        logger.warning(timeout_msg)
        return timeout_msg

    async def process_message_stream(
        self,
        user_input: str,
        channel: str = "cli",
        user_id: str | None = None,
        group_id: str | None = None,
    ) -> AsyncIterator[str]:
        """
        Process a user message with streaming output.
        
        Yields text chunks as they arrive.
        Note: Tool calls interrupt streaming.
        """
        is_dm = group_id is None
        session = self.session_manager.resolve_session(
            channel=channel,
            user_id=user_id,
            group_id=group_id,
            is_dm=is_dm,
        )
        
        session.add_message(role="user", content=user_input)
        
        system_prompt = self._build_system_prompt(session)
        system_msg = Message(role="system", content=system_prompt)
        history_messages = self._convert_session_messages(session)
        full_messages = [system_msg] + history_messages
        
        provider = self.provider_manager.get_provider()
        full_response = ""
        
        try:
            async for chunk in provider.chat_stream(
                messages=full_messages,
                temperature=self.settings.agents.defaults.temperature,
                max_tokens=self.settings.agents.defaults.max_tokens,
            ):
                full_response += chunk
                yield chunk
            
            session.add_message(role="assistant", content=full_response)
            self.session_manager.save_session(session)
            
        except Exception as e:
            error_msg = f"Streaming failed: {e}"
            yield f"\n❌ {error_msg}"

    def _append_daily_log(self, entry: str) -> None:
        """Append an entry to today's log."""
        today = datetime.now().strftime("%Y-%m-%d")
        log_path = self.workspace / "memory" / f"{today}.md"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        with open(log_path, "a") as f:
            f.write(f"\n[{timestamp}] {entry}\n")

    def get_session(self, session_id: str) -> Session | None:
        """Get a session by ID."""
        return self.session_manager.get_session(session_id)

    def list_sessions(self) -> list[str]:
        """List all sessions."""
        return self.session_manager.list_sessions()

    def activate_skill(self, session_id: str, skill_name: str) -> bool:
        """Activate a skill for a session."""
        session = self.get_session(session_id)
        if session is None:
            return False
        
        skill_path = self.workspace / "skills" / skill_name / "SKILL.md"
        if not skill_path.exists():
            return False
        
        session.active_skill = skill_name
        self.session_manager.save_session(session)
        return True

    def deactivate_skill(self, session_id: str) -> bool:
        """Deactivate the current skill for a session."""
        session = self.get_session(session_id)
        if session is None:
            return False
        
        session.active_skill = None
        self.session_manager.save_session(session)
        return True
