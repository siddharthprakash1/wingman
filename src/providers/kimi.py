"""
Kimi K2.5 Provider — Moonshot AI's flagship model.

Uses OpenAI-compatible API at https://api.moonshot.ai/v1.
Model: kimi-k2.5 — 256K context, function calling, streaming.
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator

import httpx

from src.providers.base import (
    LLMProvider,
    LLMResponse,
    Message,
    ToolCall,
    ToolDefinition,
)

logger = logging.getLogger(__name__)


class KimiProvider(LLMProvider):
    """
    Kimi K2.5 provider via Moonshot AI's OpenAI-compatible API.

    API docs: https://platform.moonshot.cn/docs
    Base URL: https://api.moonshot.ai/v1
    Model: kimi-k2.5 (256K context, function calling, streaming)
    """

    def __init__(self, api_key: str, api_base: str = "https://api.moonshot.ai/v1", model: str = "kimi-k2.5"):
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.client = httpx.AsyncClient(
            base_url=self.api_base,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(120.0, connect=10.0),
        )

    def _convert_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        """Convert internal Message format to OpenAI chat format."""
        result = []
        for msg in messages:
            m: dict[str, Any] = {"role": msg.role, "content": msg.content or ""}

            if msg.role == "tool":
                m["tool_call_id"] = msg.tool_call_id or ""
                m["name"] = msg.name or ""

            if msg.tool_calls:
                m["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments),
                        },
                    }
                    for tc in msg.tool_calls
                ]

            result.append(m)
        return result

    def _convert_tools(self, tools: list[ToolDefinition]) -> list[dict[str, Any]]:
        """Convert tool definitions to OpenAI function format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in tools
        ]

    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
        stream: bool = False,
    ) -> LLMResponse:
        """Send a chat completion request to Kimi K2.5."""
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        if tools:
            payload["tools"] = self._convert_tools(tools)
            payload["tool_choice"] = "auto"

        try:
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            error_body = e.response.text
            raise RuntimeError(f"Kimi API error {e.response.status_code}: {error_body}") from e
        except Exception as e:
            raise RuntimeError(f"Kimi API request failed: {e}") from e

        choice = data["choices"][0]
        message = choice["message"]

        # Parse tool calls
        tool_calls = []
        if message.get("tool_calls"):
            for tc in message["tool_calls"]:
                func = tc.get("function", {})
                args = func.get("arguments", "{}")
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {"raw": args}

                tool_calls.append(ToolCall(
                    id=tc.get("id", ""),
                    name=func.get("name", ""),
                    arguments=args,
                ))

        # Parse usage
        usage = {}
        if data.get("usage"):
            usage = {
                "prompt_tokens": data["usage"].get("prompt_tokens", 0),
                "completion_tokens": data["usage"].get("completion_tokens", 0),
                "total_tokens": data["usage"].get("total_tokens", 0),
            }

        return LLMResponse(
            content=message.get("content", "") or "",
            tool_calls=tool_calls,
            usage=usage,
            model=data.get("model", self.model),
            finish_reason=choice.get("finish_reason", ""),
        )

    async def chat_stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> AsyncIterator[str]:
        """Stream chat completions from Kimi K2.5."""
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        if tools:
            payload["tools"] = self._convert_tools(tools)
            payload["tool_choice"] = "auto"

        async with self.client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:].strip()
                if data_str == "[DONE]":
                    break

                try:
                    data = json.loads(data_str)
                    delta = data["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue

    async def health_check(self) -> bool:
        """Check if the Kimi API is reachable."""
        if not self.api_key:
            logger.warning("Kimi API key not configured")
            return False

        try:
            response = await self.client.get("/models")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Kimi health check failed: {e}")
            return False

    def get_model_info(self) -> dict[str, Any]:
        """Get model info."""
        return {
            "provider": "kimi",
            "model": self.model,
            "context_window": 262144,  # 256K
            "api_base": self.api_base,
            "supports_tools": True,
            "supports_streaming": True,
        }
