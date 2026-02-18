"""
OpenAI LLM provider.

Connects to OpenAI API.
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator

import httpx

from src.providers.base import LLMProvider, LLMResponse, Message, ToolCall, ToolDefinition

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI provider."""

    def __init__(self, api_key: str, api_base: str = "https://api.openai.com/v1", model: str = "gpt-4o"):
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.model = model
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        """Lazy-init the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.api_base,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(120.0, connect=10.0),
            )
        return self._client

    def _convert_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        """Convert to OpenAI format."""
        result = []
        for msg in messages:
            # OpenAI requires content to be string or null, not missing
            content = msg.content if msg.content is not None else ""
            
            # For assistant messages with tool_calls, content can be null
            if msg.role == "assistant" and msg.tool_calls:
                content = msg.content  # Can be None for tool-calling assistants
            
            m: dict[str, Any] = {"role": msg.role, "content": content}
            
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
            if msg.tool_call_id:
                m["tool_call_id"] = msg.tool_call_id
            if msg.name:
                m["name"] = msg.name
            result.append(m)
        return result

    def _convert_tools(self, tools: list[ToolDefinition]) -> list[dict[str, Any]] | None:
        """Convert tool definitions to OpenAI format."""
        if not tools:
            return None
        return [tool.to_openai_format() for tool in tools]

    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
        stream: bool = False,
    ) -> LLMResponse:
        """Send a chat request to OpenAI."""
        client = self._get_client()

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        converted_tools = self._convert_tools(tools) if tools else None
        if converted_tools:
            payload["tools"] = converted_tools

        try:
            response = await client.post("/chat/completions", json=payload)
            if response.status_code != 200:
                error_body = response.text
                logger.error(f"OpenAI API error response: {error_body}")
            response.raise_for_status()
            data = response.json()

            result = LLMResponse()

            choices = data.get("choices", [])
            if choices:
                choice = choices[0]
                message_data = choice.get("message", {})
                result.content = message_data.get("content", "") or ""
                result.finish_reason = choice.get("finish_reason", "stop")

                # Parse tool calls
                for i, tc_data in enumerate(message_data.get("tool_calls", [])):
                    func = tc_data.get("function", {})
                    args_str = func.get("arguments", "{}")
                    try:
                        args = json.loads(args_str) if isinstance(args_str, str) else args_str
                    except json.JSONDecodeError:
                        args = {"raw": args_str}

                    result.tool_calls.append(ToolCall(
                        id=tc_data.get("id", f"call_{i}"),
                        name=func.get("name", "unknown"),
                        arguments=args,
                    ))

            # Usage
            usage = data.get("usage", {})
            result.usage = {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            }

            return result

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    async def chat_stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> AsyncIterator[str]:
        """Stream a chat completion from OpenAI."""
        client = self._get_client()

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        try:
            async with client.stream("POST", "/chat/completions", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:]  # Strip "data: "
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        choices = data.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise

    async def health_check(self) -> bool:
        """Check if OpenAI is configured."""
        if not self.api_key:
            return False
        try:
            client = self._get_client()
            # OpenAI doesn't have a simple /models endpoint that is as lightweight and unauthenticated-friendly (if checking generic reachability)
            # but with a key, /models is good.
            response = await client.get("/models")
            return response.status_code == 200
        except Exception:
            return False

    def get_model_info(self) -> dict[str, Any]:
        """Return OpenAI model metadata."""
        return {
            "provider": "openai",
            "model": self.model,
            "context_window": 128000,  # Varies by model, assuming 4o/turbo
            "supports_function_calling": True,
            "supports_streaming": True,
            "free_tier": False,
        }

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
