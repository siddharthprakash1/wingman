"""
Ollama LLM provider.

Connects to a local Ollama instance for fully-free, offline inference.
Uses the OpenAI-compatible API at localhost:11434.
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator

import httpx

from src.providers.base import LLMProvider, LLMResponse, Message, ToolCall, ToolDefinition

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """Ollama local model provider via OpenAI-compatible API."""

    def __init__(self, api_base: str = "http://localhost:11434", model: str = "deepseek-r1:14b"):
        self.api_base = api_base.rstrip("/")
        self.model = model
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        """Lazy-init the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.api_base,
                timeout=httpx.Timeout(300.0, connect=10.0),  # Long timeout for local inference
            )
        return self._client

    def _convert_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        """Convert our Message format to Ollama's native /api/chat format.

        Key differences from OpenAI format:
        - tool_calls use {function: {index, name, arguments}} (no 'type' wrapper)
        - tool response messages only need 'role' and 'content'
        """
        result = []
        for msg in messages:
            m: dict[str, Any] = {"role": msg.role, "content": msg.content or ""}

            if msg.role == "assistant" and msg.tool_calls:
                # Ollama native format for tool calls
                m["tool_calls"] = [
                    {
                        "function": {
                            "index": i,
                            "name": tc.name,
                            "arguments": tc.arguments,  # dict, not JSON string
                        },
                    }
                    for i, tc in enumerate(msg.tool_calls)
                ]

            # For tool results, Ollama just needs role=tool + content
            # No tool_call_id or name needed in native format

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
        """Send a chat request to Ollama."""
        client = self._get_client()

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        # Add tools if the model supports function calling
        converted_tools = self._convert_tools(tools) if tools else None
        if converted_tools:
            payload["tools"] = converted_tools

        try:
            response = await client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()

            result = LLMResponse()

            # Parse content
            message_data = data.get("message", {})
            result.content = message_data.get("content", "")

            # Parse tool calls if present
            tool_calls_data = message_data.get("tool_calls", [])
            for i, tc_data in enumerate(tool_calls_data):
                func = tc_data.get("function", {})
                args = func.get("arguments", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {"raw": args}

                result.tool_calls.append(ToolCall(
                    id=f"call_{func.get('name', 'unknown')}_{i}",
                    name=func.get("name", "unknown"),
                    arguments=args,
                ))

            if result.tool_calls:
                result.finish_reason = "tool_calls"

            # Usage info
            result.usage = {
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
                "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
            }

            return result

        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama API HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.ConnectError:
            logger.error(f"Cannot connect to Ollama at {self.api_base}. Is Ollama running?")
            raise
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise

    async def chat_stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> AsyncIterator[str]:
        """Stream a chat completion from Ollama."""
        client = self._get_client()

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            async with client.stream("POST", "/api/chat", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        content = data.get("message", {}).get("content", "")
                        if content:
                            yield content
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            raise

    async def health_check(self) -> bool:
        """Check if Ollama is running and the model is available."""
        try:
            client = self._get_client()
            response = await client.get("/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                # Check if our model is available (partial match okay)
                model_base = self.model.split(":")[0]
                available = any(model_base in m for m in models)
                if not available:
                    logger.warning(
                        f"Ollama is running but model '{self.model}' not found. "
                        f"Available: {models}. Run: ollama pull {self.model}"
                    )
                return True  # Ollama is at least reachable
            return False
        except Exception as e:
            logger.debug(f"Ollama health check failed: {e}")
            return False

    async def list_models(self) -> list[str]:
        """List all available Ollama models."""
        try:
            client = self._get_client()
            response = await client.get("/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [m.get("name", "") for m in data.get("models", [])]
        except Exception:
            pass
        return []

    def get_model_info(self) -> dict[str, Any]:
        """Return Ollama model metadata."""
        return {
            "provider": "ollama",
            "model": self.model,
            "context_window": 32768,  # Depends on model
            "supports_function_calling": True,  # Llama 3.1+, Qwen 2.5+
            "supports_streaming": True,
            "free_tier": True,
            "local": True,
        }

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
