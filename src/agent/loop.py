"""
Agent Loop — the core brain of the assistant.

Implements the agentic loop:
  1. Receive message → 2. Build prompt → 3. Call LLM →
  4. Execute tools (if any) → 5. Loop → 6. Return response
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator

from src.config.settings import Settings, get_settings
from src.memory.manager import MemoryManager
from src.memory.transcript import TranscriptLogger
from src.providers.base import LLMResponse, Message, ToolCall
from src.providers.manager import ProviderManager
from src.tools.registry import ToolRegistry, create_default_registry
from src.agent.prompt import PromptBuilder

logger = logging.getLogger(__name__)


class AgentSession:
    """
    A single agent conversation session.

    Each session maintains its own message history and can be
    persisted/restored from disk.
    """

    def __init__(
        self,
        session_id: str | None = None,
        settings: Settings | None = None,
    ):
        self.settings = settings or get_settings()
        self.session_id = session_id or str(uuid.uuid4())[:8]

        # Core components
        self.memory = MemoryManager()
        self.provider_manager = ProviderManager(self.settings)
        self.tool_registry = create_default_registry()
        self.prompt_builder = PromptBuilder(self.memory)
        self.transcript = TranscriptLogger(
            session_dir=self.memory.sessions_dir,
            session_id=self.session_id,
        )

        # Register memory tools
        self._register_memory_tools()

        # Message history for this session
        self.messages: list[Message] = []
        self._system_prompt_built = False

    def _register_memory_tools(self) -> None:
        """Register memory management tools."""
        self.tool_registry.register(
            name="memory_read",
            description="Read a specific memory file (agents, soul, identity, user, memory, tools).",
            parameters={
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Memory file key: agents, soul, identity, user, memory, or tools",
                    },
                },
                "required": ["key"],
            },
            func=self.memory.memory_read_tool,
        )

        self.tool_registry.register(
            name="memory_update",
            description="Update a memory file with new content. Use to save important information about the user.",
            parameters={
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Memory file key: agents, soul, identity, user, memory, or tools",
                    },
                    "content": {
                        "type": "string",
                        "description": "The new content for the memory file (replaces existing)",
                    },
                },
                "required": ["key", "content"],
            },
            func=self.memory.memory_update_tool,
        )

        self.tool_registry.register(
            name="memory_append",
            description="Append information to a memory file. Good for adding new facts to MEMORY.md.",
            parameters={
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Memory file key: agents, soul, identity, user, memory, or tools",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to append to the memory file",
                    },
                },
                "required": ["key", "content"],
            },
            func=self.memory.memory_append_tool,
        )

    def _build_system_message(self) -> Message:
        """Build the system prompt message."""
        system_prompt = self.prompt_builder.build_system_prompt()
        tool_prompt = self.prompt_builder.build_tool_prompt()
        return Message(
            role="system",
            content=f"{system_prompt}\n\n---\n\n{tool_prompt}",
        )

    async def process_message(self, user_input: str, channel: str = "cli") -> str:
        """
        Process a user message through the full agent loop.

        This is the main entry point for sending a message to the agent.

        Args:
            user_input: The user's message.
            channel: The channel this message came from.

        Returns:
            The agent's text response.
        """
        # Log user message (with context detection)
        if "[Context:" in user_input:
            logger.info(f"Received message with knowledge base context: {user_input[:300]}...")
        self.transcript.log_user_message(user_input, channel)
        self.memory.append_daily_log(f"User ({channel}): {user_input[:200]}")

        # Build system prompt (first message or refresh)
        system_msg = self._build_system_message()

        # Add user message to history
        self.messages.append(Message(role="user", content=user_input))

        # Prepare full message array: system + history
        full_messages = [system_msg] + self.messages

        # Get tool definitions
        tool_defs = self.tool_registry.get_definitions()

        # Agent loop: call LLM → execute tools → repeat
        max_iterations = self.settings.agents.defaults.max_tool_iterations
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Agent loop iteration {iteration}/{max_iterations}")

            try:
                response = await self.provider_manager.chat(
                    messages=full_messages,
                    tools=tool_defs,
                    temperature=self.settings.agents.defaults.temperature,
                    max_tokens=self.settings.agents.defaults.max_tokens,
                )
            except Exception as e:
                error_msg = f"LLM call failed: {e}"
                logger.error(error_msg)
                self.transcript.log_error(error_msg)
                return f"❌ {error_msg}"

            # Check for tool calls
            if response.has_tool_calls:
                # Execute each tool call
                assistant_msg = Message(
                    role="assistant",
                    content=response.content,
                    tool_calls=response.tool_calls,
                )
                self.messages.append(assistant_msg)
                full_messages.append(assistant_msg)

                for tool_call in response.tool_calls:
                    self.transcript.log_tool_call(tool_call.name, tool_call.arguments)
                    logger.info(f"Tool call: {tool_call.name}({tool_call.arguments})")

                    # Execute the tool
                    result = await self.tool_registry.execute(tool_call)
                    self.transcript.log_tool_result(tool_call.name, result[:500])

                    # Add tool result to messages
                    tool_msg = Message(
                        role="tool",
                        content=result,
                        tool_call_id=tool_call.id,
                        name=tool_call.name,
                    )
                    self.messages.append(tool_msg)
                    full_messages.append(tool_msg)

                # Continue the loop for the LLM to process tool results
                continue

            else:
                # No tool calls — we have a final text response
                final_response = response.content.strip()

                # Add assistant message to history
                self.messages.append(Message(role="assistant", content=final_response))

                # Log the response
                self.transcript.log_assistant_message(
                    final_response[:500],
                    model=self.settings.agents.defaults.model,
                )
                self.memory.append_daily_log(f"Assistant: {final_response[:200]}")

                # Log token usage
                if response.usage:
                    logger.info(f"Token usage: {response.usage}")

                return final_response

        # Max iterations reached
        timeout_msg = (
            f"⚠️ Reached maximum tool iterations ({max_iterations}). "
            "The task may be incomplete."
        )
        logger.warning(timeout_msg)
        return timeout_msg

    async def process_message_stream(
        self, user_input: str, channel: str = "cli"
    ) -> AsyncIterator[str]:
        """
        Process a user message with streaming output.

        Yields text chunks as they arrive from the LLM.
        Note: Streaming doesn't support tool calling — it returns
        the first text response only.
        """
        self.transcript.log_user_message(user_input, channel)
        self.messages.append(Message(role="user", content=user_input))

        system_msg = self._build_system_message()
        full_messages = [system_msg] + self.messages

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

            # Save the complete response
            self.messages.append(Message(role="assistant", content=full_response))
            self.transcript.log_assistant_message(
                full_response[:500],
                model=self.settings.agents.defaults.model,
            )
        except Exception as e:
            error_msg = f"Streaming failed: {e}"
            yield f"\n❌ {error_msg}"
            self.transcript.log_error(error_msg)

    def save_session(self) -> None:
        """Persist the current session to disk."""
        session_data = {
            "session_id": self.session_id,
            "created_at": datetime.now().isoformat(),
            "message_count": len(self.messages),
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content[:1000],  # Truncate for storage
                    "has_tool_calls": bool(msg.tool_calls),
                }
                for msg in self.messages
            ],
        }
        session_path = self.memory.get_session_path(self.session_id)
        session_path.parent.mkdir(parents=True, exist_ok=True)
        session_path.write_text(json.dumps(session_data, indent=2))

    def clear_history(self) -> None:
        """Clear the conversation history (start fresh)."""
        self.messages.clear()
