"""
Protocol Definitions - Typed message formats for the Gateway.

All WebSocket messages are validated against these schemas.
This ensures type safety and enables robust error handling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import json
import uuid


class MessageType(str, Enum):
    """WebSocket message types."""
    # Client → Gateway
    INIT = "init"
    MESSAGE = "message"
    PING = "ping"
    
    # Gateway → Client
    SESSION = "session"
    RESPONSE = "response"
    THINKING = "thinking"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    ERROR = "error"
    PONG = "pong"
    
    # Agent events
    AGENT_START = "agent_start"
    AGENT_TOKEN = "agent_token"
    AGENT_COMPLETE = "agent_complete"
    
    # Project management
    PROJECT_CREATE = "project_create"
    PROJECT_UPDATE = "project_update"
    PROJECT_LIST = "project_list"
    PROJECT_LOAD = "project_load"
    PROJECT_DELETE = "project_delete"
    PROJECT_NEXT = "project_next"
    
    # Skill events
    SKILL_ACTIVATE = "skill_activate"
    SKILL_DEACTIVATE = "skill_deactivate"
    
    # Canvas/A2UI
    CANVAS_UPDATE = "canvas_update"
    CANVAS_ACTION = "canvas_action"


@dataclass
class Message:
    """A single message in a conversation."""
    role: str  # "system", "user", "assistant", "tool"
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_call_id: str | None = None
    name: str | None = None  # tool name for role="tool"

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "tool_calls": [tc.to_dict() for tc in self.tool_calls] if self.tool_calls else [],
            "tool_call_id": self.tool_call_id,
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Message:
        tool_calls = [ToolCall.from_dict(tc) for tc in data.get("tool_calls", [])]
        return cls(
            role=data["role"],
            content=data.get("content", ""),
            tool_calls=tool_calls,
            tool_call_id=data.get("tool_call_id"),
            name=data.get("name"),
        )


@dataclass
class ToolCall:
    """A tool/function call from the LLM."""
    id: str
    name: str
    arguments: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "arguments": self.arguments,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ToolCall:
        return cls(
            id=data.get("id", f"call_{uuid.uuid4().hex[:8]}"),
            name=data["name"],
            arguments=data.get("arguments", {}),
        )


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


@dataclass
class WebSocketMessage:
    """
    A typed WebSocket message with idempotency support.
    
    All messages include:
    - type: The message type
    - payload: The message data
    - request_id: Optional idempotency key for side-effecting operations
    """
    type: MessageType
    payload: dict[str, Any] = field(default_factory=dict)
    request_id: str | None = None

    def to_json(self) -> str:
        return json.dumps({
            "type": self.type.value,
            "request_id": self.request_id,
            **self.payload,
        })

    @classmethod
    def from_json(cls, data: str | dict) -> WebSocketMessage:
        if isinstance(data, str):
            data = json.loads(data)
        
        msg_type = MessageType(data.get("type", "message"))
        request_id = data.get("request_id")
        
        # Extract payload (everything except type and request_id)
        payload = {k: v for k, v in data.items() if k not in ("type", "request_id")}
        
        return cls(type=msg_type, payload=payload, request_id=request_id)


# Event types for the agent runtime
@dataclass
class AgentEvent:
    """Events emitted during agent execution."""
    event_type: str
    data: dict[str, Any] = field(default_factory=dict)
    session_id: str | None = None
    timestamp: str | None = None


# Convenience functions for creating common messages
def create_response_message(content: str, session_id: str) -> WebSocketMessage:
    return WebSocketMessage(
        type=MessageType.RESPONSE,
        payload={"content": content, "session_id": session_id},
    )


def create_error_message(error: str, details: dict | None = None) -> WebSocketMessage:
    payload = {"content": error}
    if details:
        payload["details"] = details
    return WebSocketMessage(type=MessageType.ERROR, payload=payload)


def create_thinking_message(status: bool) -> WebSocketMessage:
    return WebSocketMessage(
        type=MessageType.THINKING,
        payload={"status": status},
    )


def create_tool_call_message(tool_name: str, arguments: dict, call_id: str) -> WebSocketMessage:
    return WebSocketMessage(
        type=MessageType.TOOL_CALL,
        payload={
            "name": tool_name,
            "arguments": arguments,
            "call_id": call_id,
        },
    )


def create_tool_result_message(tool_name: str, result: str, call_id: str) -> WebSocketMessage:
    return WebSocketMessage(
        type=MessageType.TOOL_RESULT,
        payload={
            "name": tool_name,
            "result": result,
            "call_id": call_id,
        },
    )
