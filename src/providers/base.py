"""
Abstract base class for LLM providers.

All providers (Gemini, Ollama, OpenRouter) implement this interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator


@dataclass
class Message:
    """A single message in a conversation."""
    role: str  # "system", "user", "assistant", "tool"
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_call_id: str | None = None
    name: str | None = None  # tool name for role="tool"


@dataclass
class ToolCall:
    """A tool/function call from the LLM."""
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ToolDefinition:
    """OpenAI-compatible tool definition for function calling."""
    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema

    def to_gemini_format(self) -> dict[str, Any]:
        """Convert to Google Gemini function declaration format."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }

    def to_openai_format(self) -> dict[str, Any]:
        """Convert to OpenAI tool format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass
class LLMResponse:
    """Response from an LLM provider."""
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: str = "stop"
    usage: dict[str, int] = field(default_factory=dict)

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


class LLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
        stream: bool = False,
    ) -> LLMResponse:
        """
        Send a chat completion request to the LLM.

        Args:
            messages: Conversation history.
            tools: Available tools for function calling.
            temperature: Sampling temperature.
            max_tokens: Max tokens to generate.
            stream: Whether to stream the response.

        Returns:
            LLMResponse with content and/or tool calls.
        """
        ...

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> AsyncIterator[str]:
        """
        Stream a chat completion, yielding text chunks as they arrive.

        Args:
            messages: Conversation history.
            tools: Available tools for function calling.
            temperature: Sampling temperature.
            max_tokens: Max tokens to generate.

        Yields:
            Text chunks as they arrive.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if this provider is available and configured."""
        ...

    @abstractmethod
    def get_model_info(self) -> dict[str, Any]:
        """Return metadata about the current model (name, context_window, etc.)."""
        ...
