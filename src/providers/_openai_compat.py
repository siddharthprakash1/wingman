"""
OpenAI-compatible provider base class.

Any provider speaking the OpenAI `/chat/completions` protocol (OpenAI, Groq,
OpenRouter, Kimi, Ollama, together.ai, etc.) can subclass this and only
override `base_url`, `default_model`, and any auth-header quirks.

Subclasses typically set these at construction time:
    - self.api_base      (e.g. "https://api.groq.com/openai/v1")
    - self.api_key
    - self.model
    - self._provider_name (for logging)

And optionally override:
    - `_auth_headers()`   if the provider uses non-standard auth
    - `_extra_body()`     to add provider-specific request fields
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator

from src.providers._http import get_shared_client
from src.providers.base import LLMProvider, LLMResponse, Message, ToolCall, ToolDefinition

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(LLMProvider):
    """Base class for any provider using the OpenAI chat-completions protocol."""

    _provider_name: str = "openai-compatible"
    _context_window: int = 128_000

    def __init__(self, api_key: str, api_base: str, model: str):
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.model = model

    # ------------------------------------------------------------------ #
    # Hooks for subclasses                                                #
    # ------------------------------------------------------------------ #

    def _auth_headers(self) -> dict[str, str]:
        """Default: Bearer auth. Override for providers with weird auth."""
        h: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def _extra_body(self) -> dict[str, Any]:
        """Optional extra JSON fields added to every request."""
        return {}

    # ------------------------------------------------------------------ #
    # Message / tool conversion                                           #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _convert_messages(messages: list[Message]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for msg in messages:
            content = msg.content if msg.content is not None else ""
            if msg.role == "assistant" and msg.tool_calls:
                content = msg.content  # may be None for tool-calling assistants

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

    @staticmethod
    def _convert_tools(tools: list[ToolDefinition] | None) -> list[dict[str, Any]] | None:
        if not tools:
            return None
        return [tool.to_openai_format() for tool in tools]

    # ------------------------------------------------------------------ #
    # Core chat / stream                                                  #
    # ------------------------------------------------------------------ #

    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
        stream: bool = False,
    ) -> LLMResponse:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
            **self._extra_body(),
        }
        converted_tools = self._convert_tools(tools)
        if converted_tools:
            payload["tools"] = converted_tools

        client = get_shared_client()
        url = f"{self.api_base}/chat/completions"

        try:
            response = await client.post(url, json=payload, headers=self._auth_headers())
            if response.status_code != 200:
                logger.error(
                    "%s API error %d: %s",
                    self._provider_name,
                    response.status_code,
                    response.text[:500],
                )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.error("%s API error: %s", self._provider_name, e)
            raise

        result = LLMResponse()
        choices = data.get("choices", [])
        if choices:
            choice = choices[0]
            message_data = choice.get("message", {})
            result.content = message_data.get("content", "") or ""
            result.finish_reason = choice.get("finish_reason", "stop")
            for i, tc_data in enumerate(message_data.get("tool_calls", []) or []):
                func = tc_data.get("function", {})
                args_str = func.get("arguments", "{}")
                try:
                    args = json.loads(args_str) if isinstance(args_str, str) else args_str
                except json.JSONDecodeError:
                    args = {"raw": args_str}
                result.tool_calls.append(
                    ToolCall(
                        id=tc_data.get("id", f"call_{i}"),
                        name=func.get("name", "unknown"),
                        arguments=args,
                    )
                )

        usage = data.get("usage", {}) or {}
        result.usage = {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }
        return result

    async def chat_stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> AsyncIterator[str]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            **self._extra_body(),
        }
        converted_tools = self._convert_tools(tools)
        if converted_tools:
            payload["tools"] = converted_tools

        client = get_shared_client()
        url = f"{self.api_base}/chat/completions"

        try:
            async with client.stream(
                "POST", url, json=payload, headers=self._auth_headers()
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:]
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
            logger.error("%s streaming error: %s", self._provider_name, e)
            raise

    # ------------------------------------------------------------------ #
    # Health + info                                                       #
    # ------------------------------------------------------------------ #

    async def health_check(self) -> bool:
        if not self.api_key:
            return False
        try:
            client = get_shared_client()
            resp = await client.get(
                f"{self.api_base}/models", headers=self._auth_headers()
            )
            return resp.status_code == 200
        except Exception:
            return False

    def get_model_info(self) -> dict[str, Any]:
        return {
            "provider": self._provider_name,
            "model": self.model,
            "context_window": self._context_window,
            "supports_function_calling": True,
            "supports_streaming": True,
            "free_tier": False,
        }
